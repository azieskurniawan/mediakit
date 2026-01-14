"""
Audio Utilities - Handles audio file analysis using FFprobe.
"""
import subprocess
import json
import os
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class AudioInfo:
    """Audio file information."""
    filepath: str
    duration: float  # Duration in seconds
    codec: str
    sample_rate: int
    channels: int
    bitrate: Optional[int] = None
    
    @property
    def duration_formatted(self) -> str:
        """Get duration as HH:MM:SS format."""
        return AudioUtils.format_duration(self.duration)


class AudioUtils:
    """Utility class for audio file operations using FFprobe."""
    
    SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma'}
    
    def __init__(self, ffprobe_path: str = "ffprobe"):
        """
        Initialize AudioUtils.
        
        Args:
            ffprobe_path: Path to ffprobe executable.
        """
        self._ffprobe_path = ffprobe_path
    
    @property
    def ffprobe_path(self) -> str:
        """Get FFprobe path."""
        return self._ffprobe_path
    
    @ffprobe_path.setter
    def ffprobe_path(self, path: str) -> None:
        """Set FFprobe path."""
        self._ffprobe_path = path
    
    def _is_ffprobe_available(self) -> bool:
        """Check if ffprobe is accessible."""
        try:
            result = subprocess.run(
                [self._ffprobe_path, '-version'],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
    
    def get_duration(self, filepath: str) -> Optional[float]:
        """
        Get duration of audio/video file in seconds.
        
        Args:
            filepath: Path to media file.
            
        Returns:
            Duration in seconds or None if failed.
        """
        if not os.path.isfile(filepath):
            return None
        
        # Check if ffprobe is accessible
        if not self._is_ffprobe_available():
            print(f"Warning: ffprobe not found at '{self._ffprobe_path}'. Cannot get duration.")
            return None
        
        cmd = [
            self._ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            filepath
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration = float(data.get('format', {}).get('duration', 0))
                return duration
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error getting duration for {filepath}: {e}")
        
        return None
    
    def get_audio_info(self, filepath: str) -> Optional[AudioInfo]:
        """
        Get detailed audio file information.
        
        Args:
            filepath: Path to audio file.
            
        Returns:
            AudioInfo object or None if failed.
        """
        if not os.path.isfile(filepath):
            return None
        
        cmd = [
            self._ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            filepath
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                format_info = data.get('format', {})
                
                # Find audio stream
                audio_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    return AudioInfo(
                        filepath=filepath,
                        duration=float(format_info.get('duration', 0)),
                        codec=audio_stream.get('codec_name', 'unknown'),
                        sample_rate=int(audio_stream.get('sample_rate', 0)),
                        channels=int(audio_stream.get('channels', 0)),
                        bitrate=int(format_info.get('bit_rate', 0)) if format_info.get('bit_rate') else None
                    )
        except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error getting audio info for {filepath}: {e}")
        
        return None
    
    def get_directory_audio_files(self, directory: str) -> List[str]:
        """
        Get all audio files in a directory.
        
        Args:
            directory: Path to directory.
            
        Returns:
            List of audio file paths.
        """
        audio_files = []
        dir_path = Path(directory)
        
        if dir_path.is_dir():
            for file in dir_path.iterdir():
                if file.is_file() and file.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    audio_files.append(str(file))
        
        return sorted(audio_files)
    
    def calculate_total_duration(self, directory: str) -> Tuple[float, str]:
        """
        Calculate total duration of all audio files in directory.
        
        Args:
            directory: Path to directory containing audio files.
            
        Returns:
            Tuple of (total seconds, formatted string HH:MM:SS).
        """
        audio_files = self.get_directory_audio_files(directory)
        total_seconds = 0.0
        
        for filepath in audio_files:
            duration = self.get_duration(filepath)
            if duration:
                total_seconds += duration
        
        return total_seconds, self.format_duration(total_seconds)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in seconds to HH:MM:SS.
        
        Args:
            seconds: Duration in seconds.
            
        Returns:
            Formatted string HH:MM:SS.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def parse_duration(duration_str: str) -> float:
        """
        Parse HH:MM:SS string to seconds.
        
        Args:
            duration_str: Duration string in HH:MM:SS format.
            
        Returns:
            Duration in seconds.
        """
        parts = duration_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        else:
            return float(parts[0])
