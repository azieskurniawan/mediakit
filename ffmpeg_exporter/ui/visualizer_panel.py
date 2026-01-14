"""
Visualizer Panel - UI for audio visualizer settings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QDoubleSpinBox, QSlider,
    QCheckBox, QPushButton, QComboBox, QColorDialog,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.media_manager import (
    VisualizerConfig, VisualizerType,
    BarSpectrumConfig, SoundWaveConfig
)


class VisualizerPanel(QWidget):
    """Panel for configuring audio visualizer settings."""
    
    config_changed = Signal()
    preview_requested = Signal()  # Signal for full video preview (60 sec)
    live_play_requested = Signal()  # NEW: Signal for live playback
    
    def __init__(self):
        super().__init__()
        self._config = VisualizerConfig()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for all settings (full width)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Visualizer Type Selector
        type_group = self._create_type_selector()
        content_layout.addWidget(type_group)
        
        # Bar Spectrum Settings
        self._bar_spectrum_widget = self._create_bar_spectrum_ui()
        content_layout.addWidget(self._bar_spectrum_widget)
        
        # Sound Wave Settings
        self._sound_wave_widget = self._create_sound_wave_ui()
        content_layout.addWidget(self._sound_wave_widget)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Initially hide all visualizer widgets
        self._bar_spectrum_widget.hide()
        self._sound_wave_widget.hide()
    
    def _create_type_selector(self) -> QGroupBox:
        """Create visualizer type selector."""
        group = QGroupBox("AUDIO VISUALIZER")
        layout = QVBoxLayout(group)
        
        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "None",
            "Bar Spectrum",
            "Sound Wave"
        ])
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self._type_combo)
        
        # Button layout
        btn_layout = QHBoxLayout()
        
        # Live play button (NEW - real-time playback)
        live_play_btn = QPushButton("▶ LIVE PLAY")
        live_play_btn.setStyleSheet("background-color: #2ecc71; font-weight: bold;")
        live_play_btn.clicked.connect(self.live_play_requested.emit)
        btn_layout.addWidget(live_play_btn)
        
        # Preview button (full 60-second video)
        preview_btn = QPushButton("🎬 Generate 1-Min Video")
        preview_btn.clicked.connect(self.preview_requested.emit)
        btn_layout.addWidget(preview_btn)
        
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_bar_spectrum_ui(self) -> QGroupBox:
        """Create bar spectrum settings UI."""
        widget = QGroupBox("Bar Spectrum Settings")
        layout = QVBoxLayout(widget)
        
        # Max dB
        self._max_db_spin = self._add_slider_row(
            layout, "Max dB", -40, 0, -12
        )
        
        # Min Frequency
        self._min_freq_spin = self._add_slider_row(
            layout, "Min Frequency", 0, 22000, 0
        )
        
        # Max Frequency
        self._max_freq_spin = self._add_slider_row(
            layout, "Max Frequency", 0, 22000, 6000
        )
        
        # Smoothing
        self._smoothing_spin = self._add_double_slider_row(
            layout, "Smoothing", 0.0, 0.99, 0.5
        )
        
        # Normalize toggle
        normalize_row = QHBoxLayout()
        normalize_row.addWidget(QLabel("Normalize"))
        self._normalize_check = QCheckBox()
        self._normalize_check.setChecked(True)  # Astrofox default: True
        self._normalize_check.toggled.connect(self._on_config_changed)
        normalize_row.addWidget(self._normalize_check)
        normalize_row.addStretch()
        layout.addLayout(normalize_row)
        
        # Width
        self._width_spin = self._add_slider_row(
            layout, "Width", 100, 1920, 770
        )
        
        # Height
        self._height_spin = self._add_slider_row(
            layout, "Height", 50, 1080, 240
        )
        
        # Shadow Height
        self._shadow_height_spin = self._add_slider_row(
            layout, "Shadow Height", 0, 500, 100
        )
        
        # Bar Width (with Auto-size toggle)
        bar_width_row = QHBoxLayout()
        bar_width_row.addWidget(QLabel("Bar Width"))
        self._bar_width_auto = QCheckBox("Auto-size")
        self._bar_width_auto.setChecked(True)
        self._bar_width_auto.toggled.connect(self._on_config_changed)
        bar_width_row.addWidget(self._bar_width_auto)
        bar_width_row.addStretch()
        layout.addLayout(bar_width_row)
        
        # Bar Spacing (with Auto-size toggle)
        bar_spacing_row = QHBoxLayout()
        bar_spacing_row.addWidget(QLabel("Bar Spacing"))
        self._bar_spacing_auto = QCheckBox("Auto-size")
        self._bar_spacing_auto.setChecked(True)
        self._bar_spacing_auto.toggled.connect(self._on_config_changed)
        bar_spacing_row.addWidget(self._bar_spacing_auto)
        bar_spacing_row.addStretch()
        layout.addLayout(bar_spacing_row)
        
        # Bar Color (gradient)
        bar_color_row = QHBoxLayout()
        bar_color_row.addWidget(QLabel("Bar Color"))
        self._bar_color_start_btn = self._create_color_button("#FFFFFF")
        self._bar_color_end_btn = self._create_color_button("#FFFFFF")
        bar_color_row.addWidget(self._bar_color_start_btn)
        bar_color_row.addWidget(self._bar_color_end_btn)
        bar_color_row.addStretch()
        layout.addLayout(bar_color_row)
        
        # Shadow Color (gradient)
        shadow_color_row = QHBoxLayout()
        shadow_color_row.addWidget(QLabel("Shadow Color"))
        self._shadow_color_start_btn = self._create_color_button("#333333")
        self._shadow_color_end_btn = self._create_color_button("#000000")
        shadow_color_row.addWidget(self._shadow_color_start_btn)
        shadow_color_row.addWidget(self._shadow_color_end_btn)
        shadow_color_row.addStretch()
        layout.addLayout(shadow_color_row)
        
        # Position controls (X, Y, Rotation, Opacity)
        self._x_spin = self._add_slider_row(
            layout, "X", -1920, 1920, 0
        )
        
        self._y_spin = self._add_slider_row(
            layout, "Y", -1080, 1080, 0
        )
        
        self._rotation_spin = self._add_slider_row(
            layout, "Rotation", 0, 360, 0
        )
        
        self._opacity_spin = self._add_double_slider_row(
            layout, "Opacity", 0.0, 1.0, 1.0
        )
        
        return widget
    
    def _create_sound_wave_ui(self) -> QGroupBox:
        """Create sound wave settings UI."""
        widget = QGroupBox("Sound Wave Settings")
        layout = QVBoxLayout(widget)
        
        # Line Width
        self._wave_line_width_spin = self._add_slider_row(
            layout, "Line Width", 1, 10, 1
        )
        
        # Wavelength
        self._wavelength_spin = self._add_double_slider_row(
            layout, "Wavelength", 0.0, 1.0, 0.0
        )
        
        # Smoothing
        self._wave_smoothing_spin = self._add_double_slider_row(
            layout, "Smoothing", 0.0, 0.99, 0.0
        )
        
        # Stroke toggle
        stroke_row = QHBoxLayout()
        stroke_row.addWidget(QLabel("Stroke"))
        self._stroke_check = QCheckBox()
        self._stroke_check.setChecked(True)
        self._stroke_check.toggled.connect(self._on_config_changed)
        stroke_row.addWidget(self._stroke_check)
        stroke_row.addStretch()
        layout.addLayout(stroke_row)
        
        # Stroke Color
        stroke_color_row = QHBoxLayout()
        stroke_color_row.addWidget(QLabel("Stroke Color"))
        self._stroke_color_btn = self._create_color_button("#FFFFFF")
        stroke_color_row.addWidget(self._stroke_color_btn)
        stroke_color_row.addStretch()
        layout.addLayout(stroke_color_row)
        
        # Fill toggle
        fill_row = QHBoxLayout()
        fill_row.addWidget(QLabel("Fill"))
        self._fill_check = QCheckBox()
        self._fill_check.setChecked(False)
        self._fill_check.toggled.connect(self._on_config_changed)
        fill_row.addWidget(self._fill_check)
        fill_row.addStretch()
        layout.addLayout(fill_row)
        
        # Fill Color
        fill_color_row = QHBoxLayout()
        fill_color_row.addWidget(QLabel("Fill Color"))
        self._fill_color_btn = self._create_color_button("#FFFFFF")
        fill_color_row.addWidget(self._fill_color_btn)
        fill_color_row.addStretch()
        layout.addLayout(fill_color_row)
        
        # Taper Edges
        taper_row = QHBoxLayout()
        taper_row.addWidget(QLabel("Taper Edges"))
        self._taper_check = QCheckBox()
        self._taper_check.setChecked(False)
        self._taper_check.toggled.connect(self._on_config_changed)
        taper_row.addWidget(self._taper_check)
        taper_row.addStretch()
        layout.addLayout(taper_row)
        
        # Width, Height, Position
        self._wave_width_spin = self._add_slider_row(
            layout, "Width", 100, 1920, 854
        )
        
        self._wave_height_spin = self._add_slider_row(
            layout, "Height", 50, 1080, 240
        )
        
        self._wave_x_spin = self._add_slider_row(
            layout, "X", -1920, 1920, 0
        )
        
        self._wave_y_spin = self._add_slider_row(
            layout, "Y", -1080, 1080, 0
        )
        
        self._wave_rotation_spin = self._add_slider_row(
            layout, "Rotation", 0, 360, 0
        )
        
        self._wave_opacity_spin = self._add_double_slider_row(
            layout, "Opacity", 0.0, 1.0, 1.0
        )
        
        return widget
    
    def _add_slider_row(
        self,
        parent_layout: QVBoxLayout,
        label: str,
        min_val: int,
        max_val: int,
        default: int
    ) -> QSpinBox:
        """Add a slider row with spinbox."""
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setMinimumWidth(80)
        spin.valueChanged.connect(self._on_config_changed)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default)
        slider.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(slider.setValue)
        
        row.addWidget(spin)
        row.addWidget(slider)
        
        parent_layout.addLayout(row)
        
        return spin
    
    def _add_double_slider_row(
        self,
        parent_layout: QVBoxLayout,
        label: str,
        min_val: float,
        max_val: float,
        default: float
    ) -> QDoubleSpinBox:
        """Add a double slider row with double spinbox."""
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(0.01)
        spin.setValue(default)
        spin.setMinimumWidth(80)
        spin.valueChanged.connect(self._on_config_changed)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_val * 100), int(max_val * 100))
        slider.setValue(int(default * 100))
        slider.valueChanged.connect(lambda v: spin.setValue(v / 100.0))
        spin.valueChanged.connect(lambda v: slider.setValue(int(v * 100)))
        
        row.addWidget(spin)
        row.addWidget(slider)
        
        parent_layout.addLayout(row)
        
        return spin
    
    def _create_color_button(self, default_color: str) -> QPushButton:
        """Create a color picker button."""
        btn = QPushButton()
        btn.setFixedSize(40, 30)
        btn.setStyleSheet(f"background-color: {default_color}; border: 1px solid #555;")
        btn.clicked.connect(lambda: self._pick_color(btn))
        btn.setProperty("color", default_color)
        return btn
    
    def _pick_color(self, button: QPushButton):
        """Open color picker dialog."""
        current_color = QColor(button.property("color"))
        color = QColorDialog.getColor(current_color, self, "Select Color")
        
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #555;")
            button.setProperty("color", color.name())
            self._on_config_changed()
    
    def _on_type_changed(self, index: int):
        """Handle visualizer type change."""
        # Hide all
        self._bar_spectrum_widget.hide()
        self._sound_wave_widget.hide()
        
        # Show selected
        if index == 1:  # Bar Spectrum
            self._bar_spectrum_widget.show()
        elif index == 2:  # Sound Wave
            self._sound_wave_widget.show()
        
        self.config_changed.emit()
    
    def _on_config_changed(self):
        """Handle config change."""
        self.config_changed.emit()
    
    def get_config(self) -> VisualizerConfig:
        """
        Get current visualizer configuration.
        
        Returns:
            VisualizerConfig object.
        """
        config = VisualizerConfig()
        
        # Type
        type_index = self._type_combo.currentIndex()
        if type_index == 0:
            config.type = VisualizerType.NONE
        elif type_index == 1:
            config.type = VisualizerType.BAR_SPECTRUM
        elif type_index == 2:
            config.type = VisualizerType.SOUND_WAVE
        
        # Bar Spectrum settings
        config.bar_spectrum = BarSpectrumConfig(
            enabled=(config.type == VisualizerType.BAR_SPECTRUM),
            max_db=self._max_db_spin.value(),
            min_frequency=self._min_freq_spin.value(),
            max_frequency=self._max_freq_spin.value(),
            smoothing=self._smoothing_spin.value(),
            normalize=self._normalize_check.isChecked(),
            width=self._width_spin.value(),
            height=self._height_spin.value(),
            shadow_height=self._shadow_height_spin.value(),
            bar_width_auto=self._bar_width_auto.isChecked(),
            bar_spacing_auto=self._bar_spacing_auto.isChecked(),
            bar_color_start=self._bar_color_start_btn.property("color"),
            bar_color_end=self._bar_color_end_btn.property("color"),
            shadow_color_start=self._shadow_color_start_btn.property("color"),
            shadow_color_end=self._shadow_color_end_btn.property("color"),
            x=self._x_spin.value(),
            y=self._y_spin.value(),
            rotation=self._rotation_spin.value(),
            opacity=self._opacity_spin.value()
        )
        
        # Sound Wave settings
        config.sound_wave = SoundWaveConfig(
            enabled=(config.type == VisualizerType.SOUND_WAVE),
            line_width=self._wave_line_width_spin.value(),
            wavelength=self._wavelength_spin.value(),
            smoothing=self._wave_smoothing_spin.value(),
            stroke=self._stroke_check.isChecked(),
            stroke_color=self._stroke_color_btn.property("color"),
            fill=self._fill_check.isChecked(),
            fill_color=self._fill_color_btn.property("color"),
            taper_edges=self._taper_check.isChecked(),
            width=self._wave_width_spin.value(),
            height=self._wave_height_spin.value(),
            x=self._wave_x_spin.value(),
            y=self._wave_y_spin.value(),
            rotation=self._wave_rotation_spin.value(),
            opacity=self._wave_opacity_spin.value()
        )
        
        return config
    
    def set_config(self, config: VisualizerConfig):
        """
        Set visualizer configuration.
        
        Args:
            config: VisualizerConfig object.
        """
        self._config = config
        
        # Set type
        if config.type == VisualizerType.NONE:
            self._type_combo.setCurrentIndex(0)
        elif config.type == VisualizerType.BAR_SPECTRUM:
            self._type_combo.setCurrentIndex(1)
        elif config.type == VisualizerType.SOUND_WAVE:
            self._type_combo.setCurrentIndex(2)
        
        # Set bar spectrum settings
        bar = config.bar_spectrum
        self._max_db_spin.setValue(bar.max_db)
        self._min_freq_spin.setValue(bar.min_frequency)
        self._max_freq_spin.setValue(bar.max_frequency)
        self._smoothing_spin.setValue(bar.smoothing)
        self._normalize_check.setChecked(bar.normalize)
        self._width_spin.setValue(bar.width)
        self._height_spin.setValue(bar.height)
        self._shadow_height_spin.setValue(bar.shadow_height)
        self._bar_width_auto.setChecked(bar.bar_width_auto)
        self._bar_spacing_auto.setChecked(bar.bar_spacing_auto)
        
        self._bar_color_start_btn.setProperty("color", bar.bar_color_start)
        self._bar_color_start_btn.setStyleSheet(f"background-color: {bar.bar_color_start}; border: 1px solid #555;")
        
        self._bar_color_end_btn.setProperty("color", bar.bar_color_end)
        self._bar_color_end_btn.setStyleSheet(f"background-color: {bar.bar_color_end}; border: 1px solid #555;")
        
        self._shadow_color_start_btn.setProperty("color", bar.shadow_color_start)
        self._shadow_color_start_btn.setStyleSheet(f"background-color: {bar.shadow_color_start}; border: 1px solid #555;")
        
        self._shadow_color_end_btn.setProperty("color", bar.shadow_color_end)
        self._shadow_color_end_btn.setStyleSheet(f"background-color: {bar.shadow_color_end}; border: 1px solid #555;")
        
        self._x_spin.setValue(bar.x)
        self._y_spin.setValue(bar.y)
        self._rotation_spin.setValue(bar.rotation)
        self._opacity_spin.setValue(bar.opacity)
        
        # Set sound wave settings
        wave = config.sound_wave
        self._wave_line_width_spin.setValue(wave.line_width)
        self._wavelength_spin.setValue(wave.wavelength)
        self._wave_smoothing_spin.setValue(wave.smoothing)
        self._stroke_check.setChecked(wave.stroke)
        
        self._stroke_color_btn.setProperty("color", wave.stroke_color)
        self._stroke_color_btn.setStyleSheet(f"background-color: {wave.stroke_color}; border: 1px solid #555;")
        
        self._fill_check.setChecked(wave.fill)
        
        self._fill_color_btn.setProperty("color", wave.fill_color)
        self._fill_color_btn.setStyleSheet(f"background-color: {wave.fill_color}; border: 1px solid #555;")
        
        self._taper_check.setChecked(wave.taper_edges)
        self._wave_width_spin.setValue(wave.width)
        self._wave_height_spin.setValue(wave.height)
        self._wave_x_spin.setValue(wave.x)
        self._wave_y_spin.setValue(wave.y)
        self._wave_rotation_spin.setValue(wave.rotation)
        self._wave_opacity_spin.setValue(wave.opacity)

