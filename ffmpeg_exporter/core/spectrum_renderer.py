"""
Custom Audio Spectrum Renderer using librosa and PIL.
Provides better control than FFmpeg built-in filters.
Optimized for professional-quality output like Filmora.
"""
import os
import tempfile
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter1d
import librosa


class SpectrumRenderer:
    """Renders custom audio spectrum visualizations."""
    
    def __init__(self, audio_path: str):
        """
        Initialize spectrum renderer.
        
        Args:
            audio_path: Path to audio file.
        """
        self.audio_path = audio_path
        self.y = None
        self.sr = None
        self._prev_spectrum = None  # For smoothing
        self._load_audio()
    
    def _load_audio(self) -> None:
        """Load audio file with librosa."""
        # Load audio file
        self.y, self.sr = librosa.load(self.audio_path, sr=None, mono=True)
    
    def _smooth_spectrum(self, spectrum_data: np.ndarray, smoothing: float = 0.3) -> np.ndarray:
        """
        Apply temporal smoothing to reduce jitter between frames.
        
        Args:
            spectrum_data: Current frame spectrum data.
            smoothing: Smoothing factor (0 = no smoothing, 1 = max smoothing).
            
        Returns:
            Smoothed spectrum data.
        """
        if self._prev_spectrum is None:
            self._prev_spectrum = spectrum_data.copy()
            return spectrum_data
        
        # Exponential moving average
        smoothed = smoothing * self._prev_spectrum + (1 - smoothing) * spectrum_data
        self._prev_spectrum = smoothed
        
        return smoothed
    
    def render_bars(
        self,
        width: int = 1920,
        height: int = 200,
        bar_count: int = 50,
        color: Tuple[int, int, int] = (59, 130, 246),  # RGB
        fps: int = 30,
        output_dir: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """
        Render spectrum bars as video frames.
        
        Args:
            width: Video width in pixels.
            height: Video height in pixels.
            bar_count: Number of bars to display.
            color: RGB color tuple (0-255 each).
            fps: Frames per second.
            output_dir: Directory to save frames (temp if None).
            
        Returns:
            Tuple of (frames directory path, list of frame paths).
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='spectrum_')
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate spectrogram
        # Use mel spectrogram for better frequency distribution
        hop_length = int(self.sr / fps)  # Samples per frame
        n_fft = 4096  # Higher resolution for better quality
        
        # Compute mel spectrogram with optimized parameters
        S = librosa.feature.melspectrogram(
            y=self.y,
            sr=self.sr,
            n_mels=bar_count,  # Number of mel bands = bar count
            n_fft=n_fft,
            hop_length=hop_length,
            power=2.0,
            fmin=20,  # Minimum frequency (20 Hz)
            fmax=16000  # Maximum frequency (16 kHz, human hearing range)
        )
        
        # Convert to dB scale with proper reference
        S_db = librosa.power_to_db(S, ref=np.max)
        
        # Apply dynamic range compression for better visualization
        # Boost quiet sounds, compress loud sounds
        S_db_compressed = np.clip(S_db, -60, 0)  # Clip to -60dB to 0dB range
        
        # Normalize to 0-1 range for rendering
        S_norm = (S_db_compressed + 60) / 60  # Now 0 to 1
        
        # Apply smoothing across time (reduces flickering)
        S_norm = gaussian_filter1d(S_norm, sigma=0.5, axis=1)
        
        # Render each frame
        frame_paths = []
        total_frames = S_norm.shape[1]
        
        # Reset smoothing state
        self._prev_spectrum = None
        
        for frame_idx in range(total_frames):
            # Get spectrum data for this frame
            spectrum_data = S_norm[:, frame_idx]
            
            # Apply temporal smoothing (reduces jitter between frames)
            spectrum_data = self._smooth_spectrum(spectrum_data, smoothing=0.3)
            
            # Create image with transparency
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Calculate bar dimensions with optimal spacing
            total_spacing = width * 0.1  # 10% of width for all spacing
            spacing_per_gap = total_spacing / (bar_count + 1)
            usable_width = width - total_spacing
            actual_bar_width = usable_width / bar_count
            
            # Draw bars
            for i in range(bar_count):
                # Get bar height (normalized 0-1)
                bar_height_norm = spectrum_data[i]
                
                # Apply exponential scaling for more dynamic visualization
                # Makes quiet sounds more visible
                bar_height_norm = np.power(bar_height_norm, 0.7)
                
                # Calculate bar position
                x = spacing_per_gap + i * (actual_bar_width + spacing_per_gap)
                
                # Calculate bar height with minimum visibility
                min_height = 3  # Minimum 3 pixels even for silence
                bar_height_pixels = min_height + bar_height_norm * (height - min_height)
                y_top = height - bar_height_pixels
                
                # Ensure valid coordinates
                y_top = max(0, min(y_top, height - 2))
                y_bottom = height
                
                # Skip if invalid
                if y_top >= y_bottom:
                    continue
                
                # Calculate corner radius (proportional to bar width)
                corner_radius = min(actual_bar_width / 2.5, 8)
                
                # Draw bar with rounded top
                self._draw_rounded_bar(
                    draw, 
                    x, 
                    y_top, 
                    x + actual_bar_width, 
                    y_bottom,
                    radius=corner_radius,
                    fill=color
                )
            
            # Save frame with high quality
            frame_path = os.path.join(output_dir, f'frame_{frame_idx:06d}.png')
            img.save(frame_path, 'PNG', optimize=False)
            frame_paths.append(frame_path)
        
        return output_dir, frame_paths
    
    def _draw_rounded_bar(
        self,
        draw: ImageDraw.ImageDraw,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float = 5,
        fill: Tuple[int, int, int] = (255, 255, 255)
    ) -> None:
        """
        Draw a bar with perfectly rounded top corners.
        Uses PIL rounded_rectangle for smooth corners.
        """
        # Ensure valid coordinates
        if y1 >= y2 or x1 >= x2:
            return
        
        # Calculate actual bar height
        bar_height = y2 - y1
        
        # Adjust radius based on bar width and height
        bar_width = x2 - x1
        max_radius = min(bar_width / 2, bar_height / 2)
        radius = min(radius, max_radius)
        
        # For very short bars, draw simple rectangle
        if bar_height < 4 or radius < 2:
            draw.rectangle([x1, y1, x2, y2], fill=fill)
            return
        
        # Draw rounded rectangle (rounded at top only)
        # PIL doesn't have "rounded top only", so we'll compose it
        
        # 1. Draw main rectangle body (no rounding at bottom)
        if y1 + radius < y2:
            draw.rectangle([x1, y1 + radius, x2, y2], fill=fill)
        
        # 2. Draw rounded top portion with proper corners
        # Left top corner
        draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 
                      180, 270, fill=fill)
        
        # Right top corner  
        draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 
                      270, 360, fill=fill)
        
        # Top center fill
        if x1 + radius < x2 - radius:
            draw.rectangle([x1 + radius, y1, x2 - radius, y1 + radius], fill=fill)
    
    def create_spectrum_video(
        self,
        output_path: str,
        width: int = 1920,
        height: int = 200,
        bar_count: int = 50,
        color: Tuple[int, int, int] = (59, 130, 246),
        fps: int = 30
    ) -> str:
        """
        Create spectrum video from audio.
        
        Args:
            output_path: Output video path.
            width: Video width.
            height: Video height.
            bar_count: Number of bars.
            color: RGB color tuple.
            fps: Frames per second.
            
        Returns:
            Path to generated video.
        """
        import subprocess
        
        # Render frames
        frames_dir, frame_paths = self.render_bars(
            width=width,
            height=height,
            bar_count=bar_count,
            color=color,
            fps=fps
        )
        
        # Create video from frames using FFmpeg
        # Use PNG sequence input with alpha channel (transparency)
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-framerate', str(fps),
            '-i', os.path.join(frames_dir, 'frame_%06d.png'),
            '-c:v', 'png',  # Use PNG codec to preserve alpha
            '-pix_fmt', 'rgba',  # RGBA for full transparency
            output_path.replace('.mp4', '.mov')  # MOV container supports alpha
        ]
        
        # Update output path to MOV
        output_path = output_path.replace('.mp4', '.mov')
        
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        
        # Cleanup frames
        for frame_path in frame_paths:
            try:
                os.remove(frame_path)
            except:
                pass
        
        try:
            os.rmdir(frames_dir)
        except:
            pass
        
        return output_path
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#3b82f6" or "3b82f6").
            
        Returns:
            RGB tuple (r, g, b).
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

