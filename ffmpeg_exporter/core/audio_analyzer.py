"""
Audio Analyzer - FFT-based audio analysis for visualizers.
Inspired by Astrofox's audio processing.
"""
import numpy as np
from scipy import signal
from scipy.fft import rfft
from typing import Tuple, Optional
import subprocess
import json
import tempfile
import os


class AudioAnalyzer:
    """Analyze audio files using FFT for visualization."""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize audio analyzer.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable.
            ffprobe_path: Path to ffprobe executable.
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.sample_rate = 44100  # Default sample rate
        self.fft_size = 2048  # FFT window size
    
    def extract_audio_samples(
        self,
        audio_file: str,
        start_time: float = 0.0,
        duration: Optional[float] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Extract raw audio samples from audio file using FFmpeg.
        
        Args:
            audio_file: Path to audio file.
            start_time: Start time in seconds.
            duration: Duration in seconds (None = entire file).
            
        Returns:
            Tuple of (audio_samples, sample_rate).
            audio_samples is mono float32 array normalized to [-1, 1].
        """
        cmd = [
            self.ffmpeg_path,
            '-v', 'error',
            '-ss', str(start_time)
        ]
        
        if duration is not None:
            cmd.extend(['-t', str(duration)])
        
        cmd.extend([
            '-i', audio_file,
            '-f', 's16le',  # 16-bit PCM
            '-acodec', 'pcm_s16le',
            '-ar', str(self.sample_rate),  # Resample to target rate
            '-ac', '1',  # Mono
            'pipe:1'
        ])
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            audio_data, stderr = process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {stderr.decode()}")
            
            # Convert bytes to numpy array
            audio_samples = np.frombuffer(audio_data, dtype=np.int16)
            
            # Normalize to [-1, 1]
            audio_samples = audio_samples.astype(np.float32) / 32768.0
            
            return audio_samples, self.sample_rate
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio samples: {e}")
    
    def compute_fft_spectrum(
        self,
        audio_samples: np.ndarray,
        fft_size: Optional[int] = None,
        window: str = 'blackman',
        min_db: float = -100,
        max_db: float = -30
    ) -> np.ndarray:
        """
        Compute FFT spectrum from audio samples.
        Returns byte values (0-255) like Web Audio API AnalyserNode.
        
        Args:
            audio_samples: Audio samples array.
            fft_size: FFT window size (default: self.fft_size).
            window: Window function ('blackman', 'hann', 'hamming', etc.).
            min_db: Minimum dB for byte mapping (Astrofox default: -100).
            max_db: Maximum dB for byte mapping (Astrofox default: -30).
            
        Returns:
            FFT byte spectrum (0-255 values, like Web Audio API).
            
        Note:
            In Web Audio API, AnalyserNode uses minDecibels and maxDecibels
            to map dB values to 0-255 byte range. We replicate this behavior.
        """
        if fft_size is None:
            fft_size = self.fft_size
        
        # Apply window function (like Astrofox)
        if window == 'blackman':
            window_func = signal.windows.blackman(fft_size)
        elif window == 'hann':
            window_func = signal.windows.hann(fft_size)
        elif window == 'hamming':
            window_func = signal.windows.hamming(fft_size)
        else:
            window_func = np.ones(fft_size)
        
        # Pad or trim to fft_size
        if len(audio_samples) < fft_size:
            padded = np.zeros(fft_size, dtype=np.float32)
            padded[:len(audio_samples)] = audio_samples
            audio_samples = padded
        else:
            audio_samples = audio_samples[:fft_size]
        
        # Apply window
        windowed = audio_samples * window_func
        
        # Compute FFT
        spectrum = np.abs(rfft(windowed))
        
        # Convert to dB
        spectrum_db = 20 * np.log10(spectrum + 1e-10)
        
        # Map dB range to 0-255 bytes (like Web Audio API)
        # This uses the SAME min_db and max_db that will be used in parse_fft_spectrum
        spectrum_byte = np.clip(
            255 * (spectrum_db - min_db) / (max_db - min_db),
            0,
            255
        )
        
        return spectrum_byte.astype(np.uint8)
    
    def parse_fft_spectrum(
        self,
        spectrum_byte: np.ndarray,
        min_db: float = -100,
        max_db: float = 0,
        min_freq: int = 0,
        max_freq: int = 6000,
        num_bins: Optional[int] = None,
        smoothing: float = 0.0,
        smoothing_buffer: Optional[np.ndarray] = None,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Parse FFT spectrum to visualizer bins (EXACT Astrofox FFTParser algorithm).
        
        This is a Python port of Astrofox's FFTParser.parseFFT() method.
        
        Args:
            spectrum_byte: FFT byte spectrum (0-255 values from compute_fft_spectrum).
            min_db: Minimum dB level (Astrofox default: -100).
            max_db: Maximum dB level (Astrofox default: 0 or -12 for BarSpectrum).
            min_freq: Minimum frequency (Hz).
            max_freq: Maximum frequency (Hz).
            num_bins: Number of output bins (None = based on frequency range).
            smoothing: Smoothing time constant (0.0 - 0.99, Astrofox default: 0.5).
            smoothing_buffer: Buffer for exponential smoothing.
            normalize: If True, normalize using Astrofox's method (CLAMP 0-1).
            
        Returns:
            Spectrum values (0-1) for visualization.
        """
        # Calculate frequency bins (like Astrofox FFTParser.init)
        freq_range = self.sample_rate / self.fft_size
        start_bin = int(min_freq / freq_range)
        end_bin = int(max_freq / freq_range)
        total_bins = end_bin - start_bin
        
        # Clamp bins
        start_bin = max(0, start_bin)
        end_bin = min(len(spectrum_byte), end_bin)
        total_bins = max(1, end_bin - start_bin)
        
        # Determine output size
        size = num_bins if num_bins is not None else total_bins
        
        # Initialize output array
        output = np.zeros(size, dtype=np.float32)
        
        # Astrofox getValue function (line 42-47 in FFTParser.js)
        def get_value(fft_byte):
            """Convert byte FFT value to normalized magnitude (Astrofox algorithm)."""
            # Convert byte (0-255) back to dB
            db = min_db * (1.0 - fft_byte / 256.0)
            
            # Convert dB to magnitude: db2mag(db) = Math.exp(0.1151292546497023 * db)
            mag = np.exp(0.1151292546497023 * db)
            min_mag = np.exp(0.1151292546497023 * min_db)
            max_mag = np.exp(0.1151292546497023 * max_db)
            
            # Normalize: (val - min) / (max - min), clamped to [0, 1]
            normalized = (mag - min_mag) / (max_mag - min_mag)
            return np.clip(normalized, 0.0, 1.0)
        
        # Astrofox parseFFT logic (line 49-115 in FFTParser.js)
        
        # Case 1: Straight conversion (size == total_bins)
        if size == total_bins:
            for i in range(start_bin, end_bin):
                k = i - start_bin
                output[k] = get_value(spectrum_byte[i])
        
        # Case 2: Compress data (size < total_bins)
        elif size < total_bins:
            step = total_bins / size
            
            for k in range(size):
                i = int(k * step)
                start = int(i * step)
                end_range = int(start + step)
                max_val = 0
                
                # Find max value within range (line 78-87)
                n_step = max(1, int(step / 10))
                for j in range(start, end_range, n_step):
                    if j < len(spectrum_byte):
                        val = spectrum_byte[j]
                        if val > max_val:
                            max_val = val
                
                output[k] = get_value(max_val)
        
        # Case 3: Expand data (size > total_bins)
        else:  # size > total_bins
            step = size / total_bins
            
            for j in range(total_bins):
                i = start_bin + j
                if i < len(spectrum_byte):
                    val = get_value(spectrum_byte[i])
                    start_k = int(j * step)
                    end_k = int(start_k + step)
                    
                    for k in range(start_k, min(end_k, size)):
                        output[k] = val
        
        # Apply smoothing (line 107-113 in FFTParser.js)
        if smoothing > 0 and smoothing_buffer is not None:
            if len(smoothing_buffer) != size:
                smoothing_buffer.resize(size, refcheck=False)
                smoothing_buffer.fill(0)
            
            # Exponential moving average (EXACT Astrofox formula)
            for i in range(size):
                output[i] = smoothing_buffer[i] * smoothing + output[i] * (1.0 - smoothing)
                smoothing_buffer[i] = output[i]
        
        return output
    
    def parse_waveform(
        self,
        audio_samples: np.ndarray,
        num_points: int,
        smoothing: float = 0.0,
        smoothing_buffer: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Parse audio waveform for visualization (like Astrofox WaveParser).
        
        Args:
            audio_samples: Raw audio samples.
            num_points: Number of output points.
            smoothing: Smoothing constant (0.0 - 0.99).
            smoothing_buffer: Buffer for exponential smoothing.
            
        Returns:
            Normalized waveform values (0-1) for visualization.
        """
        # Resample to target point count
        if len(audio_samples) != num_points:
            x_old = np.linspace(0, 1, len(audio_samples))
            x_new = np.linspace(0, 1, num_points)
            waveform = np.interp(x_new, x_old, audio_samples)
        else:
            waveform = audio_samples.copy()
        
        # Normalize to 0-1 (assuming input is -1 to 1)
        normalized = (waveform + 1.0) / 2.0
        
        # Apply exponential smoothing
        if smoothing > 0 and smoothing_buffer is not None:
            if len(smoothing_buffer) != num_points:
                smoothing_buffer.resize(num_points, refcheck=False)
                smoothing_buffer.fill(0.5)  # Middle value
            
            normalized = smoothing_buffer * smoothing + normalized * (1.0 - smoothing)
            smoothing_buffer[:] = normalized
        
        return normalized
    
    def analyze_audio_for_frame(
        self,
        audio_file: str,
        frame_time: float,
        fft_size: int = 2048,
        sample_window: float = 0.05,  # 50ms window
        min_db: float = -100,
        max_db: float = -30
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Analyze audio at a specific time for a single frame.
        
        Args:
            audio_file: Path to audio file.
            frame_time: Time in seconds for this frame.
            fft_size: FFT window size.
            sample_window: Time window for sampling (seconds).
            min_db: Minimum dB for FFT byte mapping (must match parse call).
            max_db: Maximum dB for FFT byte mapping (must match parse call).
            
        Returns:
            Tuple of (spectrum_byte, waveform_samples).
            spectrum_byte is 0-255 byte array (like Web Audio API).
            
        Important:
            The min_db and max_db MUST be the same values used later
            in parse_fft_spectrum() for correct results!
        """
        # Extract audio samples around frame time
        start_time = max(0, frame_time - sample_window / 2)
        samples, sr = self.extract_audio_samples(
            audio_file,
            start_time=start_time,
            duration=sample_window
        )
        
        # Compute spectrum (returns byte array 0-255)
        # IMPORTANT: Use the SAME min_db/max_db that will be used in parse
        spectrum_byte = self.compute_fft_spectrum(
            samples, 
            fft_size=fft_size,
            min_db=min_db,
            max_db=max_db
        )
        
        return spectrum_byte, samples
    
    def get_audio_duration(self, audio_file: str) -> float:
        """
        Get duration of audio file using ffprobe.
        
        Args:
            audio_file: Path to audio file.
            
        Returns:
            Duration in seconds.
        """
        cmd = [
            self.ffprobe_path,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            audio_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            
            return duration
            
        except Exception as e:
            raise RuntimeError(f"Failed to get audio duration: {e}")

