"""
Beat Detector - Audio beat and tempo detection using librosa.
"""
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


@dataclass
class BeatDetectionSettings:
    """Settings for beat detection."""
    # Onset detection threshold (0.0 - 1.0, higher = less sensitive, only strong beats)
    onset_threshold: float = 0.1
    # Minimum time between beats in seconds
    min_beat_interval: float = 0.2
    # Use only strong beats (filter out weak ones)
    strong_beats_only: bool = False
    # Minimum onset strength percentile (0-100, e.g., 50 = only top 50% strongest)
    strength_percentile: int = 0


@dataclass
class BeatInfo:
    """Beat detection results."""
    filepath: str
    tempo: float  # BPM
    beat_times: List[float]  # Beat positions in seconds
    beat_strengths: List[float]  # Strength of each beat (0.0 - 1.0)
    duration: float  # Total duration in seconds
    
    @property
    def beat_count(self) -> int:
        """Get number of beats."""
        return len(self.beat_times)
    
    @property
    def avg_beat_interval(self) -> float:
        """Get average interval between beats in seconds."""
        if len(self.beat_times) < 2:
            return 0.0
        intervals = np.diff(self.beat_times)
        return float(np.mean(intervals))
    
    def get_beats_in_range(self, start: float, end: float) -> List[float]:
        """Get beats within a time range."""
        return [t for t in self.beat_times if start <= t <= end]


class BeatDetector:
    """Detects beats and tempo in audio files."""
    
    def __init__(self):
        """Initialize beat detector."""
        if not LIBROSA_AVAILABLE:
            raise ImportError(
                "librosa is required for beat detection. "
                "Install with: pip install librosa numpy"
            )
    
    @staticmethod
    def is_available() -> bool:
        """Check if librosa is available."""
        return LIBROSA_AVAILABLE
    
    def analyze(
        self, 
        filepath: str, 
        sr: int = 22050,
        settings: Optional[BeatDetectionSettings] = None
    ) -> Optional[BeatInfo]:
        """
        Analyze audio file for beats and tempo.
        
        Args:
            filepath: Path to audio file.
            sr: Sample rate for analysis (default 22050).
            settings: Beat detection settings.
            
        Returns:
            BeatInfo object or None if analysis fails.
        """
        if not os.path.isfile(filepath):
            return None
        
        if settings is None:
            settings = BeatDetectionSettings()
        
        try:
            # Load audio file
            y, sr = librosa.load(filepath, sr=sr, mono=True)
            
            # Get duration
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Compute onset envelope for strength measurement
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Detect tempo and beats
            tempo, beat_frames = librosa.beat.beat_track(
                y=y, 
                sr=sr,
                onset_envelope=onset_env
            )
            
            # Convert tempo to float (might be ndarray in newer versions)
            if hasattr(tempo, '__iter__'):
                tempo = float(tempo[0]) if len(tempo) > 0 else 0.0
            else:
                tempo = float(tempo)
            
            # Convert beat frames to times
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # Get beat strengths from onset envelope
            beat_strengths = []
            for frame in beat_frames:
                if frame < len(onset_env):
                    strength = float(onset_env[frame])
                else:
                    strength = 0.0
                beat_strengths.append(strength)
            
            # Normalize strengths to 0-1
            if beat_strengths:
                max_strength = max(beat_strengths) if max(beat_strengths) > 0 else 1.0
                beat_strengths = [s / max_strength for s in beat_strengths]
            
            # Apply filtering based on settings
            filtered_times = []
            filtered_strengths = []
            
            # Calculate threshold from percentile
            if settings.strength_percentile > 0 and beat_strengths:
                threshold = np.percentile(beat_strengths, settings.strength_percentile)
            else:
                threshold = settings.onset_threshold
            
            last_beat_time = -settings.min_beat_interval
            
            for i, (t, s) in enumerate(zip(beat_times, beat_strengths)):
                # Check minimum interval
                if t - last_beat_time < settings.min_beat_interval:
                    continue
                
                # Check strength threshold
                if s < threshold:
                    continue
                
                filtered_times.append(float(t))
                filtered_strengths.append(float(s))
                last_beat_time = t
            
            return BeatInfo(
                filepath=filepath,
                tempo=round(tempo, 1),
                beat_times=filtered_times,
                beat_strengths=filtered_strengths,
                duration=duration
            )
        
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            return None
    
    def analyze_multiple(
        self, 
        filepaths: List[str],
        settings: Optional[BeatDetectionSettings] = None
    ) -> List[BeatInfo]:
        """
        Analyze multiple audio files.
        
        Args:
            filepaths: List of audio file paths.
            settings: Beat detection settings.
            
        Returns:
            List of BeatInfo objects.
        """
        results = []
        for filepath in filepaths:
            info = self.analyze(filepath, settings=settings)
            if info:
                results.append(info)
        return results
    
    def get_combined_beats(
        self, 
        beat_infos: List[BeatInfo],
        offsets: Optional[List[float]] = None
    ) -> Tuple[List[float], float]:
        """
        Combine beats from multiple audio files with time offsets.
        
        Args:
            beat_infos: List of BeatInfo objects.
            offsets: Optional list of time offsets for each file.
                     If None, files are assumed to be sequential.
        
        Returns:
            Tuple of (combined beat times, total duration).
        """
        if not beat_infos:
            return [], 0.0
        
        # Calculate offsets if not provided
        if offsets is None:
            offsets = []
            current_offset = 0.0
            for info in beat_infos:
                offsets.append(current_offset)
                current_offset += info.duration
        
        # Combine beats with offsets
        combined_beats = []
        for info, offset in zip(beat_infos, offsets):
            for beat_time in info.beat_times:
                combined_beats.append(beat_time + offset)
        
        # Sort beats
        combined_beats.sort()
        
        # Calculate total duration
        total_duration = sum(info.duration for info in beat_infos)
        
        return combined_beats, total_duration
    
    @staticmethod
    def format_tempo(tempo: float) -> str:
        """Format tempo as string."""
        return f"{tempo:.1f} BPM"
    
    @staticmethod
    def get_tempo_category(tempo: float) -> str:
        """Get tempo category description."""
        if tempo < 60:
            return "Very Slow (Largo)"
        elif tempo < 80:
            return "Slow (Adagio)"
        elif tempo < 100:
            return "Moderate (Andante)"
        elif tempo < 120:
            return "Medium (Moderato)"
        elif tempo < 140:
            return "Fast (Allegro)"
        elif tempo < 180:
            return "Very Fast (Vivace)"
        else:
            return "Extremely Fast (Presto)"
