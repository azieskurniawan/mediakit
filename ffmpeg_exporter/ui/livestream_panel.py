"""
Livestream Panel - UI for livestream configuration.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QSpinBox,
    QGroupBox, QFormLayout, QCheckBox, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from datetime import datetime

from core.livestream_builder import LivestreamSettings, LivestreamBuilder
from core.settings_manager import SettingsManager
from core.stream_scheduler import StreamScheduler


class LivestreamPanel(QWidget):
    """Panel for livestream configuration."""
    
    # Signal emitted when user wants to start stream
    start_stream_requested = Signal(dict)  # LivestreamSettings as dict
    
    def __init__(self, settings_manager: SettingsManager, stream_scheduler: StreamScheduler):
        super().__init__()
        self._settings_manager = settings_manager
        self._stream_scheduler = stream_scheduler
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Stream destination group
        dest_group = self._create_destination_group()
        layout.addWidget(dest_group)
        
        # Video settings group
        video_group = self._create_video_settings_group()
        layout.addWidget(video_group)
        
        # Audio settings group
        audio_group = self._create_audio_settings_group()
        layout.addWidget(audio_group)
        
        # Duration settings group
        duration_group = self._create_duration_group()
        layout.addWidget(duration_group)
        
        # Schedule info group
        schedule_group = self._create_schedule_group()
        layout.addWidget(schedule_group)
        
        layout.addStretch()
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._start_btn = QPushButton("🔴 START LIVESTREAM")
        self._start_btn.setObjectName("livestreamButton")
        self._start_btn.setFixedHeight(50)
        self._start_btn.clicked.connect(self._on_start_stream)
        button_layout.addWidget(self._start_btn)
        
        layout.addLayout(button_layout)
        
        scroll.setWidget(content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # Apply styles
        self._apply_styles()
    
    def _create_destination_group(self) -> QGroupBox:
        """Create stream destination group."""
        group = QGroupBox("Stream Destination")
        layout = QFormLayout()
        layout.setSpacing(10)
        
        # RTMP URL
        self._rtmp_url_input = QLineEdit("rtmp://a.rtmp.youtube.com/live2/")
        self._rtmp_url_input.setPlaceholderText("rtmp://...")
        layout.addRow("RTMP URL:", self._rtmp_url_input)
        
        # Stream key
        stream_key_layout = QHBoxLayout()
        self._stream_key_input = QLineEdit()
        self._stream_key_input.setPlaceholderText("Enter your YouTube stream key")
        self._stream_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        stream_key_layout.addWidget(self._stream_key_input)
        
        self._show_key_btn = QPushButton("👁")
        self._show_key_btn.setFixedWidth(40)
        self._show_key_btn.setCheckable(True)
        self._show_key_btn.toggled.connect(self._toggle_stream_key_visibility)
        stream_key_layout.addWidget(self._show_key_btn)
        
        layout.addRow("Stream Key:", stream_key_layout)
        
        # Help text
        help_label = QLabel(
            "💡 Get your stream key from YouTube Studio > Go Live > Stream Settings"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #8892b0; font-size: 10px; padding: 5px;")
        layout.addRow("", help_label)
        
        group.setLayout(layout)
        return group
    
    def _create_video_settings_group(self) -> QGroupBox:
        """Create video settings group."""
        group = QGroupBox("Video Settings")
        layout = QFormLayout()
        layout.setSpacing(10)
        
        # Preset selector
        self._preset_combo = QComboBox()
        presets = list(LivestreamBuilder.get_youtube_presets().keys())
        self._preset_combo.addItems(presets)
        self._preset_combo.setCurrentText("YouTube 1080p 30fps")
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        layout.addRow("Preset:", self._preset_combo)
        
        # Resolution
        resolution_layout = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(640, 3840)
        self._width_spin.setValue(1920)
        self._width_spin.setSuffix(" px")
        resolution_layout.addWidget(self._width_spin)
        
        resolution_layout.addWidget(QLabel("×"))
        
        self._height_spin = QSpinBox()
        self._height_spin.setRange(360, 2160)
        self._height_spin.setValue(1080)
        self._height_spin.setSuffix(" px")
        resolution_layout.addWidget(self._height_spin)
        
        layout.addRow("Resolution:", resolution_layout)
        
        # FPS
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(15, 60)
        self._fps_spin.setValue(30)
        self._fps_spin.setSuffix(" fps")
        layout.addRow("Frame Rate:", self._fps_spin)
        
        # Bitrate
        self._bitrate_spin = QSpinBox()
        self._bitrate_spin.setRange(1000, 15000)
        self._bitrate_spin.setValue(4500)
        self._bitrate_spin.setSuffix(" kbps")
        self._bitrate_spin.setSingleStep(500)
        layout.addRow("Video Bitrate:", self._bitrate_spin)
        
        # Encoding method
        self._encoding_combo = QComboBox()
        self._encoding_combo.addItems([
            "nvenc = GPU NVIDIA Fast",
            "nvenc_hq = GPU NVIDIA High Quality",
            "x264 = CPU (slower)",
        ])
        layout.addRow("Encoding:", self._encoding_combo)
        
        group.setLayout(layout)
        return group
    
    def _create_audio_settings_group(self) -> QGroupBox:
        """Create audio settings group."""
        group = QGroupBox("Audio Settings")
        layout = QFormLayout()
        layout.setSpacing(10)
        
        # Audio bitrate
        self._audio_bitrate_spin = QSpinBox()
        self._audio_bitrate_spin.setRange(64, 320)
        self._audio_bitrate_spin.setValue(128)
        self._audio_bitrate_spin.setSuffix(" kbps")
        layout.addRow("Audio Bitrate:", self._audio_bitrate_spin)
        
        group.setLayout(layout)
        return group
    
    def _create_duration_group(self) -> QGroupBox:
        """Create duration settings group."""
        group = QGroupBox("Stream Duration")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Auto-stop option
        duration_layout = QHBoxLayout()
        
        self._auto_stop_check = QCheckBox("Auto-stop after")
        self._auto_stop_check.toggled.connect(self._on_auto_stop_toggled)
        duration_layout.addWidget(self._auto_stop_check)
        
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 1440)  # 1 min to 24 hours
        self._duration_spin.setValue(60)
        self._duration_spin.setSuffix(" minutes")
        self._duration_spin.setEnabled(False)
        duration_layout.addWidget(self._duration_spin)
        
        duration_layout.addStretch()
        
        layout.addLayout(duration_layout)
        
        # Info label
        info_label = QLabel("💡 If disabled, stream runs until manually stopped")
        info_label.setStyleSheet("color: #8892b0; font-size: 10px; padding: 5px;")
        layout.addWidget(info_label)
        
        group.setLayout(layout)
        return group
    
    def _toggle_stream_key_visibility(self, checked: bool) -> None:
        """Toggle stream key visibility."""
        if checked:
            self._stream_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._stream_key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def _on_preset_changed(self, preset_name: str) -> None:
        """Handle preset change."""
        presets = LivestreamBuilder.get_youtube_presets()
        if preset_name in presets:
            settings = presets[preset_name]
            self._width_spin.setValue(settings.width)
            self._height_spin.setValue(settings.height)
            self._fps_spin.setValue(settings.fps)
            self._bitrate_spin.setValue(settings.bitrate_kbps)
            self._audio_bitrate_spin.setValue(settings.audio_bitrate_kbps)
    
    def _on_auto_stop_toggled(self, checked: bool) -> None:
        """Handle auto-stop toggle."""
        self._duration_spin.setEnabled(checked)
    
    def _on_start_stream(self) -> None:
        """Handle start stream button click."""
        # Validate stream key
        if not self._stream_key_input.text().strip():
            QMessageBox.warning(
                self,
                "Stream Key Required",
                "Please enter your YouTube stream key."
            )
            return
        
        # Get settings
        settings = self.get_settings()
        
        # Emit signal
        self.start_stream_requested.emit(settings)
    
    def get_settings(self) -> dict:
        """Get livestream settings as dictionary."""
        # Determine encoding method
        encoding_text = self._encoding_combo.currentText()
        if "nvenc_hq" in encoding_text:
            from core.ffmpeg_builder import EncodingMethod
            encoding = EncodingMethod.NVENC_HQ
        elif "nvenc" in encoding_text:
            from core.ffmpeg_builder import EncodingMethod
            encoding = EncodingMethod.NVENC
        else:
            from core.ffmpeg_builder import EncodingMethod
            encoding = EncodingMethod.X264
        
        return {
            'rtmp_url': self._rtmp_url_input.text().strip(),
            'stream_key': self._stream_key_input.text().strip(),
            'width': self._width_spin.value(),
            'height': self._height_spin.value(),
            'fps': self._fps_spin.value(),
            'bitrate_kbps': self._bitrate_spin.value(),
            'audio_bitrate_kbps': self._audio_bitrate_spin.value(),
            'duration_minutes': self._duration_spin.value() if self._auto_stop_check.isChecked() else 0,
            'encoding_method': encoding
        }
    
    def _apply_styles(self) -> None:
        """Apply custom styles."""
        self.setStyleSheet("""
            #livestreamButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px 30px;
                font-weight: bold;
                font-size: 14px;
            }
            
            #livestreamButton:hover {
                background-color: #c0392b;
            }
            
            #livestreamButton:pressed {
                background-color: #a93226;
            }
            
            #scheduleButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            
            #scheduleButton:hover {
                background-color: #1a4f7a;
            }
            
            #nextScheduleInfo {
                font-size: 12px;
            }
        """)

