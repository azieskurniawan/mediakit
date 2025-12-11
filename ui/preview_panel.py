"""
Preview Panel - Video preview and playback controls.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QUrl
from PySide6.QtGui import QPixmap, QImage, QPainter, QFont, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from typing import Optional
import os


class PreviewPanel(QWidget):
    """Panel for video preview and playback."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Media player
        self._media_player: Optional[QMediaPlayer] = None
        self._audio_output: Optional[QAudioOutput] = None
        self._video_widget: Optional[QVideoWidget] = None
        
        # State
        self._is_playing = False
        self._current_file = ""
        
        # Timer for position updates
        self._position_timer = QTimer()
        self._position_timer.timeout.connect(self._update_position)
        
        self._setup_ui()
        self._setup_media_player()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Video display area
        self._video_container = QFrame()
        self._video_container.setObjectName("videoContainer")
        self._video_container.setStyleSheet("""
            #videoContainer {
                background-color: #0a0a14;
                border: none;
            }
        """)
        
        video_layout = QVBoxLayout(self._video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Video widget
        self._video_widget = QVideoWidget()
        self._video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        video_layout.addWidget(self._video_widget)
        
        # Placeholder for when no video
        self._placeholder = QLabel("No Preview Available")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("""
            QLabel {
                color: #8892b0;
                font-size: 18px;
                background-color: #0a0a14;
            }
        """)
        self._placeholder.hide()
        video_layout.addWidget(self._placeholder)
        
        layout.addWidget(self._video_container, 1)
        
        # Controls area
        controls = self._create_controls()
        layout.addWidget(controls)
    
    def _create_controls(self) -> QWidget:
        """Create playback controls."""
        controls = QWidget()
        controls.setObjectName("previewControls")
        controls.setFixedHeight(100)
        controls.setStyleSheet("""
            #previewControls {
                background-color: #16213e;
                border-top: 1px solid #0f3460;
            }
        """)
        
        layout = QVBoxLayout(controls)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)
        
        # Progress slider
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 1000)
        self._progress_slider.setValue(0)
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        layout.addWidget(self._progress_slider)
        
        # Time and controls row
        controls_row = QHBoxLayout()
        
        # Time display
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setStyleSheet("color: #00d4ff; font-size: 12px;")
        controls_row.addWidget(self._time_label)
        
        controls_row.addStretch()
        
        # Playback buttons
        self._play_btn = QPushButton("▶ PLAY")
        self._play_btn.setObjectName("playButton")
        self._play_btn.setFixedWidth(100)
        self._play_btn.clicked.connect(self._toggle_playback)
        self._play_btn.setStyleSheet("""
            #playButton {
                background-color: transparent;
                color: #00d4ff;
                border: 1px solid #00d4ff;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            #playButton:hover {
                background-color: rgba(0, 212, 255, 0.1);
            }
        """)
        controls_row.addWidget(self._play_btn)
        
        controls_row.addStretch()
        
        # Volume control
        vol_label = QLabel("VOL")
        vol_label.setStyleSheet("color: #8892b0;")
        controls_row.addWidget(vol_label)
        
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(70)
        self._volume_slider.setFixedWidth(100)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        controls_row.addWidget(self._volume_slider)
        
        layout.addLayout(controls_row)
        
        return controls
    
    def _setup_media_player(self) -> None:
        """Setup the media player."""
        self._media_player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        
        self._media_player.setAudioOutput(self._audio_output)
        self._media_player.setVideoOutput(self._video_widget)
        
        # Connect signals
        self._media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._media_player.durationChanged.connect(self._on_duration_changed)
        self._media_player.positionChanged.connect(self._on_position_changed)
        self._media_player.errorOccurred.connect(self._on_error)
        
        # Set initial volume
        self._audio_output.setVolume(0.7)
    
    def load_video(self, filepath: str) -> bool:
        """
        Load a video file for preview.
        
        Args:
            filepath: Path to video file.
            
        Returns:
            True if loaded successfully.
        """
        if not filepath or not os.path.isfile(filepath):
            self._show_placeholder("No Preview Available")
            return False
        
        self._current_file = filepath
        self._media_player.setSource(QUrl.fromLocalFile(filepath))
        self._video_widget.show()
        self._placeholder.hide()
        return True
    
    def load_image(self, filepath: str) -> bool:
        """
        Load an image for preview.
        
        Args:
            filepath: Path to image file.
            
        Returns:
            True if loaded successfully.
        """
        if not filepath or not os.path.isfile(filepath):
            self._show_placeholder("No Preview Available")
            return False
        
        # Stop any playing video
        self._media_player.stop()
        
        # Load image into placeholder
        pixmap = QPixmap(filepath)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self._placeholder.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._placeholder.setPixmap(scaled)
            self._placeholder.show()
            self._video_widget.hide()
            return True
        
        self._show_placeholder("Failed to load image")
        return False
    
    def _show_placeholder(self, message: str) -> None:
        """Show placeholder with message."""
        self._placeholder.setText(message)
        self._placeholder.setPixmap(QPixmap())  # Clear any pixmap
        self._placeholder.show()
        self._video_widget.hide()
    
    def _toggle_playback(self) -> None:
        """Toggle play/pause."""
        if self._is_playing:
            self._media_player.pause()
        else:
            self._media_player.play()
    
    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """Handle playback state change."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._is_playing = True
            self._play_btn.setText("⏸ PAUSE")
            self._position_timer.start(100)
        else:
            self._is_playing = False
            self._play_btn.setText("▶ PLAY")
            self._position_timer.stop()
    
    def _on_duration_changed(self, duration: int) -> None:
        """Handle duration change."""
        self._update_time_display(self._media_player.position(), duration)
    
    def _on_position_changed(self, position: int) -> None:
        """Handle position change."""
        if not self._progress_slider.isSliderDown():
            duration = self._media_player.duration()
            if duration > 0:
                self._progress_slider.setValue(int(position / duration * 1000))
        self._update_time_display(position, self._media_player.duration())
    
    def _update_position(self) -> None:
        """Update position display."""
        position = self._media_player.position()
        duration = self._media_player.duration()
        self._update_time_display(position, duration)
    
    def _update_time_display(self, position: int, duration: int) -> None:
        """Update time label."""
        pos_str = self._format_time(position)
        dur_str = self._format_time(duration)
        self._time_label.setText(f"{pos_str} / {dur_str}")
    
    def _format_time(self, ms: int) -> str:
        """Format milliseconds to MM:SS."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def _on_slider_pressed(self) -> None:
        """Handle slider press."""
        self._position_timer.stop()
    
    def _on_slider_released(self) -> None:
        """Handle slider release."""
        duration = self._media_player.duration()
        position = int(self._progress_slider.value() / 1000 * duration)
        self._media_player.setPosition(position)
        if self._is_playing:
            self._position_timer.start(100)
    
    def _on_volume_changed(self, value: int) -> None:
        """Handle volume change."""
        if self._audio_output:
            self._audio_output.setVolume(value / 100)
    
    def _on_error(self, error: QMediaPlayer.Error, message: str) -> None:
        """Handle media player error."""
        if error != QMediaPlayer.Error.NoError:
            self._show_placeholder(f"Error: {message}")
    
    def stop(self) -> None:
        """Stop playback."""
        if self._media_player:
            self._media_player.stop()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self._position_timer.stop()
        if self._media_player:
            self._media_player.stop()
            self._media_player.setSource(QUrl())
