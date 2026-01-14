"""
Media Panel - UI for selecting video/image and audio sources.
"""
import os
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QRadioButton, QButtonGroup, QGroupBox,
    QFileDialog, QCheckBox, QScrollArea, QFrame, QMessageBox,
    QListWidget, QListWidgetItem, QSpinBox, QComboBox, QAbstractItemView,
    QSlider
)
from PySide6.QtCore import Qt, Signal

from core.settings_manager import SettingsManager
from core.media_manager import MediaMode, LoopMode, AudioSource, AudioLayer
from core.audio_utils import AudioUtils
from ui.audio_layer_dialog import AudioLayerDialog


class MediaPanel(QWidget):
    """Panel for media source selection."""
    
    # Signals
    settings_changed = Signal()
    video_selected = Signal(str)  # Emits filepath when video is selected for preview
    
    VIDEO_EXTENSIONS = "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm)"
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings_manager = settings_manager
        self._audio_utils = AudioUtils()
        self._audio_files = []  # List of selected audio files
        self._video_files = []  # List of selected video files
        self._beat_times = []  # Detected beat times in seconds
        self._sfx_file = ""  # Sound effect file path
        
        # Update ffprobe path
        if settings_manager.settings.ffprobe_path:
            self._audio_utils.ffprobe_path = settings_manager.settings.ffprobe_path
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Visuals section
        visuals_group = self._create_visuals_section()
        layout.addWidget(visuals_group)
        
        # Loop settings section
        loop_group = self._create_loop_section()
        layout.addWidget(loop_group)
        
        # Audio section
        audio_group = self._create_audio_section()
        layout.addWidget(audio_group)
        
        # Audio Layers section (Multi-layer audio / sound effects)
        audio_layers_group = self._create_audio_layers_section()
        layout.addWidget(audio_layers_group)
        
        # Sound Effect section
        sfx_group = self._create_sfx_section()
        layout.addWidget(sfx_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _create_visuals_section(self) -> QGroupBox:
        """Create the visuals selection section."""
        group = QGroupBox("VISUALS")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        
        self._video_mode_radio = QRadioButton("Video Files")
        self._video_mode_radio.setChecked(True)
        self._image_mode_radio = QRadioButton("Static Image")
        
        self._mode_group = QButtonGroup()
        self._mode_group.addButton(self._video_mode_radio, 0)
        self._mode_group.addButton(self._image_mode_radio, 1)
        self._mode_group.buttonClicked.connect(self._on_mode_changed)
        
        mode_layout.addWidget(self._video_mode_radio)
        mode_layout.addWidget(self._image_mode_radio)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Video files section
        self._video_section = QWidget()
        video_layout = QVBoxLayout(self._video_section)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setSpacing(8)
        
        # Video file list
        video_label = QLabel("Selected Video Files:")
        video_layout.addWidget(video_label)
        
        self._video_list = QListWidget()
        self._video_list.setMinimumHeight(100)
        self._video_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._video_list.setStyleSheet("""
            QListWidget {
                background-color: #0f3460;
                border: 1px solid #1a4f7a;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                color: #ccd6f6;
                padding: 4px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #1a4f7a;
            }
        """)
        video_layout.addWidget(self._video_list)
        
        # Video buttons row 1
        vid_btn_row1 = QHBoxLayout()
        
        add_video_btn = QPushButton("+ Add Files")
        add_video_btn.clicked.connect(self._add_video_files)
        vid_btn_row1.addWidget(add_video_btn)
        
        add_video_folder_btn = QPushButton("+ Add Folder")
        add_video_folder_btn.clicked.connect(self._add_video_folder)
        vid_btn_row1.addWidget(add_video_folder_btn)
        
        remove_video_btn = QPushButton("- Remove")
        remove_video_btn.clicked.connect(self._remove_selected_video)
        vid_btn_row1.addWidget(remove_video_btn)
        
        clear_video_btn = QPushButton("Clear All")
        clear_video_btn.clicked.connect(self._clear_video_list)
        vid_btn_row1.addWidget(clear_video_btn)
        
        video_layout.addLayout(vid_btn_row1)
        
        # Video buttons row 2 - shuffle and order
        vid_btn_row2 = QHBoxLayout()
        
        shuffle_video_btn = QPushButton("🔀 Shuffle Order")
        shuffle_video_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #00d4ff;
                border: 1px solid #00d4ff;
            }
            QPushButton:hover {
                background-color: rgba(0, 212, 255, 0.2);
            }
        """)
        shuffle_video_btn.clicked.connect(self._shuffle_video_list)
        vid_btn_row2.addWidget(shuffle_video_btn)
        
        move_video_up_btn = QPushButton("↑ Up")
        move_video_up_btn.clicked.connect(self._move_video_up)
        vid_btn_row2.addWidget(move_video_up_btn)
        
        move_video_down_btn = QPushButton("↓ Down")
        move_video_down_btn.clicked.connect(self._move_video_down)
        vid_btn_row2.addWidget(move_video_down_btn)
        
        video_layout.addLayout(vid_btn_row2)
        
        # Video info
        self._video_info_label = QLabel("No video files selected")
        self._video_info_label.setStyleSheet("color: #8892b0; font-size: 11px;")
        video_layout.addWidget(self._video_info_label)
        
        # Cover video (optional - plays first)
        cover_label = QLabel("Cover Video (Optional - plays first):")
        video_layout.addWidget(cover_label)
        
        cover_row = QHBoxLayout()
        self._cover_edit = QLineEdit()
        self._cover_edit.setPlaceholderText("Optional: Video yang selalu diputar pertama...")
        self._cover_edit.setReadOnly(True)
        cover_row.addWidget(self._cover_edit)
        
        cover_btn = QPushButton("Browse")
        cover_btn.setFixedWidth(70)
        cover_btn.clicked.connect(self._browse_cover_video)
        cover_row.addWidget(cover_btn)
        
        cover_clear_btn = QPushButton("✕")
        cover_clear_btn.setFixedWidth(30)
        cover_clear_btn.clicked.connect(lambda: self._cover_edit.clear())
        cover_row.addWidget(cover_clear_btn)
        video_layout.addLayout(cover_row)
        
        # Video Scale/Zoom section (for watermark removal)
        scale_container = QWidget()
        scale_container.setStyleSheet("""
            QWidget {
                background-color: #1a2332;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        scale_layout = QVBoxLayout(scale_container)
        scale_layout.setSpacing(8)
        
        # Title with icon
        scale_title_layout = QHBoxLayout()
        scale_title = QLabel("🔍 Video Scale/Zoom (Remove Watermark)")
        scale_title.setStyleSheet("font-weight: bold; color: #64ffda; font-size: 13px; border: none; padding: 0;")
        scale_title_layout.addWidget(scale_title)
        scale_title_layout.addStretch()
        scale_layout.addLayout(scale_title_layout)
        
        # Enable checkbox
        self._scale_enabled_checkbox = QCheckBox("Enable video zoom (crops edges to remove watermark)")
        self._scale_enabled_checkbox.setChecked(False)
        self._scale_enabled_checkbox.toggled.connect(self._on_scale_toggle)
        self._scale_enabled_checkbox.setStyleSheet("color: #ccd6f6; border: none; padding: 0;")
        scale_layout.addWidget(self._scale_enabled_checkbox)
        
        # Zoom slider container
        zoom_slider_container = QWidget()
        zoom_slider_layout = QVBoxLayout(zoom_slider_container)
        zoom_slider_layout.setContentsMargins(20, 5, 0, 0)
        zoom_slider_layout.setSpacing(5)
        
        # Slider label and value
        zoom_label_row = QHBoxLayout()
        zoom_label_row.addWidget(QLabel("Zoom Level:"))
        self._scale_percent_label = QLabel("150%")
        self._scale_percent_label.setStyleSheet("color: #666; font-weight: bold; min-width: 50px;")
        zoom_label_row.addWidget(self._scale_percent_label)
        zoom_label_row.addStretch()
        zoom_slider_layout.addLayout(zoom_label_row)
        
        # Slider
        self._scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._scale_slider.setMinimum(100)  # 100% = no zoom
        self._scale_slider.setMaximum(200)  # 200% = 2x zoom
        self._scale_slider.setValue(150)    # 150% default
        self._scale_slider.setEnabled(False)
        self._scale_slider.valueChanged.connect(self._on_scale_changed)
        self._scale_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #0f3460;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #64ffda;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #7fffd4;
            }
            QSlider::handle:horizontal:disabled {
                background: #444;
            }
        """)
        zoom_slider_layout.addWidget(self._scale_slider)
        
        # Visual scale guide
        scale_guide = QLabel("100% ←→ 150% (recommended) ←→ 200%")
        scale_guide.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        zoom_slider_layout.addWidget(scale_guide)
        
        scale_layout.addWidget(zoom_slider_container)
        
        # Info label
        info_label = QLabel("⚠️ Higher zoom = more edges removed = better watermark removal\n"
                           "💡 Works best for watermarks in corners. Applied to ALL videos.")
        info_label.setStyleSheet("color: #888; font-size: 11px; font-style: italic; border: none; padding: 5px 0 0 0;")
        info_label.setWordWrap(True)
        scale_layout.addWidget(info_label)
        
        video_layout.addWidget(scale_container)
        
        # Video Transitions section
        transition_container = QWidget()
        transition_container.setStyleSheet("""
            QWidget {
                background-color: #1a2332;
                border: 1px solid #0f3460;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        transition_layout = QVBoxLayout(transition_container)
        transition_layout.setSpacing(8)
        
        # Title with icon
        transition_title_layout = QHBoxLayout()
        transition_title = QLabel("🎬 Video Transitions")
        transition_title.setStyleSheet("font-weight: bold; color: #64ffda; font-size: 13px; border: none; padding: 0;")
        transition_title_layout.addWidget(transition_title)
        transition_title_layout.addStretch()
        transition_layout.addLayout(transition_title_layout)
        
        # Enable checkbox
        self._transition_enabled_checkbox = QCheckBox("Enable smooth transitions between videos (fade in/out)")
        self._transition_enabled_checkbox.setChecked(False)
        self._transition_enabled_checkbox.toggled.connect(self._on_transition_toggle)
        self._transition_enabled_checkbox.setStyleSheet("color: #ccd6f6; border: none; padding: 0;")
        transition_layout.addWidget(self._transition_enabled_checkbox)
        
        # Settings container
        transition_settings_container = QWidget()
        transition_settings_layout = QVBoxLayout(transition_settings_container)
        transition_settings_layout.setContentsMargins(20, 5, 0, 0)
        transition_settings_layout.setSpacing(8)
        
        # Transition type
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self._transition_type_combo = QComboBox()
        self._transition_type_combo.addItems([
            "fade",
            "fadeblack",
            "fadewhite",
            "wipeleft",
            "wiperight",
            "dissolve"
        ])
        self._transition_type_combo.setCurrentIndex(0)
        self._transition_type_combo.setEnabled(False)
        self._transition_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #0f3460;
                color: #ccd6f6;
                border: 1px solid #1a4f7a;
                border-radius: 3px;
                padding: 3px 8px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #64ffda;
            }
            QComboBox:disabled {
                background-color: #1a1a1a;
                color: #666;
            }
        """)
        type_row.addWidget(self._transition_type_combo)
        type_row.addStretch()
        transition_settings_layout.addLayout(type_row)
        
        # Duration slider
        duration_label_row = QHBoxLayout()
        duration_label_row.addWidget(QLabel("Duration:"))
        self._transition_duration_label = QLabel("1.0s")
        self._transition_duration_label.setStyleSheet("color: #666; font-weight: bold; min-width: 50px;")
        duration_label_row.addWidget(self._transition_duration_label)
        duration_label_row.addStretch()
        transition_settings_layout.addLayout(duration_label_row)
        
        self._transition_duration_slider = QSlider(Qt.Orientation.Horizontal)
        self._transition_duration_slider.setMinimum(5)   # 0.5 seconds
        self._transition_duration_slider.setMaximum(30)  # 3.0 seconds
        self._transition_duration_slider.setValue(10)    # 1.0 second default
        self._transition_duration_slider.setEnabled(False)
        self._transition_duration_slider.valueChanged.connect(self._on_transition_duration_changed)
        self._transition_duration_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #0f3460;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #64ffda;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #7fffd4;
            }
            QSlider::handle:horizontal:disabled {
                background: #444;
            }
        """)
        transition_settings_layout.addWidget(self._transition_duration_slider)
        
        # Guide
        guide_label = QLabel("0.5s ←→ 1.0s (recommended) ←→ 3.0s")
        guide_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        transition_settings_layout.addWidget(guide_label)
        
        transition_layout.addWidget(transition_settings_container)
        
        # Info label
        transition_info = QLabel("💡 Smooth crossfade makes video cuts less abrupt\n"
                                "⚠️ Only applies when you have 2+ videos\n"
                                "⚙️ Note: Encoding with transitions takes longer")
        transition_info.setStyleSheet("color: #888; font-size: 11px; font-style: italic; border: none; padding: 5px 0 0 0;")
        transition_info.setWordWrap(True)
        transition_layout.addWidget(transition_info)
        
        video_layout.addWidget(transition_container)
        
        layout.addWidget(self._video_section)
        
        # Static image section
        self._image_section = QWidget()
        image_layout = QVBoxLayout(self._image_section)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(8)
        
        image_label = QLabel("Static Image:")
        image_layout.addWidget(image_label)
        
        image_row = QHBoxLayout()
        self._image_edit = QLineEdit()
        self._image_edit.setPlaceholderText("Select an image file...")
        self._image_edit.setReadOnly(True)
        image_row.addWidget(self._image_edit)
        
        image_btn = QPushButton("Browse...")
        image_btn.setFixedWidth(100)
        image_btn.clicked.connect(self._browse_static_image)
        image_row.addWidget(image_btn)
        image_layout.addLayout(image_row)
        
        self._image_section.hide()
        layout.addWidget(self._image_section)
        
        return group
    
    def _create_loop_section(self) -> QGroupBox:
        """Create the loop settings section."""
        group = QGroupBox("LOOP SETTINGS")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Loop mode selection
        mode_label = QLabel("Loop Mode:")
        layout.addWidget(mode_label)
        
        self._loop_mode_combo = QComboBox()
        self._loop_mode_combo.addItems([
            "Match Audio Duration",
            "Custom Duration (HH:MM:SS)",
            "Multiply Audio Duration (x times)"
        ])
        self._loop_mode_combo.currentIndexChanged.connect(self._on_loop_mode_changed)
        layout.addWidget(self._loop_mode_combo)
        
        # Custom duration input (hidden by default)
        self._duration_widget = QWidget()
        duration_layout = QHBoxLayout(self._duration_widget)
        duration_layout.setContentsMargins(0, 5, 0, 0)
        
        duration_label = QLabel("Duration:")
        duration_layout.addWidget(duration_label)
        
        self._hours_spin = QSpinBox()
        self._hours_spin.setRange(0, 99)
        self._hours_spin.setSuffix(" h")
        self._hours_spin.valueChanged.connect(self._emit_settings_changed)
        duration_layout.addWidget(self._hours_spin)
        
        self._minutes_spin = QSpinBox()
        self._minutes_spin.setRange(0, 59)
        self._minutes_spin.setSuffix(" m")
        self._minutes_spin.valueChanged.connect(self._emit_settings_changed)
        duration_layout.addWidget(self._minutes_spin)
        
        self._seconds_spin = QSpinBox()
        self._seconds_spin.setRange(0, 59)
        self._seconds_spin.setSuffix(" s")
        self._seconds_spin.valueChanged.connect(self._emit_settings_changed)
        duration_layout.addWidget(self._seconds_spin)
        
        duration_layout.addStretch()
        self._duration_widget.hide()
        layout.addWidget(self._duration_widget)
        
        # Multiplier input (hidden by default)
        self._multiplier_widget = QWidget()
        mult_layout = QHBoxLayout(self._multiplier_widget)
        mult_layout.setContentsMargins(0, 5, 0, 0)
        
        mult_label = QLabel("Multiply by:")
        mult_layout.addWidget(mult_label)
        
        self._multiplier_spin = QSpinBox()
        self._multiplier_spin.setRange(1, 100)
        self._multiplier_spin.setValue(1)
        self._multiplier_spin.setSuffix("x audio length")
        self._multiplier_spin.valueChanged.connect(self._emit_settings_changed)
        mult_layout.addWidget(self._multiplier_spin)
        
        mult_layout.addStretch()
        self._multiplier_widget.hide()
        layout.addWidget(self._multiplier_widget)
        
        return group
    
    def _on_loop_mode_changed(self, index: int) -> None:
        """Handle loop mode change."""
        self._duration_widget.hide()
        self._multiplier_widget.hide()
        
        if index == 1:  # Custom Duration
            self._duration_widget.show()
        elif index == 2:  # Multiply
            self._multiplier_widget.show()
        
        self.settings_changed.emit()
    
    def _on_audio_source_changed(self, index: int) -> None:
        """Handle audio source mode change."""
        if index == 0:  # Audio Directory (Replace)
            self._audio_files_widget.show()
            self._mix_volume_widget.hide()
        elif index == 1:  # Video Original Audio
            self._audio_files_widget.hide()
            self._mix_volume_widget.hide()
        elif index == 2:  # Mix Both
            self._audio_files_widget.show()
            self._mix_volume_widget.show()
        
        self.settings_changed.emit()
    
    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.settings_changed.emit()
    
    def _create_audio_section(self) -> QGroupBox:
        """Create the audio selection section."""
        group = QGroupBox("AUDIO FILES")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Audio source mode selection
        mode_label = QLabel("Audio Source:")
        mode_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        layout.addWidget(mode_label)
        
        self._audio_source_combo = QComboBox()
        self._audio_source_combo.addItems([
            "🎵 Audio Directory (Replace)",
            "🎬 Video Original Audio",
            "🎚️ Mix Both (Video + Music)"
        ])
        self._audio_source_combo.currentIndexChanged.connect(self._on_audio_source_changed)
        self._audio_source_combo.setToolTip(
            "Audio Directory: Use only audio from Audio Files\n"
            "Video Original Audio: Use audio from video files\n"
            "Mix Both: Combine video audio with background music"
        )
        layout.addWidget(self._audio_source_combo)
        
        # Separator
        layout.addSpacing(5)
        
        # Audio file list section (can be hidden for VIDEO_AUDIO mode)
        self._audio_files_widget = QWidget()
        audio_files_layout = QVBoxLayout(self._audio_files_widget)
        audio_files_layout.setContentsMargins(0, 0, 0, 0)
        audio_files_layout.setSpacing(8)
        
        audio_label = QLabel("Selected Audio Files:")
        audio_files_layout.addWidget(audio_label)
        
        self._audio_list = QListWidget()
        self._audio_list.setMinimumHeight(120)
        self._audio_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._audio_list.setStyleSheet("""
            QListWidget {
                background-color: #0f3460;
                border: 1px solid #1a4f7a;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                color: #ccd6f6;
                padding: 5px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #1a4f7a;
            }
        """)
        audio_files_layout.addWidget(self._audio_list)
        
        # Audio buttons row
        btn_row1 = QHBoxLayout()
        
        add_audio_btn = QPushButton("+ Add Files")
        add_audio_btn.clicked.connect(self._add_audio_files)
        btn_row1.addWidget(add_audio_btn)
        
        add_folder_btn = QPushButton("+ Add Folder")
        add_folder_btn.clicked.connect(self._add_audio_folder)
        btn_row1.addWidget(add_folder_btn)
        
        remove_audio_btn = QPushButton("- Remove")
        remove_audio_btn.clicked.connect(self._remove_selected_audio)
        btn_row1.addWidget(remove_audio_btn)
        
        clear_audio_btn = QPushButton("Clear All")
        clear_audio_btn.clicked.connect(self._clear_audio_list)
        btn_row1.addWidget(clear_audio_btn)
        
        audio_files_layout.addLayout(btn_row1)
        
        # Shuffle and order buttons
        btn_row2 = QHBoxLayout()
        
        shuffle_btn = QPushButton("🔀 Shuffle Order")
        shuffle_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #00d4ff;
                border: 1px solid #00d4ff;
            }
            QPushButton:hover {
                background-color: rgba(0, 212, 255, 0.2);
            }
        """)
        shuffle_btn.clicked.connect(self._shuffle_audio_list)
        btn_row2.addWidget(shuffle_btn)
        
        move_up_btn = QPushButton("↑ Up")
        move_up_btn.clicked.connect(self._move_audio_up)
        btn_row2.addWidget(move_up_btn)
        
        move_down_btn = QPushButton("↓ Down")
        move_down_btn.clicked.connect(self._move_audio_down)
        btn_row2.addWidget(move_down_btn)
        
        audio_files_layout.addLayout(btn_row2)
        
        layout.addWidget(self._audio_files_widget)
        
        # Mix volume controls (shown only for MIX_BOTH mode)
        self._mix_volume_widget = QWidget()
        mix_layout = QVBoxLayout(self._mix_volume_widget)
        mix_layout.setContentsMargins(0, 10, 0, 0)
        mix_layout.setSpacing(8)
        
        mix_label = QLabel("Mix Volume Controls:")
        mix_label.setStyleSheet("font-weight: bold;")
        mix_layout.addWidget(mix_label)
        
        # Video audio volume
        video_vol_layout = QHBoxLayout()
        video_vol_label = QLabel("Video Audio:")
        video_vol_layout.addWidget(video_vol_label)
        
        self._video_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._video_volume_slider.setRange(0, 100)
        self._video_volume_slider.setValue(100)
        self._video_volume_slider.valueChanged.connect(self._emit_settings_changed)
        video_vol_layout.addWidget(self._video_volume_slider)
        
        self._video_volume_label = QLabel("100%")
        self._video_volume_label.setFixedWidth(40)
        video_vol_layout.addWidget(self._video_volume_label)
        self._video_volume_slider.valueChanged.connect(
            lambda v: self._video_volume_label.setText(f"{v}%")
        )
        
        mix_layout.addLayout(video_vol_layout)
        
        # Music audio volume
        music_vol_layout = QHBoxLayout()
        music_vol_label = QLabel("Background Music:")
        music_vol_layout.addWidget(music_vol_label)
        
        self._music_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._music_volume_slider.setRange(0, 100)
        self._music_volume_slider.setValue(100)
        self._music_volume_slider.valueChanged.connect(self._emit_settings_changed)
        music_vol_layout.addWidget(self._music_volume_slider)
        
        self._music_volume_label = QLabel("100%")
        self._music_volume_label.setFixedWidth(40)
        music_vol_layout.addWidget(self._music_volume_label)
        self._music_volume_slider.valueChanged.connect(
            lambda v: self._music_volume_label.setText(f"{v}%")
        )
        
        mix_layout.addLayout(music_vol_layout)
        
        self._mix_volume_widget.hide()
        layout.addWidget(self._mix_volume_widget)
        
        # Duration info
        duration_row = QHBoxLayout()
        
        self._duration_label = QLabel("Total Duration: --:--:--")
        self._duration_label.setStyleSheet("color: #00d4ff; font-weight: bold; font-size: 13px;")
        duration_row.addWidget(self._duration_label)
        
        duration_row.addStretch()
        
        calc_btn = QPushButton("Recalculate")
        calc_btn.setFixedWidth(100)
        calc_btn.clicked.connect(self._calculate_duration)
        duration_row.addWidget(calc_btn)
        
        layout.addLayout(duration_row)
        
        # Beat detection section
        beat_header = QHBoxLayout()
        
        detect_beat_btn = QPushButton("🎵 Detect BPM")
        detect_beat_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #ff6b9d;
                border: 1px solid #ff6b9d;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 157, 0.2);
            }
        """)
        detect_beat_btn.clicked.connect(self._detect_beats)
        beat_header.addWidget(detect_beat_btn)
        
        self._bpm_label = QLabel("")
        self._bpm_label.setStyleSheet("color: #ff6b9d; font-weight: bold; font-size: 12px;")
        beat_header.addWidget(self._bpm_label)
        
        beat_header.addStretch()
        layout.addLayout(beat_header)
        
        # Beat sensitivity controls
        sensitivity_row = QHBoxLayout()
        
        sens_label = QLabel("Sensitivity:")
        sens_label.setStyleSheet("color: #8892b0; font-size: 11px;")
        sensitivity_row.addWidget(sens_label)
        
        self._beat_sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self._beat_sensitivity_slider.setRange(0, 100)
        self._beat_sensitivity_slider.setValue(80)  # Default: 80% sensitivity (20% threshold)
        self._beat_sensitivity_slider.setFixedWidth(100)
        self._beat_sensitivity_slider.valueChanged.connect(self._on_beat_sensitivity_changed)
        sensitivity_row.addWidget(self._beat_sensitivity_slider)
        
        self._beat_sensitivity_label = QLabel("80%")
        self._beat_sensitivity_label.setFixedWidth(35)
        self._beat_sensitivity_label.setStyleSheet("color: #ff6b9d; font-size: 11px;")
        sensitivity_row.addWidget(self._beat_sensitivity_label)
        
        # Min interval
        interval_label = QLabel("Min Interval:")
        interval_label.setStyleSheet("color: #8892b0; font-size: 11px;")
        sensitivity_row.addWidget(interval_label)
        
        self._min_interval_spin = QSpinBox()
        self._min_interval_spin.setRange(50, 1000)
        self._min_interval_spin.setValue(200)
        self._min_interval_spin.setSuffix(" ms")
        self._min_interval_spin.setFixedWidth(80)
        sensitivity_row.addWidget(self._min_interval_spin)
        
        sensitivity_row.addStretch()
        layout.addLayout(sensitivity_row)
        
        # Audio info
        self._audio_info_label = QLabel("No audio files selected")
        self._audio_info_label.setStyleSheet("color: #8892b0; font-size: 11px;")
        layout.addWidget(self._audio_info_label)
        
        return group
    
    def _create_audio_layers_section(self) -> QGroupBox:
        """Create the audio layers (multi-layer audio) section."""
        group = QGroupBox("🔊 AUDIO LAYERS (Sound Effects)")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 8px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Info label
        info_label = QLabel("Add multiple sound effects that will be mixed with main audio")
        info_label.setStyleSheet("color: #8892b0; font-size: 11px; font-weight: normal;")
        layout.addWidget(info_label)
        
        # Audio layers list
        self._audio_layers_list = QListWidget()
        self._audio_layers_list.setMaximumHeight(120)
        self._audio_layers_list.setStyleSheet("""
            QListWidget {
                background-color: #0a192f;
                border: 1px solid #233554;
                border-radius: 4px;
                color: #ccd6f6;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #172a45;
            }
            QListWidget::item:selected {
                background-color: #0f3460;
                color: #64ffda;
            }
            QListWidget::item:hover {
                background-color: #172a45;
            }
        """)
        layout.addWidget(self._audio_layers_list)
        
        # Buttons
        btn_row = QHBoxLayout()
        
        add_layer_btn = QPushButton("➕ Add Sound Effect")
        add_layer_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #64ffda;
                border: 1px solid #64ffda;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 255, 218, 0.2);
            }
        """)
        add_layer_btn.clicked.connect(self._add_audio_layer)
        btn_row.addWidget(add_layer_btn)
        
        edit_layer_btn = QPushButton("✏️ Edit")
        edit_layer_btn.clicked.connect(self._edit_audio_layer)
        btn_row.addWidget(edit_layer_btn)
        
        remove_layer_btn = QPushButton("🗑️ Remove")
        remove_layer_btn.clicked.connect(self._remove_audio_layer)
        btn_row.addWidget(remove_layer_btn)
        
        layout.addLayout(btn_row)
        
        return group
    
    def _add_audio_layer(self):
        """Add new audio layer (sound effect)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Sound Effect",
            "",
            "Audio Files (*.mp3 *.wav *.aac *.m4a *.ogg *.flac)"
        )
        
        if not file_path:
            return
        
        # Open dialog to configure layer
        dialog = AudioLayerDialog(self, file_path)
        if dialog.exec() == AudioLayerDialog.Accepted:
            layer_config = dialog.get_config()
            
            # Add to list with visual display
            filename = os.path.basename(file_path)
            loop_text = "🔁 Loop" if layer_config.loop else "▶️ Once"
            vol_text = f"Vol: {int(layer_config.volume * 100)}%"
            
            item_text = f"🎵 {filename} | {loop_text} | {vol_text}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, layer_config)  # Store config
            self._audio_layers_list.addItem(item)
            
            self._emit_settings_changed()
    
    def _edit_audio_layer(self):
        """Edit selected audio layer."""
        current_item = self._audio_layers_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a layer to edit")
            return
        
        layer_config = current_item.data(Qt.UserRole)
        dialog = AudioLayerDialog(self, layer_config.file_path, layer_config)
        
        if dialog.exec() == AudioLayerDialog.Accepted:
            updated_config = dialog.get_config()
            current_item.setData(Qt.UserRole, updated_config)
            
            # Update display text
            filename = os.path.basename(updated_config.file_path)
            loop_text = "🔁 Loop" if updated_config.loop else "▶️ Once"
            vol_text = f"Vol: {int(updated_config.volume * 100)}%"
            current_item.setText(f"🎵 {filename} | {loop_text} | {vol_text}")
            
            self._emit_settings_changed()
    
    def _remove_audio_layer(self):
        """Remove selected audio layer."""
        current_row = self._audio_layers_list.currentRow()
        if current_row >= 0:
            self._audio_layers_list.takeItem(current_row)
            self._emit_settings_changed()
    
    def _on_beat_sensitivity_changed(self, value: int) -> None:
        """Handle beat sensitivity slider change."""
        self._beat_sensitivity_label.setText(f"{value}%")
    
    def _detect_beats(self) -> None:
        """Detect beats and BPM for selected audio files."""
        if not self._audio_files:
            QMessageBox.warning(self, "Warning", "Please add audio files first.")
            return
        
        try:
            from core.beat_detector import BeatDetector, BeatDetectionSettings, LIBROSA_AVAILABLE
            
            if not LIBROSA_AVAILABLE:
                QMessageBox.warning(
                    self, "Library Missing",
                    "librosa is required for beat detection.\n\n"
                    "Install with:\npip install librosa numpy"
                )
                return
            
            detector = BeatDetector()
            
            # Get settings from UI
            # Sensitivity 100% = threshold 0 (detect all), 0% = threshold 1 (detect none)
            sensitivity = self._beat_sensitivity_slider.value()
            threshold = 1.0 - (sensitivity / 100.0)
            min_interval = self._min_interval_spin.value() / 1000.0  # Convert ms to seconds
            
            settings = BeatDetectionSettings(
                onset_threshold=threshold,
                min_beat_interval=min_interval,
                strength_percentile=0  # Use threshold directly
            )
            
            # Analyze all audio files
            results = []
            total_beats = 0
            weighted_tempo = 0.0
            total_duration = 0.0
            
            for filepath in self._audio_files:
                info = detector.analyze(filepath, settings=settings)
                if info:
                    results.append(info)
                    total_beats += info.beat_count
                    weighted_tempo += info.tempo * info.duration
                    total_duration += info.duration
            
            if results:
                # Calculate weighted average tempo
                avg_tempo = weighted_tempo / total_duration if total_duration > 0 else 0
                
                # Get combined beat times
                combined_beats, _ = detector.get_combined_beats(results)
                self._beat_times = combined_beats
                
                # Calculate average beat strength
                all_strengths = []
                for info in results:
                    all_strengths.extend(info.beat_strengths)
                avg_strength = sum(all_strengths) / len(all_strengths) if all_strengths else 0
                
                # Update BPM label
                self._bpm_label.setText(
                    f"⚡ {avg_tempo:.1f} BPM • {len(self._beat_times)} beats"
                )
                
                # Update SFX beat info
                self._sfx_beat_info.setText(
                    f"✓ {len(self._beat_times)} beats detected (avg strength: {avg_strength:.0%})"
                )
                self._sfx_beat_info.setStyleSheet("color: #00ff00; font-size: 11px;")
                
                # Show detailed info
                details = []
                for info in results:
                    filename = os.path.basename(info.filepath)
                    category = detector.get_tempo_category(info.tempo)
                    avg_str = sum(info.beat_strengths) / len(info.beat_strengths) if info.beat_strengths else 0
                    details.append(
                        f"• {filename}: {info.tempo:.1f} BPM, "
                        f"{info.beat_count} beats (strength: {avg_str:.0%})"
                    )
                
                QMessageBox.information(
                    self, "Beat Detection Results",
                    f"Average Tempo: {avg_tempo:.1f} BPM\n"
                    f"Total Beats Detected: {len(self._beat_times)}\n"
                    f"Average Beat Strength: {avg_strength:.0%}\n"
                    f"Total Duration: {AudioUtils.format_duration(total_duration)}\n\n"
                    f"Settings: Sensitivity {sensitivity}%, Min Interval {min_interval*1000:.0f}ms\n\n"
                    + "\n".join(details[:10])
                    + (f"\n... and {len(details) - 10} more" if len(details) > 10 else "")
                )
            else:
                self._bpm_label.setText("Detection failed")
                self._beat_times = []
                QMessageBox.warning(self, "Error", "Could not detect beats in audio files.")
        
        except ImportError:
            QMessageBox.warning(
                self, "Library Missing",
                "librosa is required for beat detection.\n\n"
                "Install with:\npip install librosa numpy"
            )
    
    def _create_sfx_section(self) -> QGroupBox:
        """Create sound effect on beat section."""
        group = QGroupBox("SOUND EFFECT ON BEAT")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # Enable checkbox
        self._sfx_enabled_cb = QCheckBox("Enable Sound Effect on Every Beat")
        self._sfx_enabled_cb.stateChanged.connect(self._on_sfx_enabled_changed)
        layout.addWidget(self._sfx_enabled_cb)
        
        # SFX content (disabled by default)
        self._sfx_content = QWidget()
        sfx_layout = QVBoxLayout(self._sfx_content)
        sfx_layout.setContentsMargins(0, 0, 0, 0)
        sfx_layout.setSpacing(8)
        
        # SFX file selection
        sfx_label = QLabel("Sound Effect File:")
        sfx_layout.addWidget(sfx_label)
        
        sfx_row = QHBoxLayout()
        self._sfx_file_edit = QLineEdit()
        self._sfx_file_edit.setPlaceholderText("Select sound effect (ding, clap, kick, etc.)...")
        self._sfx_file_edit.setReadOnly(True)
        sfx_row.addWidget(self._sfx_file_edit)
        
        sfx_btn = QPushButton("Browse...")
        sfx_btn.setFixedWidth(90)
        sfx_btn.clicked.connect(self._browse_sfx_file)
        sfx_row.addWidget(sfx_btn)
        sfx_layout.addLayout(sfx_row)
        
        # Volume slider
        vol_row = QHBoxLayout()
        vol_label = QLabel("Volume:")
        vol_row.addWidget(vol_label)
        
        self._sfx_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._sfx_volume_slider.setRange(0, 100)
        self._sfx_volume_slider.setValue(50)
        self._sfx_volume_slider.valueChanged.connect(self._on_sfx_volume_changed)
        vol_row.addWidget(self._sfx_volume_slider)
        
        self._sfx_volume_label = QLabel("50%")
        self._sfx_volume_label.setFixedWidth(40)
        vol_row.addWidget(self._sfx_volume_label)
        sfx_layout.addLayout(vol_row)
        
        # Beat info
        self._sfx_beat_info = QLabel("⚠️ Detect beats first using 🎵 Detect BPM button above")
        self._sfx_beat_info.setStyleSheet("color: #ffaa00; font-size: 11px;")
        self._sfx_beat_info.setWordWrap(True)
        sfx_layout.addWidget(self._sfx_beat_info)
        
        # Preview beat times button
        preview_beats_btn = QPushButton("👁 Preview Beat Times")
        preview_beats_btn.clicked.connect(self._preview_beat_times)
        sfx_layout.addWidget(preview_beats_btn)
        
        self._sfx_content.setEnabled(False)
        layout.addWidget(self._sfx_content)
        
        return group
    
    def _on_sfx_enabled_changed(self, state: int) -> None:
        """Handle SFX enabled state change."""
        enabled = state == Qt.CheckState.Checked.value
        self._sfx_content.setEnabled(enabled)
        self.settings_changed.emit()
    
    def _browse_sfx_file(self) -> None:
        """Browse for sound effect file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Sound Effect File", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a)"
        )
        if filepath:
            self._sfx_file = filepath
            self._sfx_file_edit.setText(filepath)
            self.settings_changed.emit()
    
    def _on_sfx_volume_changed(self, value: int) -> None:
        """Handle SFX volume change."""
        self._sfx_volume_label.setText(f"{value}%")
        self.settings_changed.emit()
    
    def _preview_beat_times(self) -> None:
        """Show preview of detected beat times."""
        if not self._beat_times:
            QMessageBox.warning(
                self, "No Beats Detected",
                "Please detect beats first using the 🎵 Detect BPM button."
            )
            return
        
        # Format beat times for display
        beat_count = len(self._beat_times)
        
        # Show first 20 and last 5 beats
        if beat_count <= 25:
            beats_display = self._beat_times
        else:
            beats_display = self._beat_times[:20] + ["..."] + self._beat_times[-5:]
        
        # Format as time strings
        formatted = []
        for i, t in enumerate(beats_display):
            if t == "...":
                formatted.append("...")
            else:
                mins = int(t // 60)
                secs = t % 60
                formatted.append(f"Beat {i+1}: {mins:02d}:{secs:05.2f}")
        
        QMessageBox.information(
            self, f"Beat Times ({beat_count} beats)",
            "Sound effect will play at these times:\n\n" +
            "\n".join(formatted[:30]) +
            (f"\n\n... and {beat_count - 30} more beats" if beat_count > 30 else "")
        )
    
    def _add_audio_files(self) -> None:
        """Add individual audio files."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.mp3 *.wav *.aac *.flac *.ogg *.m4a *.wma)"
        )
        if files:
            for filepath in files:
                if filepath not in self._audio_files:
                    self._audio_files.append(filepath)
                    self._add_audio_to_list(filepath)
            self._update_audio_info()
            self.settings_changed.emit()
    
    def _add_audio_folder(self) -> None:
        """Add all audio files from a folder."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Audio Folder", ""
        )
        if directory:
            audio_files = self._audio_utils.get_directory_audio_files(directory)
            for filepath in audio_files:
                if filepath not in self._audio_files:
                    self._audio_files.append(filepath)
                    self._add_audio_to_list(filepath)
            self._update_audio_info()
            self.settings_changed.emit()
    
    def _add_audio_to_list(self, filepath: str) -> None:
        """Add audio file to the list widget."""
        filename = os.path.basename(filepath)
        duration = self._audio_utils.get_duration(filepath)
        duration_str = AudioUtils.format_duration(duration) if duration else "??:??:??"
        
        item = QListWidgetItem(f"{filename}  [{duration_str}]")
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        item.setToolTip(filepath)
        self._audio_list.addItem(item)
    
    def _remove_selected_audio(self) -> None:
        """Remove selected audio files from list."""
        selected = self._audio_list.selectedItems()
        for item in selected:
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if filepath in self._audio_files:
                self._audio_files.remove(filepath)
            self._audio_list.takeItem(self._audio_list.row(item))
        self._update_audio_info()
        self.settings_changed.emit()
    
    def _clear_audio_list(self) -> None:
        """Clear all audio files."""
        self._audio_files.clear()
        self._audio_list.clear()
        self._update_audio_info()
        self.settings_changed.emit()
    
    def _shuffle_audio_list(self) -> None:
        """Shuffle the audio file order."""
        if len(self._audio_files) < 2:
            return
        
        random.shuffle(self._audio_files)
        self._audio_list.clear()
        for filepath in self._audio_files:
            self._add_audio_to_list(filepath)
        self.settings_changed.emit()
    
    def _move_audio_up(self) -> None:
        """Move selected audio item up."""
        current_row = self._audio_list.currentRow()
        if current_row > 0:
            # Swap in list
            self._audio_files[current_row], self._audio_files[current_row - 1] = \
                self._audio_files[current_row - 1], self._audio_files[current_row]
            # Refresh display
            self._refresh_audio_list()
            self._audio_list.setCurrentRow(current_row - 1)
            self.settings_changed.emit()
    
    def _move_audio_down(self) -> None:
        """Move selected audio item down."""
        current_row = self._audio_list.currentRow()
        if current_row < len(self._audio_files) - 1:
            # Swap in list
            self._audio_files[current_row], self._audio_files[current_row + 1] = \
                self._audio_files[current_row + 1], self._audio_files[current_row]
            # Refresh display
            self._refresh_audio_list()
            self._audio_list.setCurrentRow(current_row + 1)
            self.settings_changed.emit()
    
    def _refresh_audio_list(self) -> None:
        """Refresh the audio list display."""
        self._audio_list.clear()
        for filepath in self._audio_files:
            self._add_audio_to_list(filepath)
    
    def _update_audio_info(self) -> None:
        """Update audio info display."""
        count = len(self._audio_files)
        if count == 0:
            self._audio_info_label.setText("No audio files selected")
            self._duration_label.setText("Total Duration: --:--:--")
        else:
            # Count SRT files
            from pathlib import Path
            srt_count = 0
            for audio_file in self._audio_files:
                srt_path = Path(audio_file).with_suffix('.srt')
                if srt_path.exists():
                    srt_count += 1
            
            # Build info text
            info_text = f"{count} audio file(s) selected"
            if srt_count > 0:
                info_text += f" | {srt_count} file(s) dengan SRT"
            else:
                info_text += " | ⚠ Tidak ada file SRT ditemukan"
            
            self._audio_info_label.setText(info_text)
            self._calculate_duration()
    
    def _browse_audio_dir(self) -> None:
        """Legacy: Browse for audio directory."""
        self._add_audio_folder()
    
    def _on_mode_changed(self, button: QRadioButton) -> None:
        """Handle mode selection change."""
        if button == self._video_mode_radio:
            self._video_section.show()
            self._image_section.hide()
        else:
            self._video_section.hide()
            self._image_section.show()
        
        self.settings_changed.emit()
    
    def _on_scale_toggle(self, checked: bool) -> None:
        """Handle video scale enable/disable."""
        self._scale_slider.setEnabled(checked)
        if checked:
            self._scale_percent_label.setStyleSheet("color: #64ffda; font-weight: bold; min-width: 50px;")
        else:
            self._scale_percent_label.setStyleSheet("color: #666; font-weight: bold; min-width: 50px;")
        self.settings_changed.emit()
    
    def _on_scale_changed(self, value: int) -> None:
        """Handle zoom slider value change."""
        self._scale_percent_label.setText(f"{value}%")
        
        # Visual warning for extreme zoom
        if value >= 180:
            self._scale_percent_label.setStyleSheet("color: #ff6b6b; font-weight: bold; min-width: 50px;")
        elif self._scale_enabled_checkbox.isChecked():
            self._scale_percent_label.setStyleSheet("color: #64ffda; font-weight: bold; min-width: 50px;")
        
        self.settings_changed.emit()
    
    def _on_transition_toggle(self, checked: bool) -> None:
        """Handle transition enable/disable."""
        self._transition_type_combo.setEnabled(checked)
        self._transition_duration_slider.setEnabled(checked)
        if checked:
            self._transition_duration_label.setStyleSheet("color: #64ffda; font-weight: bold; min-width: 50px;")
        else:
            self._transition_duration_label.setStyleSheet("color: #666; font-weight: bold; min-width: 50px;")
        self.settings_changed.emit()
    
    def _on_transition_duration_changed(self, value: int) -> None:
        """Handle transition duration slider change."""
        duration = value / 10.0  # Convert to seconds
        self._transition_duration_label.setText(f"{duration:.1f}s")
        self.settings_changed.emit()
    
    # ==================== VIDEO FILE MANAGEMENT ====================
    
    def _add_video_files(self) -> None:
        """Add individual video files."""
        last_dir = self._settings_manager.settings.last_video_dir or ""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files", last_dir, self.VIDEO_EXTENSIONS
        )
        if files:
            for filepath in files:
                if filepath not in self._video_files:
                    self._video_files.append(filepath)
                    self._add_video_to_list(filepath)
            # Save last directory
            if files:
                self._settings_manager.update(last_video_dir=os.path.dirname(files[0]))
            self._update_video_info()
            self.settings_changed.emit()
    
    def _add_video_folder(self) -> None:
        """Add all video files from a folder."""
        last_dir = self._settings_manager.settings.last_video_dir or ""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Video Folder", last_dir
        )
        if directory:
            self._settings_manager.update(last_video_dir=directory)
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
            for file in sorted(os.listdir(directory)):
                filepath = os.path.join(directory, file)
                if os.path.isfile(filepath) and os.path.splitext(file)[1].lower() in video_extensions:
                    if filepath not in self._video_files:
                        self._video_files.append(filepath)
                        self._add_video_to_list(filepath)
            self._update_video_info()
            self.settings_changed.emit()
    
    def _add_video_to_list(self, filepath: str) -> None:
        """Add video file to the list widget."""
        filename = os.path.basename(filepath)
        duration = self._audio_utils.get_duration(filepath)
        duration_str = AudioUtils.format_duration(duration) if duration else "??:??:??"
        
        item = QListWidgetItem(f"{filename}  [{duration_str}]")
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        item.setToolTip(filepath)
        self._video_list.addItem(item)
        
        # Emit signal for preview (use first video in list)
        if self._video_list.count() > 0:
            first_item = self._video_list.item(0)
            first_filepath = first_item.data(Qt.ItemDataRole.UserRole)
            self.video_selected.emit(first_filepath)
    
    def _remove_selected_video(self) -> None:
        """Remove selected video files from list."""
        selected = self._video_list.selectedItems()
        for item in selected:
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if filepath in self._video_files:
                self._video_files.remove(filepath)
            self._video_list.takeItem(self._video_list.row(item))
        self._update_video_info()
        self.settings_changed.emit()
    
    def _clear_video_list(self) -> None:
        """Clear all video files."""
        self._video_files.clear()
        self._video_list.clear()
        self._update_video_info()
        self.settings_changed.emit()
    
    def _shuffle_video_list(self) -> None:
        """Shuffle the video file order."""
        if len(self._video_files) < 2:
            return
        
        random.shuffle(self._video_files)
        self._video_list.clear()
        for filepath in self._video_files:
            self._add_video_to_list(filepath)
        self.settings_changed.emit()
    
    def _move_video_up(self) -> None:
        """Move selected video item up."""
        current_row = self._video_list.currentRow()
        if current_row > 0:
            self._video_files[current_row], self._video_files[current_row - 1] = \
                self._video_files[current_row - 1], self._video_files[current_row]
            self._refresh_video_list()
            self._video_list.setCurrentRow(current_row - 1)
            self.settings_changed.emit()
    
    def _move_video_down(self) -> None:
        """Move selected video item down."""
        current_row = self._video_list.currentRow()
        if current_row < len(self._video_files) - 1:
            self._video_files[current_row], self._video_files[current_row + 1] = \
                self._video_files[current_row + 1], self._video_files[current_row]
            self._refresh_video_list()
            self._video_list.setCurrentRow(current_row + 1)
            self.settings_changed.emit()
    
    def _refresh_video_list(self) -> None:
        """Refresh the video list display."""
        self._video_list.clear()
        for filepath in self._video_files:
            self._add_video_to_list(filepath)
    
    def _update_video_info(self) -> None:
        """Update video info display."""
        count = len(self._video_files)
        if count == 0:
            self._video_info_label.setText("No video files selected")
        else:
            # Calculate total duration
            total_seconds = 0.0
            for filepath in self._video_files:
                duration = self._audio_utils.get_duration(filepath)
                if duration:
                    total_seconds += duration
            formatted = AudioUtils.format_duration(total_seconds)
            self._video_info_label.setText(f"{count} video file(s) • Total: {formatted}")
    
    def _browse_cover_video(self) -> None:
        """Browse for cover video."""
        last_dir = self._settings_manager.settings.last_video_dir or ""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Video", last_dir,
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm)"
        )
        if filepath:
            self._cover_edit.setText(filepath)
            self.settings_changed.emit()
    
    def _browse_static_image(self) -> None:
        """Browse for static image."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Static Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if filepath:
            self._image_edit.setText(filepath)
            self.settings_changed.emit()
    
    def _browse_audio_dir(self) -> None:
        """Browse for audio directory."""
        last_dir = self._settings_manager.settings.last_audio_dir or ""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Audio Directory", last_dir
        )
        if directory:
            self._audio_dir_edit.setText(directory)
            self._settings_manager.update(last_audio_dir=directory)
            self._update_audio_info(directory)
            self.settings_changed.emit()
    
    def _calculate_duration(self) -> None:
        """Calculate total audio duration."""
        if not self._audio_files:
            self._duration_label.setText("Total Duration: --:--:--")
            return
        
        # Update ffprobe path
        if self._settings_manager.settings.ffprobe_path:
            self._audio_utils.ffprobe_path = self._settings_manager.settings.ffprobe_path
        
        total_seconds = 0.0
        for filepath in self._audio_files:
            duration = self._audio_utils.get_duration(filepath)
            if duration:
                total_seconds += duration
        
        formatted = AudioUtils.format_duration(total_seconds)
        self._duration_label.setText(f"Total Duration: {formatted}")
        self._audio_info_label.setText(
            f"{len(self._audio_files)} audio file(s) • Total: {formatted}"
        )
    
    def get_settings(self) -> dict:
        """
        Get current media panel settings.
        
        Returns:
            Dictionary with current settings.
        """
        if self._video_mode_radio.isChecked():
            mode = MediaMode.VIDEO_DIRECTORY
        else:
            mode = MediaMode.STATIC_IMAGE
        
        # Get loop mode
        loop_mode_index = self._loop_mode_combo.currentIndex()
        if loop_mode_index == 0:
            loop_mode = LoopMode.MATCH_AUDIO
        elif loop_mode_index == 1:
            loop_mode = LoopMode.CUSTOM_DURATION
        else:
            loop_mode = LoopMode.MULTIPLY_AUDIO
        
        # Calculate custom duration in seconds
        custom_duration = (
            self._hours_spin.value() * 3600 +
            self._minutes_spin.value() * 60 +
            self._seconds_spin.value()
        )
        
        # Get audio source mode
        audio_source_index = self._audio_source_combo.currentIndex()
        if audio_source_index == 0:
            audio_source = AudioSource.AUDIO_DIRECTORY
        elif audio_source_index == 1:
            audio_source = AudioSource.VIDEO_AUDIO
        else:
            audio_source = AudioSource.MIX_BOTH
        
        return {
            'mode': mode,
            'video_files': self._video_files.copy(),
            'cover_video': self._cover_edit.text(),
            'static_image': self._image_edit.text(),
            'audio_files': self._audio_files.copy(),
            'audio_source': audio_source,
            'audio_mix_video_volume': self._video_volume_slider.value() / 100.0,
            'audio_mix_music_volume': self._music_volume_slider.value() / 100.0,
            'loop_mode': loop_mode,
            'custom_duration': custom_duration,
            'audio_multiplier': self._multiplier_spin.value(),
            # Audio layers (sound effects)
            'audio_layers': self._get_audio_layers(),
            # Video scale/zoom settings
            'video_scale_enabled': self._scale_enabled_checkbox.isChecked(),
            'video_scale_percent': self._scale_slider.value(),
            # Video transition settings
            'transition_enabled': self._transition_enabled_checkbox.isChecked(),
            'transition_duration': self._transition_duration_slider.value() / 10.0,
            'transition_type': self._transition_type_combo.currentText(),
            # Sound effect settings
            'sfx_enabled': self._sfx_enabled_cb.isChecked(),
            'sfx_file': self._sfx_file,
            'sfx_volume': self._sfx_volume_slider.value() / 100.0,
            'beat_times': self._beat_times.copy(),
        }
    
    def _get_audio_layers(self) -> list:
        """Get all audio layer configurations."""
        layers = []
        for i in range(self._audio_layers_list.count()):
            item = self._audio_layers_list.item(i)
            layer_config = item.data(Qt.UserRole)
            layers.append(layer_config)
        return layers
    
    def set_settings(self, settings: dict) -> None:
        """
        Set media panel settings.
        
        Args:
            settings: Dictionary with settings to apply.
        """
        mode = settings.get('mode', MediaMode.VIDEO_DIRECTORY)
        if mode == MediaMode.VIDEO_DIRECTORY:
            self._video_mode_radio.setChecked(True)
            self._video_section.show()
            self._image_section.hide()
        else:
            self._image_mode_radio.setChecked(True)
            self._video_section.hide()
            self._image_section.show()
        
        # Set video files
        video_files = settings.get('video_files', [])
        self._video_files = video_files.copy()
        self._refresh_video_list()
        self._update_video_info()
        
        self._cover_edit.setText(settings.get('cover_video', ''))
        self._image_edit.setText(settings.get('static_image', ''))
        
        # Set audio files
        audio_files = settings.get('audio_files', [])
        self._audio_files = audio_files.copy()
        self._refresh_audio_list()
        self._update_audio_info()
        
        # Set loop mode
        loop_mode = settings.get('loop_mode', LoopMode.MATCH_AUDIO)
        if loop_mode == LoopMode.MATCH_AUDIO:
            self._loop_mode_combo.setCurrentIndex(0)
        elif loop_mode == LoopMode.CUSTOM_DURATION:
            self._loop_mode_combo.setCurrentIndex(1)
        else:
            self._loop_mode_combo.setCurrentIndex(2)
        
        # Set custom duration
        custom_duration = settings.get('custom_duration', 0)
        self._hours_spin.setValue(int(custom_duration // 3600))
        self._minutes_spin.setValue(int((custom_duration % 3600) // 60))
        self._seconds_spin.setValue(int(custom_duration % 60))
        
        # Set multiplier
        self._multiplier_spin.setValue(settings.get('audio_multiplier', 1))
