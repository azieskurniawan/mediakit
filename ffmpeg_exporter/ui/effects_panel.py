"""
Effects Panel - UI for logo and text overlay settings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QSlider, QComboBox, QGroupBox,
    QFileDialog, QCheckBox, QScrollArea, QColorDialog, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.media_manager import LogoOverlay, TextOverlay, AudioVisualizerConfig, SubtitleConfig, OverlayPosition, VisualizerStyle


class EffectsPanel(QWidget):
    """Panel for overlay effects settings."""
    
    # Signals
    settings_changed = Signal()
    preview_requested = Signal()  # Signal when user wants to preview spectrum
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._logo_overlay = LogoOverlay()
        self._text_overlay = TextOverlay()
        self._audio_visualizer = AudioVisualizerConfig()
        self._subtitle_config = SubtitleConfig()
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
        
        # Logo section
        logo_group = self._create_logo_section()
        layout.addWidget(logo_group)
        
        # Text overlay section
        text_group = self._create_text_section()
        layout.addWidget(text_group)
        
        # Audio visualizer section
        viz_group = self._create_visualizer_section()
        layout.addWidget(viz_group)
        
        # Subtitle/Lyrics section
        subtitle_group = self._create_subtitle_section()
        layout.addWidget(subtitle_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _create_logo_section(self) -> QGroupBox:
        """Create the logo overlay section."""
        group = QGroupBox("CUSTOM LOGO")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Enable checkbox
        self._logo_enabled_cb = QCheckBox("Enable Logo Overlay")
        self._logo_enabled_cb.stateChanged.connect(self._on_logo_enabled_changed)
        layout.addWidget(self._logo_enabled_cb)
        
        # Logo content (disabled by default)
        self._logo_content = QWidget()
        logo_layout = QVBoxLayout(self._logo_content)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)
        
        # Logo file selection
        file_label = QLabel("Logo Image:")
        logo_layout.addWidget(file_label)
        
        file_row = QHBoxLayout()
        self._logo_file_edit = QLineEdit()
        self._logo_file_edit.setPlaceholderText("Select logo image (PNG/JPG)...")
        self._logo_file_edit.setReadOnly(True)
        file_row.addWidget(self._logo_file_edit)
        
        file_btn = QPushButton("Browse...")
        file_btn.setFixedWidth(100)
        file_btn.clicked.connect(self._browse_logo)
        file_row.addWidget(file_btn)
        logo_layout.addLayout(file_row)
        
        # Size slider
        size_row = QHBoxLayout()
        size_label = QLabel("Size (%):")
        size_row.addWidget(size_label)
        
        self._logo_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._logo_size_slider.setRange(5, 50)
        self._logo_size_slider.setValue(15)
        self._logo_size_slider.valueChanged.connect(self._on_logo_size_changed)
        size_row.addWidget(self._logo_size_slider)
        
        self._logo_size_value = QLabel("15%")
        self._logo_size_value.setFixedWidth(40)
        size_row.addWidget(self._logo_size_value)
        logo_layout.addLayout(size_row)
        
        # Position selection
        pos_label = QLabel("Position:")
        logo_layout.addWidget(pos_label)
        
        self._logo_position_combo = QComboBox()
        self._logo_position_combo.addItems([
            "Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center", "Custom"
        ])
        self._logo_position_combo.setCurrentIndex(1)  # Top Right
        self._logo_position_combo.currentIndexChanged.connect(self._on_logo_position_changed)
        logo_layout.addWidget(self._logo_position_combo)
        
        # Offset controls
        offset_label = QLabel("Offset:")
        logo_layout.addWidget(offset_label)
        
        offset_row = QHBoxLayout()
        
        x_label = QLabel("X:")
        offset_row.addWidget(x_label)
        self._logo_x_spin = QSpinBox()
        self._logo_x_spin.setRange(0, 500)
        self._logo_x_spin.setValue(20)
        self._logo_x_spin.valueChanged.connect(self._emit_settings_changed)
        offset_row.addWidget(self._logo_x_spin)
        
        y_label = QLabel("Y:")
        offset_row.addWidget(y_label)
        self._logo_y_spin = QSpinBox()
        self._logo_y_spin.setRange(0, 500)
        self._logo_y_spin.setValue(20)
        self._logo_y_spin.valueChanged.connect(self._emit_settings_changed)
        offset_row.addWidget(self._logo_y_spin)
        
        offset_row.addStretch()
        logo_layout.addLayout(offset_row)
        
        self._logo_content.setEnabled(False)
        layout.addWidget(self._logo_content)
        
        return group
    
    def _create_text_section(self) -> QGroupBox:
        """Create the text overlay section."""
        group = QGroupBox("TEXT OVERLAY")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Enable checkbox
        self._text_enabled_cb = QCheckBox("Enable Text Overlay")
        self._text_enabled_cb.stateChanged.connect(self._on_text_enabled_changed)
        layout.addWidget(self._text_enabled_cb)
        
        # Text content (disabled by default)
        self._text_content = QWidget()
        text_layout = QVBoxLayout(self._text_content)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)
        
        # Text input
        text_label = QLabel("Text Content:")
        text_layout.addWidget(text_label)
        
        self._text_edit = QLineEdit()
        self._text_edit.setPlaceholderText("Enter overlay text...")
        self._text_edit.textChanged.connect(self._emit_settings_changed)
        text_layout.addWidget(self._text_edit)
        
        # Font file selection
        font_label = QLabel("Font File (Optional):")
        text_layout.addWidget(font_label)
        
        font_row = QHBoxLayout()
        self._font_file_edit = QLineEdit()
        self._font_file_edit.setPlaceholderText("Select TTF font file (optional)...")
        self._font_file_edit.setReadOnly(True)
        font_row.addWidget(self._font_file_edit)
        
        font_btn = QPushButton("Browse...")
        font_btn.setFixedWidth(100)
        font_btn.clicked.connect(self._browse_font)
        font_row.addWidget(font_btn)
        text_layout.addLayout(font_row)
        
        # Font size
        size_row = QHBoxLayout()
        size_label = QLabel("Font Size:")
        size_row.addWidget(size_label)
        
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 200)
        self._font_size_spin.setValue(48)
        self._font_size_spin.valueChanged.connect(self._emit_settings_changed)
        size_row.addWidget(self._font_size_spin)
        size_row.addStretch()
        text_layout.addLayout(size_row)
        
        # Font color
        color_row = QHBoxLayout()
        color_label = QLabel("Font Color:")
        color_row.addWidget(color_label)
        
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(80, 30)
        self._color_btn.setStyleSheet("background-color: white; border: 1px solid #0f3460;")
        self._color_btn.clicked.connect(self._pick_color)
        self._font_color = "white"
        color_row.addWidget(self._color_btn)
        
        self._color_edit = QLineEdit("white")
        self._color_edit.setFixedWidth(100)
        self._color_edit.textChanged.connect(self._on_color_text_changed)
        color_row.addWidget(self._color_edit)
        
        color_row.addStretch()
        text_layout.addLayout(color_row)
        
        # Position selection
        pos_label = QLabel("Position:")
        text_layout.addWidget(pos_label)
        
        self._text_position_combo = QComboBox()
        self._text_position_combo.addItems([
            "Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center", "Custom"
        ])
        self._text_position_combo.setCurrentIndex(1)  # Top Right
        self._text_position_combo.currentIndexChanged.connect(self._on_text_position_changed)
        text_layout.addWidget(self._text_position_combo)
        
        # Offset controls
        offset_label = QLabel("Offset:")
        text_layout.addWidget(offset_label)
        
        offset_row = QHBoxLayout()
        
        x_label = QLabel("X:")
        offset_row.addWidget(x_label)
        self._text_x_spin = QSpinBox()
        self._text_x_spin.setRange(0, 500)
        self._text_x_spin.setValue(20)
        self._text_x_spin.valueChanged.connect(self._emit_settings_changed)
        offset_row.addWidget(self._text_x_spin)
        
        y_label = QLabel("Y:")
        offset_row.addWidget(y_label)
        self._text_y_spin = QSpinBox()
        self._text_y_spin.setRange(0, 500)
        self._text_y_spin.setValue(20)
        self._text_y_spin.valueChanged.connect(self._emit_settings_changed)
        offset_row.addWidget(self._text_y_spin)
        
        offset_row.addStretch()
        text_layout.addLayout(offset_row)
        
        self._text_content.setEnabled(False)
        layout.addWidget(self._text_content)
        
        return group
    
    def _create_visualizer_section(self) -> QGroupBox:
        """Create the audio visualizer section."""
        group = QGroupBox("AUDIO VISUALIZER")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Enable checkbox
        self._viz_enabled_cb = QCheckBox("Enable Audio Visualizer")
        self._viz_enabled_cb.stateChanged.connect(self._on_viz_enabled_changed)
        layout.addWidget(self._viz_enabled_cb)
        
        # Visualizer content (disabled by default)
        self._viz_content = QWidget()
        viz_layout = QVBoxLayout(self._viz_content)
        viz_layout.setContentsMargins(0, 0, 0, 0)
        viz_layout.setSpacing(8)
        
        # Style selection
        style_label = QLabel("Visualization Style:")
        viz_layout.addWidget(style_label)
        
        self._viz_style_combo = QComboBox()
        self._viz_style_combo.addItems([
            "Custom Bars (BEST! Full Control)",
            "Spectrum Bars (FFmpeg)",
            "Spectrum Line (FFmpeg)",
            "Waveform Line",
            "Waveform Point",
            "Waveform P2P",
            "Spectrogram",
            "Musical CQT",
            "Stereo Scope"
        ])
        self._viz_style_combo.currentIndexChanged.connect(self._emit_settings_changed)
        viz_layout.addWidget(self._viz_style_combo)
        
        # Color picker
        color_row = QHBoxLayout()
        color_label = QLabel("Color:")
        color_row.addWidget(color_label)
        
        self._viz_color_btn = QPushButton()
        self._viz_color_btn.setFixedSize(80, 30)
        self._viz_color_btn.setStyleSheet("background-color: #3b82f6; border: 1px solid #0f3460;")
        self._viz_color_btn.clicked.connect(self._pick_viz_color)
        self._viz_color = "#3b82f6"
        color_row.addWidget(self._viz_color_btn)
        
        self._viz_color_edit = QLineEdit("#3b82f6")
        self._viz_color_edit.setFixedWidth(100)
        self._viz_color_edit.textChanged.connect(self._on_viz_color_changed)
        color_row.addWidget(self._viz_color_edit)
        
        color_row.addStretch()
        viz_layout.addLayout(color_row)
        
        # Min dB slider (note: only works for some styles)
        min_db_label = QLabel("Min dB (optional - not all styles support):")
        min_db_label.setStyleSheet("color: #8892b0; font-size: 11px;")
        viz_layout.addWidget(min_db_label)
        
        min_db_row = QHBoxLayout()
        self._viz_min_db_slider = QSlider(Qt.Orientation.Horizontal)
        self._viz_min_db_slider.setRange(-90, 0)
        self._viz_min_db_slider.setValue(-90)
        self._viz_min_db_slider.valueChanged.connect(self._on_viz_min_db_changed)
        min_db_row.addWidget(self._viz_min_db_slider)
        
        self._viz_min_db_value = QLabel("-90 dB")
        self._viz_min_db_value.setFixedWidth(70)
        min_db_row.addWidget(self._viz_min_db_value)
        viz_layout.addLayout(min_db_row)
        
        # Max dB slider (note: only works for some styles)
        max_db_label = QLabel("Max dB (optional - not all styles support):")
        max_db_label.setStyleSheet("color: #8892b0; font-size: 11px;")
        viz_layout.addWidget(max_db_label)
        
        max_db_row = QHBoxLayout()
        self._viz_max_db_slider = QSlider(Qt.Orientation.Horizontal)
        self._viz_max_db_slider.setRange(0, 200)
        self._viz_max_db_slider.setValue(200)
        self._viz_max_db_slider.valueChanged.connect(self._on_viz_max_db_changed)
        max_db_row.addWidget(self._viz_max_db_slider)
        
        self._viz_max_db_value = QLabel("200 dB")
        self._viz_max_db_value.setFixedWidth(70)
        max_db_row.addWidget(self._viz_max_db_value)
        viz_layout.addLayout(max_db_row)
        
        # Bar count slider (for spectrum styles)
        bar_count_label = QLabel("Bar Count (spectrum styles only):")
        bar_count_label.setStyleSheet("color: #8892b0; font-size: 11px;")
        viz_layout.addWidget(bar_count_label)
        
        bar_count_row = QHBoxLayout()
        self._viz_bar_count_slider = QSlider(Qt.Orientation.Horizontal)
        self._viz_bar_count_slider.setRange(10, 100)
        self._viz_bar_count_slider.setValue(50)
        self._viz_bar_count_slider.valueChanged.connect(self._on_viz_bar_count_changed)
        bar_count_row.addWidget(self._viz_bar_count_slider)
        
        self._viz_bar_count_value = QLabel("50 bars")
        self._viz_bar_count_value.setFixedWidth(70)
        bar_count_row.addWidget(self._viz_bar_count_value)
        viz_layout.addLayout(bar_count_row)
        
        # Size controls
        size_label = QLabel("Size:")
        viz_layout.addWidget(size_label)
        
        size_row = QHBoxLayout()
        
        w_label = QLabel("W:")
        size_row.addWidget(w_label)
        self._viz_width_spin = QSpinBox()
        self._viz_width_spin.setRange(100, 3840)
        self._viz_width_spin.setValue(1920)
        self._viz_width_spin.setSingleStep(10)
        self._viz_width_spin.valueChanged.connect(self._emit_settings_changed)
        size_row.addWidget(self._viz_width_spin)
        
        h_label = QLabel("H:")
        size_row.addWidget(h_label)
        self._viz_height_spin = QSpinBox()
        self._viz_height_spin.setRange(50, 2160)
        self._viz_height_spin.setValue(200)
        self._viz_height_spin.setSingleStep(10)
        self._viz_height_spin.valueChanged.connect(self._emit_settings_changed)
        size_row.addWidget(self._viz_height_spin)
        
        size_row.addStretch()
        viz_layout.addLayout(size_row)
        
        # Position controls (X, Y coordinates)
        pos_label = QLabel("Position (X, Y):")
        viz_layout.addWidget(pos_label)
        
        pos_row = QHBoxLayout()
        
        x_label = QLabel("X:")
        pos_row.addWidget(x_label)
        self._viz_x_spin = QSpinBox()
        self._viz_x_spin.setRange(0, 3840)
        self._viz_x_spin.setValue(0)
        self._viz_x_spin.setSingleStep(10)
        self._viz_x_spin.valueChanged.connect(self._emit_settings_changed)
        pos_row.addWidget(self._viz_x_spin)
        
        y_label = QLabel("Y:")
        pos_row.addWidget(y_label)
        self._viz_y_spin = QSpinBox()
        self._viz_y_spin.setRange(0, 2160)
        self._viz_y_spin.setValue(880)
        self._viz_y_spin.setSingleStep(10)
        self._viz_y_spin.valueChanged.connect(self._emit_settings_changed)
        pos_row.addWidget(self._viz_y_spin)
        
        pos_row.addStretch()
        viz_layout.addLayout(pos_row)
        
        self._viz_content.setEnabled(False)
        layout.addWidget(self._viz_content)
        
        # Preview button
        preview_btn = QPushButton("🔍 Generate Preview (10s)")
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #0a0a14;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00b8e6;
            }
            QPushButton:disabled {
                background-color: #4a5568;
                color: #8892b0;
            }
        """)
        preview_btn.clicked.connect(self._on_preview_requested)
        layout.addWidget(preview_btn)
        
        return group
    
    def _create_subtitle_section(self) -> QGroupBox:
        """Create the subtitle/lyrics section."""
        group = QGroupBox("SUBTITLE / LIRIK (SRT)")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Enable checkbox
        self._subtitle_enabled_cb = QCheckBox("Tampilkan Subtitle/Lirik dari SRT")
        self._subtitle_enabled_cb.setToolTip(
            "Otomatis mencari file SRT dengan nama yang sama dengan audio.\n"
            "Contoh: jika audio = lagu.mp3, akan mencari lagu.srt"
        )
        self._subtitle_enabled_cb.stateChanged.connect(self._on_subtitle_enabled_changed)
        layout.addWidget(self._subtitle_enabled_cb)
        
        # Subtitle content (disabled by default)
        self._subtitle_content = QWidget()
        subtitle_layout = QVBoxLayout(self._subtitle_content)
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.setSpacing(8)
        
        # Info label
        info_label = QLabel("📝 Styling berlaku untuk SEMUA subtitle")
        info_label.setStyleSheet("color: #00d4ff; font-size: 11px; font-style: italic;")
        subtitle_layout.addWidget(info_label)
        
        # Font file selection (optional)
        font_label = QLabel("Font (Opsional):")
        subtitle_layout.addWidget(font_label)
        
        font_row = QHBoxLayout()
        self._subtitle_font_edit = QLineEdit()
        self._subtitle_font_edit.setPlaceholderText("Font default sistem jika kosong...")
        self._subtitle_font_edit.setReadOnly(True)
        font_row.addWidget(self._subtitle_font_edit)
        
        font_btn = QPushButton("Browse...")
        font_btn.setFixedWidth(100)
        font_btn.clicked.connect(self._browse_subtitle_font)
        font_row.addWidget(font_btn)
        subtitle_layout.addLayout(font_row)
        
        # Font size
        size_row = QHBoxLayout()
        size_label = QLabel("Ukuran Font:")
        size_row.addWidget(size_label)
        
        self._subtitle_font_size_spin = QSpinBox()
        self._subtitle_font_size_spin.setRange(12, 80)
        self._subtitle_font_size_spin.setValue(28)
        self._subtitle_font_size_spin.valueChanged.connect(self._emit_settings_changed)
        size_row.addWidget(self._subtitle_font_size_spin)
        size_row.addStretch()
        subtitle_layout.addLayout(size_row)
        
        # Font color
        color_row = QHBoxLayout()
        color_label = QLabel("Warna Teks:")
        color_row.addWidget(color_label)
        
        self._subtitle_color_btn = QPushButton()
        self._subtitle_color_btn.setFixedSize(80, 30)
        self._subtitle_color_btn.setStyleSheet("background-color: white; border: 1px solid #0f3460;")
        self._subtitle_color_btn.clicked.connect(self._pick_subtitle_color)
        self._subtitle_font_color = "white"
        color_row.addWidget(self._subtitle_color_btn)
        
        self._subtitle_color_edit = QLineEdit("white")
        self._subtitle_color_edit.setFixedWidth(100)
        self._subtitle_color_edit.textChanged.connect(self._on_subtitle_color_changed)
        color_row.addWidget(self._subtitle_color_edit)
        
        color_row.addStretch()
        subtitle_layout.addLayout(color_row)
        
        # Outline color
        outline_row = QHBoxLayout()
        outline_label = QLabel("Warna Outline:")
        outline_row.addWidget(outline_label)
        
        self._subtitle_outline_btn = QPushButton()
        self._subtitle_outline_btn.setFixedSize(80, 30)
        self._subtitle_outline_btn.setStyleSheet("background-color: black; border: 1px solid #0f3460;")
        self._subtitle_outline_btn.clicked.connect(self._pick_subtitle_outline)
        self._subtitle_outline_color = "black"
        outline_row.addWidget(self._subtitle_outline_btn)
        
        self._subtitle_outline_edit = QLineEdit("black")
        self._subtitle_outline_edit.setFixedWidth(100)
        self._subtitle_outline_edit.textChanged.connect(self._on_subtitle_outline_changed)
        outline_row.addWidget(self._subtitle_outline_edit)
        
        outline_row.addStretch()
        subtitle_layout.addLayout(outline_row)
        
        # Outline width
        outline_width_row = QHBoxLayout()
        outline_width_label = QLabel("Ketebalan Outline:")
        outline_width_row.addWidget(outline_width_label)
        
        self._subtitle_outline_width_spin = QSpinBox()
        self._subtitle_outline_width_spin.setRange(0, 5)
        self._subtitle_outline_width_spin.setValue(2)
        self._subtitle_outline_width_spin.valueChanged.connect(self._emit_settings_changed)
        outline_width_row.addWidget(self._subtitle_outline_width_spin)
        outline_width_row.addStretch()
        subtitle_layout.addLayout(outline_width_row)
        
        # Position (alignment)
        pos_label = QLabel("Posisi:")
        subtitle_layout.addWidget(pos_label)
        
        self._subtitle_alignment_combo = QComboBox()
        self._subtitle_alignment_combo.addItems([
            "Bottom Center (Default)",
            "Top Center",
            "Center",
            "Bottom Left",
            "Bottom Right"
        ])
        self._subtitle_alignment_combo.setCurrentIndex(0)  # Bottom Center
        self._subtitle_alignment_combo.currentIndexChanged.connect(self._emit_settings_changed)
        subtitle_layout.addWidget(self._subtitle_alignment_combo)
        
        # Margin vertical
        margin_row = QHBoxLayout()
        margin_label = QLabel("Margin Vertikal (px):")
        margin_row.addWidget(margin_label)
        
        self._subtitle_margin_v_spin = QSpinBox()
        self._subtitle_margin_v_spin.setRange(0, 200)
        self._subtitle_margin_v_spin.setValue(60)
        self._subtitle_margin_v_spin.valueChanged.connect(self._emit_settings_changed)
        margin_row.addWidget(self._subtitle_margin_v_spin)
        margin_row.addStretch()
        subtitle_layout.addLayout(margin_row)
        
        # Preview button
        preview_subtitle_btn = QPushButton("👁 Preview Dummy Text")
        preview_subtitle_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #0a0a14;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00b8e6;
            }
            QPushButton:disabled {
                background-color: #4a5568;
                color: #8892b0;
            }
        """)
        preview_subtitle_btn.clicked.connect(self._on_subtitle_preview_requested)
        subtitle_layout.addWidget(preview_subtitle_btn)
        
        self._subtitle_content.setEnabled(False)
        layout.addWidget(self._subtitle_content)
        
        return group
    
    def _on_logo_enabled_changed(self, state: int) -> None:
        """Handle logo enabled state change."""
        enabled = state == Qt.CheckState.Checked.value
        self._logo_content.setEnabled(enabled)
        self._logo_overlay.enabled = enabled
        self.settings_changed.emit()
    
    def _on_text_enabled_changed(self, state: int) -> None:
        """Handle text enabled state change."""
        enabled = state == Qt.CheckState.Checked.value
        self._text_content.setEnabled(enabled)
        self._text_overlay.enabled = enabled
        self.settings_changed.emit()
    
    def _browse_logo(self) -> None:
        """Browse for logo image."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if filepath:
            self._logo_file_edit.setText(filepath)
            self._logo_overlay.filepath = filepath
            self.settings_changed.emit()
    
    def _browse_font(self) -> None:
        """Browse for font file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Font File", "",
            "Font Files (*.ttf *.otf)"
        )
        if filepath:
            self._font_file_edit.setText(filepath)
            self._text_overlay.font_file = filepath
            self.settings_changed.emit()
    
    def _on_logo_size_changed(self, value: int) -> None:
        """Handle logo size slider change."""
        self._logo_size_value.setText(f"{value}%")
        self._logo_overlay.size_percent = value
        self.settings_changed.emit()
    
    def _on_logo_position_changed(self, index: int) -> None:
        """Handle logo position change."""
        positions = [
            OverlayPosition.TOP_LEFT,
            OverlayPosition.TOP_RIGHT,
            OverlayPosition.BOTTOM_LEFT,
            OverlayPosition.BOTTOM_RIGHT,
            OverlayPosition.CENTER,
            OverlayPosition.CUSTOM
        ]
        self._logo_overlay.position = positions[index]
        self.settings_changed.emit()
    
    def _on_text_position_changed(self, index: int) -> None:
        """Handle text position change."""
        positions = [
            OverlayPosition.TOP_LEFT,
            OverlayPosition.TOP_RIGHT,
            OverlayPosition.BOTTOM_LEFT,
            OverlayPosition.BOTTOM_RIGHT,
            OverlayPosition.CENTER,
            OverlayPosition.CUSTOM
        ]
        self._text_overlay.position = positions[index]
        self.settings_changed.emit()
    
    def _pick_color(self) -> None:
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self._font_color), self, "Select Font Color")
        if color.isValid():
            self._font_color = color.name()
            self._color_btn.setStyleSheet(
                f"background-color: {self._font_color}; border: 1px solid #0f3460;"
            )
            self._color_edit.setText(self._font_color)
            self._text_overlay.font_color = self._font_color
            self.settings_changed.emit()
    
    def _on_color_text_changed(self, text: str) -> None:
        """Handle color text input change."""
        self._font_color = text
        self._text_overlay.font_color = text
        try:
            self._color_btn.setStyleSheet(
                f"background-color: {text}; border: 1px solid #0f3460;"
            )
        except:
            pass
        self.settings_changed.emit()
    
    def _on_viz_enabled_changed(self, state: int) -> None:
        """Handle visualizer enabled state change."""
        enabled = state == Qt.CheckState.Checked.value
        self._viz_content.setEnabled(enabled)
        self._audio_visualizer.enabled = enabled
        self.settings_changed.emit()
    
    def _pick_viz_color(self) -> None:
        """Open color picker for visualizer."""
        color = QColorDialog.getColor(QColor(self._viz_color), self, "Select Visualizer Color")
        if color.isValid():
            self._viz_color = color.name()
            self._viz_color_btn.setStyleSheet(
                f"background-color: {self._viz_color}; border: 1px solid #0f3460;"
            )
            self._viz_color_edit.setText(self._viz_color)
            self._audio_visualizer.color = self._viz_color
            self.settings_changed.emit()
    
    def _on_viz_color_changed(self, text: str) -> None:
        """Handle visualizer color text change."""
        self._viz_color = text
        self._audio_visualizer.color = text
        try:
            self._viz_color_btn.setStyleSheet(
                f"background-color: {text}; border: 1px solid #0f3460;"
            )
        except:
            pass
        self.settings_changed.emit()
    
    def _on_viz_min_db_changed(self, value: int) -> None:
        """Handle min dB slider change."""
        self._viz_min_db_value.setText(f"{value} dB")
        self._audio_visualizer.min_db = value
        self.settings_changed.emit()
    
    def _on_viz_max_db_changed(self, value: int) -> None:
        """Handle max dB slider change."""
        self._viz_max_db_value.setText(f"{value} dB")
        self._audio_visualizer.max_db = value
        self.settings_changed.emit()
    
    def _on_viz_bar_count_changed(self, value: int) -> None:
        """Handle bar count slider change."""
        self._viz_bar_count_value.setText(f"{value} bars")
        self._audio_visualizer.bar_count = value
        self.settings_changed.emit()
    
    def _on_preview_requested(self) -> None:
        """Handle preview button click."""
        if self._viz_enabled_cb.isChecked():
            self.preview_requested.emit()
    
    def _on_subtitle_enabled_changed(self, state: int) -> None:
        """Handle subtitle enabled state change."""
        enabled = state == Qt.CheckState.Checked.value
        self._subtitle_content.setEnabled(enabled)
        self._subtitle_config.enabled = enabled
        self.settings_changed.emit()
    
    def _browse_subtitle_font(self) -> None:
        """Browse for subtitle font file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Font File", "",
            "Font Files (*.ttf *.otf)"
        )
        if filepath:
            self._subtitle_font_edit.setText(filepath)
            self._subtitle_config.font_file = filepath
            self.settings_changed.emit()
    
    def _pick_subtitle_color(self) -> None:
        """Open color picker for subtitle text."""
        color = QColorDialog.getColor(QColor(self._subtitle_font_color), self, "Select Subtitle Color")
        if color.isValid():
            self._subtitle_font_color = color.name()
            self._subtitle_color_btn.setStyleSheet(
                f"background-color: {self._subtitle_font_color}; border: 1px solid #0f3460;"
            )
            self._subtitle_color_edit.setText(self._subtitle_font_color)
            self._subtitle_config.font_color = self._subtitle_font_color
            self.settings_changed.emit()
    
    def _on_subtitle_color_changed(self, text: str) -> None:
        """Handle subtitle color text change."""
        self._subtitle_font_color = text
        self._subtitle_config.font_color = text
        try:
            self._subtitle_color_btn.setStyleSheet(
                f"background-color: {text}; border: 1px solid #0f3460;"
            )
        except:
            pass
        self.settings_changed.emit()
    
    def _pick_subtitle_outline(self) -> None:
        """Open color picker for subtitle outline."""
        color = QColorDialog.getColor(QColor(self._subtitle_outline_color), self, "Select Outline Color")
        if color.isValid():
            self._subtitle_outline_color = color.name()
            self._subtitle_outline_btn.setStyleSheet(
                f"background-color: {self._subtitle_outline_color}; border: 1px solid #0f3460;"
            )
            self._subtitle_outline_edit.setText(self._subtitle_outline_color)
            self._subtitle_config.outline_color = self._subtitle_outline_color
            self.settings_changed.emit()
    
    def _on_subtitle_outline_changed(self, text: str) -> None:
        """Handle subtitle outline color text change."""
        self._subtitle_outline_color = text
        self._subtitle_config.outline_color = text
        try:
            self._subtitle_outline_btn.setStyleSheet(
                f"background-color: {text}; border: 1px solid #0f3460;"
            )
        except:
            pass
        self.settings_changed.emit()
    
    def _on_subtitle_preview_requested(self) -> None:
        """Handle subtitle preview button click."""
        from ui.subtitle_preview_dialog import SubtitlePreviewDialog
        
        # Get current subtitle settings
        self._update_subtitle_config_from_ui()
        
        # Show preview dialog
        dialog = SubtitlePreviewDialog(self._subtitle_config, self)
        dialog.exec()
    
    def _update_subtitle_config_from_ui(self) -> None:
        """Update subtitle config from UI values."""
        self._subtitle_config.enabled = self._subtitle_enabled_cb.isChecked()
        self._subtitle_config.font_file = self._subtitle_font_edit.text()
        self._subtitle_config.font_size = self._subtitle_font_size_spin.value()
        self._subtitle_config.font_color = self._subtitle_color_edit.text()
        self._subtitle_config.outline_color = self._subtitle_outline_edit.text()
        self._subtitle_config.outline_width = self._subtitle_outline_width_spin.value()
        self._subtitle_config.margin_v = self._subtitle_margin_v_spin.value()
        
        # Map alignment combo to FFmpeg alignment (1-9)
        alignment_map = [2, 8, 5, 1, 3]  # bottom-center, top-center, center, bottom-left, bottom-right
        self._subtitle_config.alignment = alignment_map[self._subtitle_alignment_combo.currentIndex()]
    
    def _emit_settings_changed(self) -> None:
        """Emit settings changed signal."""
        self.settings_changed.emit()
    
    def get_settings(self) -> dict:
        """
        Get current effects panel settings.
        
        Returns:
            Dictionary with overlay settings.
        """
        # Update logo overlay from UI
        self._logo_overlay.enabled = self._logo_enabled_cb.isChecked()
        self._logo_overlay.filepath = self._logo_file_edit.text()
        self._logo_overlay.size_percent = self._logo_size_slider.value()
        self._logo_overlay.x_offset = self._logo_x_spin.value()
        self._logo_overlay.y_offset = self._logo_y_spin.value()
        
        # Update text overlay from UI
        self._text_overlay.enabled = self._text_enabled_cb.isChecked()
        self._text_overlay.text = self._text_edit.text()
        self._text_overlay.font_file = self._font_file_edit.text()
        self._text_overlay.font_size = self._font_size_spin.value()
        self._text_overlay.font_color = self._color_edit.text()
        self._text_overlay.x_offset = self._text_x_spin.value()
        self._text_overlay.y_offset = self._text_y_spin.value()
        
        # Update audio visualizer from UI
        self._audio_visualizer.enabled = self._viz_enabled_cb.isChecked()
        
        # Map combo index to VisualizerStyle enum
        style_map = [
            VisualizerStyle.CUSTOM_BARS,
            VisualizerStyle.SPECTRUM_BARS,
            VisualizerStyle.SPECTRUM_LINE,
            VisualizerStyle.WAVEFORM_LINE,
            VisualizerStyle.WAVEFORM_POINT,
            VisualizerStyle.WAVEFORM_P2P,
            VisualizerStyle.SPECTROGRAM,
            VisualizerStyle.MUSICAL_CQT,
            VisualizerStyle.STEREO_SCOPE
        ]
        self._audio_visualizer.style = style_map[self._viz_style_combo.currentIndex()]
        self._audio_visualizer.color = self._viz_color_edit.text()
        self._audio_visualizer.min_db = self._viz_min_db_slider.value()
        self._audio_visualizer.max_db = self._viz_max_db_slider.value()
        self._audio_visualizer.bar_count = self._viz_bar_count_slider.value()
        self._audio_visualizer.x_position = self._viz_x_spin.value()
        self._audio_visualizer.y_position = self._viz_y_spin.value()
        self._audio_visualizer.width = self._viz_width_spin.value()
        self._audio_visualizer.height = self._viz_height_spin.value()
        
        # Update subtitle config from UI
        self._update_subtitle_config_from_ui()
        
        return {
            'logo_overlay': self._logo_overlay,
            'text_overlay': self._text_overlay,
            'audio_visualizer': self._audio_visualizer,
            'subtitle_config': self._subtitle_config,
        }
    
    def set_settings(self, settings: dict) -> None:
        """
        Set effects panel settings.
        
        Args:
            settings: Dictionary with settings to apply.
        """
        if 'logo_overlay' in settings:
            logo = settings['logo_overlay']
            self._logo_enabled_cb.setChecked(logo.enabled)
            self._logo_file_edit.setText(logo.filepath)
            self._logo_size_slider.setValue(logo.size_percent)
            self._logo_x_spin.setValue(logo.x_offset)
            self._logo_y_spin.setValue(logo.y_offset)
            self._logo_overlay = logo
        
        if 'text_overlay' in settings:
            text = settings['text_overlay']
            self._text_enabled_cb.setChecked(text.enabled)
            self._text_edit.setText(text.text)
            self._font_file_edit.setText(text.font_file)
            self._font_size_spin.setValue(text.font_size)
            self._color_edit.setText(text.font_color)
            self._text_x_spin.setValue(text.x_offset)
            self._text_y_spin.setValue(text.y_offset)
            self._text_overlay = text
        
        if 'audio_visualizer' in settings:
            viz = settings['audio_visualizer']
            self._viz_enabled_cb.setChecked(viz.enabled)
            
            # Map VisualizerStyle enum to combo index
            style_map = {
                VisualizerStyle.CUSTOM_BARS: 0,
                VisualizerStyle.SPECTRUM_BARS: 1,
                VisualizerStyle.SPECTRUM_LINE: 2,
                VisualizerStyle.WAVEFORM_LINE: 3,
                VisualizerStyle.WAVEFORM_POINT: 4,
                VisualizerStyle.WAVEFORM_P2P: 5,
                VisualizerStyle.SPECTROGRAM: 6,
                VisualizerStyle.MUSICAL_CQT: 7,
                VisualizerStyle.STEREO_SCOPE: 8
            }
            self._viz_style_combo.setCurrentIndex(style_map.get(viz.style, 0))
            self._viz_color_edit.setText(viz.color)
            self._viz_min_db_slider.setValue(viz.min_db)
            self._viz_max_db_slider.setValue(viz.max_db)
            self._viz_bar_count_slider.setValue(viz.bar_count)
            self._viz_x_spin.setValue(viz.x_position)
            self._viz_y_spin.setValue(viz.y_position)
            self._viz_width_spin.setValue(viz.width)
            self._viz_height_spin.setValue(viz.height)
            self._audio_visualizer = viz
        
        if 'subtitle_config' in settings:
            sub = settings['subtitle_config']
            self._subtitle_enabled_cb.setChecked(sub.enabled)
            self._subtitle_font_edit.setText(sub.font_file)
            self._subtitle_font_size_spin.setValue(sub.font_size)
            self._subtitle_color_edit.setText(sub.font_color)
            self._subtitle_outline_edit.setText(sub.outline_color)
            self._subtitle_outline_width_spin.setValue(sub.outline_width)
            self._subtitle_margin_v_spin.setValue(sub.margin_v)
            
            # Map alignment back to combo index
            alignment_reverse_map = {2: 0, 8: 1, 5: 2, 1: 3, 3: 4}
            self._subtitle_alignment_combo.setCurrentIndex(alignment_reverse_map.get(sub.alignment, 0))
            
            self._subtitle_config = sub
