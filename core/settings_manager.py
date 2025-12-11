"""
Settings Manager - Handles application configuration persistence.
"""
import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional


@dataclass
class AppSettings:
    """Application settings data class."""
    ffmpeg_path: str = ""
    ffprobe_path: str = ""
    last_output_dir: str = ""
    last_video_dir: str = ""
    last_audio_dir: str = ""
    
    def is_ffmpeg_configured(self) -> bool:
        """Check if FFmpeg path is configured and exists."""
        return bool(self.ffmpeg_path) and os.path.isfile(self.ffmpeg_path)
    
    def is_ffprobe_configured(self) -> bool:
        """Check if FFprobe path is configured and exists."""
        return bool(self.ffprobe_path) and os.path.isfile(self.ffprobe_path)


class SettingsManager:
    """Manages loading and saving application settings."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize settings manager.
        
        Args:
            config_dir: Optional custom config directory path.
        """
        if config_dir is None:
            # Default to config folder relative to this module
            self._config_dir = Path(__file__).parent.parent / "config"
        else:
            self._config_dir = Path(config_dir)
        
        self._config_file = self._config_dir / "settings.json"
        self._settings: AppSettings = AppSettings()
        self._ensure_config_dir()
        self.load()
    
    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def settings(self) -> AppSettings:
        """Get current settings."""
        return self._settings
    
    def load(self) -> AppSettings:
        """
        Load settings from JSON file.
        
        Returns:
            Loaded AppSettings object.
        """
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._settings = AppSettings(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Could not load settings: {e}")
                self._settings = AppSettings()
        else:
            self._settings = AppSettings()
            self.save()  # Create default config file
        
        return self._settings
    
    def save(self) -> bool:
        """
        Save current settings to JSON file.
        
        Returns:
            True if save was successful, False otherwise.
        """
        try:
            self._ensure_config_dir()
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._settings), f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False
    
    def update(self, **kwargs) -> None:
        """
        Update settings with provided keyword arguments.
        
        Args:
            **kwargs: Setting key-value pairs to update.
        """
        for key, value in kwargs.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
        self.save()
    
    def get_ffmpeg_path(self) -> str:
        """Get FFmpeg executable path."""
        return self._settings.ffmpeg_path
    
    def get_ffprobe_path(self) -> str:
        """Get FFprobe executable path."""
        return self._settings.ffprobe_path
    
    def set_ffmpeg_path(self, path: str) -> None:
        """Set FFmpeg executable path."""
        self._settings.ffmpeg_path = path
        self.save()
    
    def set_ffprobe_path(self, path: str) -> None:
        """Set FFprobe executable path."""
        self._settings.ffprobe_path = path
        self.save()
