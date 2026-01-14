"""
Live Visualizer Player - Real-time audio visualization playback.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QUrl
from PIL import Image
from PIL.ImageQt import ImageQt
import numpy as np

from core.audio_analyzer import AudioAnalyzer
from core.visualizer_renderer import VisualizerRenderer
from core.media_manager import VisualizerConfig, VisualizerType


class LiveVisualizerPlayer(QWidget):
    """Live audio visualizer player with real-time playback."""
    
    playback_stopped = Signal()
    
    def __init__(self):
        super().__init__()
        self._audio_files = []
        self._current_audio_index = 0
        self._visualizer_config = None
        self._is_playing = False
        
        # Audio player
        self._media_player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._media_player.setAudioOutput(self._audio_output)
        
        # Visualizer components
        self._analyzer = None
        self._renderer = VisualizerRenderer()
        
        # Smoothing buffers for continuous visualization
        self._spectrum_buffer = np.array([])
        self._waveform_buffer = np.array([])
        
        # Render timer (30 FPS)
        self._render_timer = QTimer()
        self._render_timer.timeout.connect(self._render_frame)
        self._render_fps = 30
        
        self._init_ui()
        
        # Connect media player signals
        self._media_player.positionChanged.connect(self._on_position_changed)
        self._media_player.durationChanged.connect(self._on_duration_changed)
        self._media_player.playbackStateChanged.connect(self._on_playback_state_changed)
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🎵 LIVE VISUALIZER PLAYER")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Visualizer display frame
        self._viz_frame = QFrame()
        self._viz_frame.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self._viz_frame.setMinimumSize(800, 400)
        self._viz_frame.setStyleSheet("background-color: #000000;")
        
        viz_layout = QVBoxLayout(self._viz_frame)
        self._viz_label = QLabel()
        self._viz_label.setAlignment(Qt.AlignCenter)
        self._viz_label.setStyleSheet("color: #888;")
        self._viz_label.setText("▶ Press PLAY to start visualization")
        viz_layout.addWidget(self._viz_label)
        
        layout.addWidget(self._viz_frame, stretch=1)
        
        # Progress bar
        progress_layout = QHBoxLayout()
        self._time_label_start = QLabel("00:00")
        self._time_label_start.setMinimumWidth(50)
        progress_layout.addWidget(self._time_label_start)
        
        self._progress_slider = QSlider(Qt.Horizontal)
        self._progress_slider.setRange(0, 1000)
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        progress_layout.addWidget(self._progress_slider)
        
        self._time_label_end = QLabel("00:00")
        self._time_label_end.setMinimumWidth(50)
        self._time_label_end.setAlignment(Qt.AlignRight)
        progress_layout.addWidget(self._time_label_end)
        
        layout.addLayout(progress_layout)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        self._play_btn = QPushButton("▶ PLAY")
        self._play_btn.clicked.connect(self._toggle_playback)
        self._play_btn.setMinimumHeight(40)
        controls_layout.addWidget(self._play_btn)
        
        self._stop_btn = QPushButton("⏹ STOP")
        self._stop_btn.clicked.connect(self._stop_playback)
        self._stop_btn.setMinimumHeight(40)
        controls_layout.addWidget(self._stop_btn)
        
        self._prev_btn = QPushButton("⏮ PREV")
        self._prev_btn.clicked.connect(self._play_previous)
        self._prev_btn.setMinimumHeight(40)
        controls_layout.addWidget(self._prev_btn)
        
        self._next_btn = QPushButton("⏭ NEXT")
        self._next_btn.clicked.connect(self._play_next)
        self._next_btn.setMinimumHeight(40)
        controls_layout.addWidget(self._next_btn)
        
        layout.addLayout(controls_layout)
        
        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self._status_label)
    
    def set_audio_files(self, audio_files: list):
        """Set audio files for playback."""
        self._audio_files = audio_files
        self._current_audio_index = 0
        if audio_files:
            self._status_label.setText(f"Loaded {len(audio_files)} audio file(s)")
    
    def set_visualizer_config(self, config: VisualizerConfig):
        """Set visualizer configuration."""
        self._visualizer_config = config
    
    def set_ffmpeg_path(self, ffmpeg_path: str):
        """Set FFmpeg path for audio analyzer."""
        self._analyzer = AudioAnalyzer(ffmpeg_path=ffmpeg_path)
    
    def _toggle_playback(self):
        """Toggle play/pause."""
        if not self._audio_files:
            self._status_label.setText("❌ No audio files loaded")
            return
        
        if not self._visualizer_config or self._visualizer_config.type == VisualizerType.NONE:
            self._status_label.setText("❌ No visualizer selected")
            return
        
        if self._media_player.playbackState() == QMediaPlayer.PlayingState:
            self._media_player.pause()
            self._render_timer.stop()
            self._play_btn.setText("▶ PLAY")
        else:
            if self._media_player.playbackState() == QMediaPlayer.StoppedState:
                # Start new playback
                audio_file = self._audio_files[self._current_audio_index]
                self._media_player.setSource(QUrl.fromLocalFile(audio_file))
                self._status_label.setText(f"Playing: {audio_file.split('/')[-1]}")
            
            self._media_player.play()
            self._render_timer.start(1000 // self._render_fps)  # 30 FPS
            self._play_btn.setText("⏸ PAUSE")
    
    def _stop_playback(self):
        """Stop playback."""
        self._media_player.stop()
        self._render_timer.stop()
        self._play_btn.setText("▶ PLAY")
        self._viz_label.setText("⏹ Stopped")
        self._status_label.setText("Ready")
        self.playback_stopped.emit()
    
    def _play_previous(self):
        """Play previous audio."""
        if not self._audio_files:
            return
        
        self._current_audio_index = (self._current_audio_index - 1) % len(self._audio_files)
        self._media_player.stop()
        self._toggle_playback()
    
    def _play_next(self):
        """Play next audio."""
        if not self._audio_files:
            return
        
        self._current_audio_index = (self._current_audio_index + 1) % len(self._audio_files)
        self._media_player.stop()
        self._toggle_playback()
    
    def _render_frame(self):
        """Render visualizer frame for current audio position."""
        if not self._analyzer or not self._visualizer_config:
            return
        
        try:
            # Get current playback position
            position_ms = self._media_player.position()
            position_sec = position_ms / 1000.0
            
            # Get current audio file
            audio_file = self._audio_files[self._current_audio_index]
            
            # Get max_db from config for consistent byte mapping
            config = self._visualizer_config.bar_spectrum if self._visualizer_config.type == VisualizerType.BAR_SPECTRUM else None
            max_db_config = config.max_db if config else -30
            
            # Analyze audio at current position
            # IMPORTANT: Pass min_db/max_db for consistent byte conversion
            spectrum_byte, waveform_samples = self._analyzer.analyze_audio_for_frame(
                audio_file,
                frame_time=position_sec,
                fft_size=2048,
                sample_window=0.05,
                min_db=-100,  # Astrofox default
                max_db=max_db_config
            )
            
            # Render based on visualizer type
            if self._visualizer_config.type == VisualizerType.BAR_SPECTRUM:
                config = self._visualizer_config.bar_spectrum
                
                # Calculate actual number of bins based on frequency range (like Astrofox)
                sample_rate = self._analyzer.sample_rate
                fft_size = 2048
                freq_per_bin = sample_rate / fft_size  # ~21.5 Hz per bin
                
                # Calculate bins in frequency range
                min_bin = int(config.min_frequency / freq_per_bin)
                max_bin = int(config.max_frequency / freq_per_bin)
                num_bins = max_bin - min_bin
                
                # Clamp to reasonable range
                num_bins = max(1, min(num_bins, 500))
                
                # Parse spectrum with correct bin count (EXACT Astrofox algorithm)
                spectrum_normalized = self._analyzer.parse_fft_spectrum(
                    spectrum_byte,
                    min_db=-100,  # Astrofox default
                    max_db=config.max_db,
                    min_freq=config.min_frequency,
                    max_freq=config.max_frequency,
                    num_bins=num_bins,  # Use frequency-based bin count!
                    smoothing=config.smoothing,
                    smoothing_buffer=self._spectrum_buffer,
                    normalize=config.normalize  # Astrofox default: True
                )
                
                # Render bars
                viz_img = self._renderer.render_bar_spectrum(
                    spectrum_normalized,
                    config.width,
                    config.height,
                    shadow_height=config.shadow_height,
                    bar_width_auto=config.bar_width_auto,
                    bar_width=config.bar_width,
                    bar_spacing_auto=config.bar_spacing_auto,
                    bar_spacing=config.bar_spacing,
                    bar_color_start=config.bar_color_start,
                    bar_color_end=config.bar_color_end,
                    shadow_color_start=config.shadow_color_start,
                    shadow_color_end=config.shadow_color_end,
                    opacity=config.opacity,
                    normalize=config.normalize
                )
            
            elif self._visualizer_config.type == VisualizerType.SOUND_WAVE:
                config = self._visualizer_config.sound_wave
                
                # Parse waveform
                waveform_normalized = self._analyzer.parse_waveform(
                    waveform_samples,
                    num_points=config.width,
                    smoothing=config.smoothing,
                    smoothing_buffer=self._waveform_buffer
                )
                
                # Render waveform
                viz_img = self._renderer.render_sound_wave(
                    waveform_normalized,
                    config.width,
                    config.height,
                    line_width=config.line_width,
                    wavelength=config.wavelength,
                    stroke=config.stroke,
                    stroke_color=config.stroke_color,
                    fill=config.fill,
                    fill_color=config.fill_color,
                    taper_edges=config.taper_edges,
                    opacity=config.opacity
                )
            else:
                return
            
            # Display in label
            if viz_img:
                qimage = ImageQt(viz_img.convert('RGBA'))
                pixmap = QPixmap.fromImage(qimage)
                
                # Scale to fit display
                scaled_pixmap = pixmap.scaled(
                    self._viz_frame.width() - 20,
                    self._viz_frame.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self._viz_label.setPixmap(scaled_pixmap)
        
        except Exception as e:
            print(f"Render error: {e}")
    
    def _on_position_changed(self, position: int):
        """Handle position change."""
        # Update progress slider
        duration = self._media_player.duration()
        if duration > 0:
            self._progress_slider.setValue(int(position / duration * 1000))
        
        # Update time labels
        self._time_label_start.setText(self._format_time(position))
    
    def _on_duration_changed(self, duration: int):
        """Handle duration change."""
        self._time_label_end.setText(self._format_time(duration))
    
    def _on_playback_state_changed(self, state):
        """Handle playback state change."""
        if state == QMediaPlayer.StoppedState:
            # Auto-play next if available
            if self._current_audio_index < len(self._audio_files) - 1:
                self._play_next()
            else:
                self._stop_playback()
    
    def _on_slider_pressed(self):
        """Handle slider press."""
        self._render_timer.stop()
    
    def _on_slider_released(self):
        """Handle slider release."""
        # Seek to position
        duration = self._media_player.duration()
        if duration > 0:
            position = int(self._progress_slider.value() / 1000 * duration)
            self._media_player.setPosition(position)
        
        if self._media_player.playbackState() == QMediaPlayer.PlayingState:
            self._render_timer.start(1000 // self._render_fps)
    
    def _format_time(self, ms: int) -> str:
        """Format milliseconds to MM:SS."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def closeEvent(self, event):
        """Handle close event - stop playback."""
        self._media_player.stop()
        self._render_timer.stop()
        event.accept()

