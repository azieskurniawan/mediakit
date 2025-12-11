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

from core.media_manager import LogoOverlay, TextOverlay, OverlayPosition


class EffectsPanel(QWidget):
    """Panel for overlay effects settings."""
    
    # Signals
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._logo_overlay = LogoOverlay()
        self._text_overlay = TextOverlay()
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
        
        return {
            'logo_overlay': self._logo_overlay,
            'text_overlay': self._text_overlay,
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
