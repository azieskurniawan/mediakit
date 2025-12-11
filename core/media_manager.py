"""
Media Manager - Handles video and image file management.
"""
import os
import random
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class MediaMode(Enum):
    """Media source mode."""
    VIDEO_DIRECTORY = "video_directory"
    STATIC_IMAGE = "static_image"


class LoopMode(Enum):
    """Loop mode for media."""
    MATCH_AUDIO = "match_audio"  # Loop to match total audio duration
    CUSTOM_DURATION = "custom_duration"  # Loop to custom duration (HH:MM:SS)
    MULTIPLY_AUDIO = "multiply_audio"  # Loop to N times the audio duration


class AudioSource(Enum):
    """Audio source mode."""
    VIDEO_AUDIO = "video_audio"  # Use audio from video files
    AUDIO_DIRECTORY = "audio_directory"  # Use audio from audio directory (replace)
    MIX_BOTH = "mix_both"  # Mix video audio + audio directory


class OverlayPosition(Enum):
    """Overlay position presets."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
    CUSTOM = "custom"


@dataclass
class LogoOverlay:
    """Logo overlay settings."""
    enabled: bool = False
    filepath: str = ""
    size_percent: int = 15  # Size as percentage of video width
    position: OverlayPosition = OverlayPosition.TOP_RIGHT
    x_offset: int = 20
    y_offset: int = 20
    
    def get_overlay_filter(self, video_width: int, video_height: int) -> str:
        """
        Generate FFmpeg overlay filter string.
        
        Args:
            video_width: Target video width.
            video_height: Target video height.
            
        Returns:
            FFmpeg overlay filter string.
        """
        if not self.enabled or not self.filepath:
            return ""
        
        # Calculate logo width based on percentage
        logo_width = int(video_width * self.size_percent / 100)
        
        # Get position coordinates
        x, y = self._get_position_coords(video_width, video_height, logo_width)
        
        return f"overlay={x}:{y}"
    
    def get_scale_filter(self, video_width: int) -> str:
        """Get scale filter for the logo."""
        logo_width = int(video_width * self.size_percent / 100)
        return f"scale={logo_width}:-1"
    
    def _get_position_coords(self, video_width: int, video_height: int, logo_width: int) -> tuple:
        """Calculate position coordinates based on preset."""
        logo_height = logo_width  # Approximate, will be aspect-preserved
        
        if self.position == OverlayPosition.TOP_LEFT:
            return (self.x_offset, self.y_offset)
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (f"W-w-{self.x_offset}", self.y_offset)
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (self.x_offset, f"H-h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (f"W-w-{self.x_offset}", f"H-h-{self.y_offset}")
        elif self.position == OverlayPosition.CENTER:
            return ("(W-w)/2", "(H-h)/2")
        else:  # CUSTOM
            return (self.x_offset, self.y_offset)


@dataclass
class TextOverlay:
    """Text overlay settings."""
    enabled: bool = False
    text: str = ""
    font_file: str = ""
    font_size: int = 48
    font_color: str = "white"
    position: OverlayPosition = OverlayPosition.TOP_RIGHT
    x_offset: int = 20
    y_offset: int = 20
    
    def get_drawtext_filter(self, video_width: int, video_height: int) -> str:
        """
        Generate FFmpeg drawtext filter string.
        
        Args:
            video_width: Target video width.
            video_height: Target video height.
            
        Returns:
            FFmpeg drawtext filter string.
        """
        if not self.enabled or not self.text:
            return ""
        
        # Escape special characters in text
        escaped_text = self.text.replace("'", "\\'").replace(":", "\\:")
        
        # Get position expression
        x_expr, y_expr = self._get_position_expression()
        
        # Build filter
        filter_parts = [
            f"text='{escaped_text}'",
            f"fontsize={self.font_size}",
            f"fontcolor={self.font_color}",
            f"x={x_expr}",
            f"y={y_expr}"
        ]
        
        if self.font_file and os.path.isfile(self.font_file):
            # Escape backslashes and colons in path for FFmpeg
            escaped_path = self.font_file.replace("\\", "/").replace(":", "\\:")
            filter_parts.insert(1, f"fontfile='{escaped_path}'")
        
        return "drawtext=" + ":".join(filter_parts)
    
    def _get_position_expression(self) -> tuple:
        """Get FFmpeg position expressions."""
        if self.position == OverlayPosition.TOP_LEFT:
            return (str(self.x_offset), str(self.y_offset))
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (f"w-text_w-{self.x_offset}", str(self.y_offset))
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (str(self.x_offset), f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (f"w-text_w-{self.x_offset}", f"h-text_h-{self.y_offset}")
        elif self.position == OverlayPosition.CENTER:
            return ("(w-text_w)/2", "(h-text_h)/2")
        else:  # CUSTOM
            return (str(self.x_offset), str(self.y_offset))


@dataclass
class MediaConfig:
    """Media configuration for export."""
    mode: MediaMode = MediaMode.VIDEO_DIRECTORY
    
    # Video files mode - list of selected video files (in order)
    video_files: List[str] = field(default_factory=list)
    cover_video: str = ""  # Optional cover video (plays first)
    
    # Static image mode
    static_image: str = ""
    
    # Audio - list of selected audio files (in order)
    audio_files: List[str] = field(default_factory=list)
    audio_source: AudioSource = AudioSource.AUDIO_DIRECTORY  # Audio source mode
    audio_mix_video_volume: float = 1.0  # Volume for video audio when mixing (0.0-1.0)
    audio_mix_music_volume: float = 1.0  # Volume for music audio when mixing (0.0-1.0)
    
    # Loop settings
    loop_mode: LoopMode = LoopMode.MATCH_AUDIO
    custom_duration: float = 0.0  # Duration in seconds for CUSTOM_DURATION mode
    audio_multiplier: int = 1  # Multiplier for MULTIPLY_AUDIO mode
    
    # Overlays
    logo_overlay: LogoOverlay = field(default_factory=LogoOverlay)
    text_overlay: TextOverlay = field(default_factory=TextOverlay)
    
    # Sound effect on beat
    sfx_enabled: bool = False
    sfx_file: str = ""
    sfx_volume: float = 0.5  # 0.0 to 1.0
    beat_times: List[float] = field(default_factory=list)  # Beat positions in seconds
    
    def get_target_duration(self, audio_total_duration: float) -> float:
        """
        Calculate target duration based on loop mode.
        
        Args:
            audio_total_duration: Total duration of all audio files.
            
        Returns:
            Target duration in seconds.
        """
        if self.loop_mode == LoopMode.MATCH_AUDIO:
            return audio_total_duration
        elif self.loop_mode == LoopMode.CUSTOM_DURATION:
            return self.custom_duration
        else:  # MULTIPLY_AUDIO
            return audio_total_duration * self.audio_multiplier


class MediaManager:
    """Manages media files for the exporter."""
    
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp'}
    
    def __init__(self):
        """Initialize MediaManager."""
        self._config = MediaConfig()
    
    @property
    def config(self) -> MediaConfig:
        """Get current media configuration."""
        return self._config
    
    @config.setter
    def config(self, value: MediaConfig) -> None:
        """Set media configuration."""
        self._config = value
    
    def get_video_files(self, directory: str, shuffle: bool = True) -> List[str]:
        """
        Get all video files from directory.
        
        Args:
            directory: Path to video directory.
            shuffle: Whether to randomize order.
            
        Returns:
            List of video file paths.
        """
        video_files = []
        dir_path = Path(directory)
        
        if dir_path.is_dir():
            for file in dir_path.iterdir():
                if file.is_file() and file.suffix.lower() in self.VIDEO_EXTENSIONS:
                    video_files.append(str(file))
        
        if shuffle:
            random.shuffle(video_files)
        else:
            video_files.sort()
        
        return video_files
    
    def get_ordered_video_list(self, video_files: List[str], cover_video: Optional[str] = None) -> List[str]:
        """
        Get ordered list of videos with cover video first.
        
        Args:
            video_files: List of video file paths.
            cover_video: Optional cover video path (placed first).
            
        Returns:
            Ordered list of video file paths.
        """
        videos = video_files.copy()
        
        # Remove cover video from list if present
        if cover_video and cover_video in videos:
            videos.remove(cover_video)
        
        # Insert cover video at the beginning
        if cover_video and os.path.isfile(cover_video):
            videos.insert(0, cover_video)
        
        return videos
    
    def is_valid_video(self, filepath: str) -> bool:
        """Check if file is a valid video file."""
        path = Path(filepath)
        return path.is_file() and path.suffix.lower() in self.VIDEO_EXTENSIONS
    
    def is_valid_image(self, filepath: str) -> bool:
        """Check if file is a valid image file."""
        path = Path(filepath)
        return path.is_file() and path.suffix.lower() in self.IMAGE_EXTENSIONS
    
    def get_audio_files(self) -> List[str]:
        """
        Get list of audio files from config.
        
        Returns:
            List of audio file paths.
        """
        return self._config.audio_files.copy()
    
    def get_total_audio_duration(self, ffprobe_path: str = "ffprobe") -> float:
        """
        Calculate total duration of all audio files.
        
        Args:
            ffprobe_path: Path to ffprobe executable.
            
        Returns:
            Total duration in seconds.
        """
        from core.audio_utils import AudioUtils
        
        audio_utils = AudioUtils(ffprobe_path)
        total = 0.0
        for filepath in self._config.audio_files:
            duration = audio_utils.get_duration(filepath)
            if duration:
                total += duration
        return total
    
    def validate_config(self) -> List[str]:
        """
        Validate current media configuration.
        
        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []
        
        if self._config.mode == MediaMode.VIDEO_DIRECTORY:
            if not self._config.video_files:
                errors.append("No video files selected.")
            else:
                # Check if all video files exist
                for filepath in self._config.video_files:
                    if not os.path.isfile(filepath):
                        errors.append(f"Video file not found: {os.path.basename(filepath)}")
                        break
            
            if self._config.cover_video and not os.path.isfile(self._config.cover_video):
                errors.append("Cover video file does not exist.")
        
        elif self._config.mode == MediaMode.STATIC_IMAGE:
            if not self._config.static_image:
                errors.append("Static image is not set.")
            elif not self.is_valid_image(self._config.static_image):
                errors.append("Static image file is invalid or does not exist.")
        
        if not self._config.audio_files:
            errors.append("No audio files selected.")
        else:
            # Check if all audio files exist
            for filepath in self._config.audio_files:
                if not os.path.isfile(filepath):
                    errors.append(f"Audio file not found: {os.path.basename(filepath)}")
                    break
        
        # Validate loop settings
        if self._config.loop_mode == LoopMode.CUSTOM_DURATION:
            if self._config.custom_duration <= 0:
                errors.append("Custom duration must be greater than 0.")
        
        # Validate overlays
        if self._config.logo_overlay.enabled:
            if not self._config.logo_overlay.filepath:
                errors.append("Logo overlay is enabled but no file is selected.")
            elif not self.is_valid_image(self._config.logo_overlay.filepath):
                errors.append("Logo overlay file is invalid or does not exist.")
        
        if self._config.text_overlay.enabled:
            if not self._config.text_overlay.text:
                errors.append("Text overlay is enabled but no text is entered.")
        
        return errors
