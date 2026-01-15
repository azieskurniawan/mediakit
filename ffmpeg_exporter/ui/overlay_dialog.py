"""
Advanced Overlay Dialog - Blend modes, chroma key, opacity, timing.
"""
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QSlider, QSpinBox, QDoubleSpinBox,
    QComboBox, QGroupBox, QColorDialog, QFrame, QCheckBox, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from core.media_manager import OverlayConfig, OverlayPosition, BlendMode


class ColorPreviewButton(QPushButton):
    """Button that shows current color and opens color picker."""
    
    def __init__(self, initial_color="#00FF00"):
        super().__init__()
        self.current_color = initial_color
        self.setFixedHeight(40)
        self.clicked.connect(self._pick_color)
        self._update_display()
    
    def _pick_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self._update_display()
    
    def _update_display(self):
        """Update button background to show current color."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color};
                border: 2px solid #555;
                border-radius: 4px;
                color: {"white" if self._is_dark(self.current_color) else "black"};
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #888;
            }}
        """)
        self.setText(f"{self.current_color.upper()}")
    
    def _is_dark(self, hex_color):
        """Check if color is dark (for text contrast)."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b)
        return luminance < 128
    
    def get_color(self):
        """Get current color."""
        return self.current_color
    
    def set_color(self, hex_color):
        """Set current color."""
        self.current_color = hex_color
        self._update_display()


class OverlayPreviewFrame(QFrame):
    """Preview frame showing overlay position and size."""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(640, 360)  # 16:9 aspect ratio
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 4px;
            }
        """)
        
        # Overlay preview
        self.overlay_frame = QFrame(self)
        self.overlay_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(59, 130, 246, 0.5);
                border: 2px dashed #3b82f6;
                border-radius: 4px;
            }
        """)
        
        # Label showing size
        self.size_label = QLabel(self.overlay_frame)
        self.size_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        self.size_label.setAlignment(Qt.AlignCenter)
    
    def update_preview(self, size_percent, position, x_offset, y_offset, opacity=1.0):
        """Update preview based on settings."""
        frame_w, frame_h = 640, 360
        
        # Calculate overlay size
        overlay_w = int(frame_w * size_percent / 100)
        overlay_h = int(overlay_w * 0.5625)  # 16:9 aspect
        
        # Calculate position
        if position == OverlayPosition.TOP_LEFT:
            x = int(x_offset * frame_w / 1920)
            y = int(y_offset * frame_h / 1080)
        elif position == OverlayPosition.TOP_RIGHT:
            x = frame_w - overlay_w - int(x_offset * frame_w / 1920)
            y = int(y_offset * frame_h / 1080)
        elif position == OverlayPosition.BOTTOM_LEFT:
            x = int(x_offset * frame_w / 1920)
            y = frame_h - overlay_h - int(y_offset * frame_h / 1080)
        elif position == OverlayPosition.BOTTOM_RIGHT:
            x = frame_w - overlay_w - int(x_offset * frame_w / 1920)
            y = frame_h - overlay_h - int(y_offset * frame_h / 1080)
        elif position == OverlayPosition.CENTER:
            x = (frame_w - overlay_w) // 2
            y = (frame_h - overlay_h) // 2
        else:  # CUSTOM
            x = int(x_offset * frame_w / 1920)
            y = int(y_offset * frame_h / 1080)
        
        # Clamp to frame bounds
        x = max(0, min(x, frame_w - overlay_w))
        y = max(0, min(y, frame_h - overlay_h))
        
        # Update overlay frame with opacity
        self.overlay_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(59, 130, 246, {opacity * 0.5});
                border: 2px dashed #3b82f6;
                border-radius: 4px;
            }}
        """)
        self.overlay_frame.setGeometry(x, y, overlay_w, overlay_h)
        
        # Update size label
        self.size_label.setText(f"{size_percent}%\n{overlay_w}×{overlay_h}px\nOpacity: {int(opacity*100)}%")
        self.size_label.adjustSize()
        self.size_label.move(
            (overlay_w - self.size_label.width()) // 2,
            (overlay_h - self.size_label.height()) // 2
        )


class OverlayDialog(QDialog):
    """Dialog for configuring advanced overlay with blend modes."""
    
    def __init__(self, config: OverlayConfig = None, parent=None):
        super().__init__(parent)
        self.config = config or OverlayConfig()
        self.setWindowTitle("🎨 Advanced Overlay Settings")
        self.resize(1000, 750)
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QHBoxLayout(self)
        
        # Left side: Settings with tabs
        left_widget = QGroupBox("Settings")
        left_layout = QVBoxLayout(left_widget)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_input = QLineEdit(self.config.filepath)
        self.file_input.setPlaceholderText("Select overlay file (image/video)...")
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(QLabel("Overlay File:"))
        file_layout.addWidget(self.file_input, 1)
        file_layout.addWidget(browse_btn)
        left_layout.addLayout(file_layout)
        
        # Tab widget for settings
        tab_widget = QTabWidget()
        
        # === TAB 1: BLEND & OPACITY ===
        blend_tab = QWidget()
        blend_layout = QFormLayout()
        
        # Blend mode dropdown
        self.blend_mode_combo = QComboBox()
        self.blend_mode_combo.addItem("✨ Normal (Default)", BlendMode.NORMAL)
        self.blend_mode_combo.addItem("🌑 Multiply (Darken)", BlendMode.MULTIPLY)
        self.blend_mode_combo.addItem("☀️ Screen (Lighten)", BlendMode.SCREEN)
        self.blend_mode_combo.addItem("🎨 Overlay", BlendMode.OVERLAY)
        self.blend_mode_combo.addItem("⬇️ Darken", BlendMode.DARKEN)
        self.blend_mode_combo.addItem("⬆️ Lighten", BlendMode.LIGHTEN)
        self.blend_mode_combo.addItem("💡 Color Dodge", BlendMode.COLOR_DODGE)
        self.blend_mode_combo.addItem("🔥 Color Burn", BlendMode.COLOR_BURN)
        self.blend_mode_combo.addItem("💎 Hard Light", BlendMode.HARD_LIGHT)
        self.blend_mode_combo.addItem("✨ Soft Light", BlendMode.SOFT_LIGHT)
        self.blend_mode_combo.addItem("🔄 Difference", BlendMode.DIFFERENCE)
        self.blend_mode_combo.addItem("🎯 Exclusion", BlendMode.EXCLUSION)
        self.blend_mode_combo.currentIndexChanged.connect(self._update_preview)
        blend_layout.addRow("Blend Mode:", self.blend_mode_combo)
        
        # Opacity slider
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self.config.opacity * 100))
        self.opacity_slider.valueChanged.connect(self._update_preview)
        self.opacity_label = QLabel(f"{self.config.opacity * 100:.0f}%")
        opacity_layout.addWidget(self.opacity_slider, 1)
        opacity_layout.addWidget(self.opacity_label)
        blend_layout.addRow("Opacity:", opacity_layout)
        
        blend_tab.setLayout(blend_layout)
        tab_widget.addTab(blend_tab, "🎨 Blend & Opacity")
        
        # === TAB 2: CHROMA KEY ===
        chroma_tab = QWidget()
        chroma_layout = QFormLayout()
        
        # Enable chroma key checkbox
        self.chroma_enable_check = QCheckBox("Enable Chroma Key (Green Screen)")
        self.chroma_enable_check.setChecked(self.config.chroma_key_enabled)
        self.chroma_enable_check.toggled.connect(self._toggle_chroma_key)
        chroma_layout.addRow("", self.chroma_enable_check)
        
        # Color picker
        self.color_btn = ColorPreviewButton(self.config.key_color)
        chroma_layout.addRow("Key Color:", self.color_btn)
        
        # Similarity slider
        similarity_layout = QHBoxLayout()
        self.similarity_slider = QSlider(Qt.Horizontal)
        self.similarity_slider.setRange(1, 100)
        self.similarity_slider.setValue(int(self.config.similarity * 100))
        self.similarity_slider.valueChanged.connect(self._update_preview)
        self.similarity_label = QLabel(f"{self.config.similarity:.2f}")
        similarity_layout.addWidget(self.similarity_slider, 1)
        similarity_layout.addWidget(self.similarity_label)
        chroma_layout.addRow("Similarity:", similarity_layout)
        
        # Blend slider
        blend_layout_slider = QHBoxLayout()
        self.blend_slider = QSlider(Qt.Horizontal)
        self.blend_slider.setRange(0, 100)
        self.blend_slider.setValue(int(self.config.blend * 100))
        self.blend_slider.valueChanged.connect(self._update_preview)
        self.blend_label = QLabel(f"{self.config.blend:.2f}")
        blend_layout_slider.addWidget(self.blend_slider, 1)
        blend_layout_slider.addWidget(self.blend_label)
        chroma_layout.addRow("Edge Blend:", blend_layout_slider)
        
        chroma_tab.setLayout(chroma_layout)
        tab_widget.addTab(chroma_tab, "🔑 Chroma Key")
        
        # === TAB 3: TIMING ===
        timing_tab = QWidget()
        timing_layout = QFormLayout()
        
        # Loop checkbox
        self.loop_check = QCheckBox("Loop for entire video duration")
        self.loop_check.setChecked(self.config.loop)
        self.loop_check.toggled.connect(self._toggle_loop)
        timing_layout.addRow("", self.loop_check)
        
        # Start time
        self.start_time_spin = QDoubleSpinBox()
        self.start_time_spin.setRange(0, 9999)
        self.start_time_spin.setValue(self.config.start_time)
        self.start_time_spin.setSuffix(" s")
        self.start_time_spin.setDecimals(1)
        timing_layout.addRow("Start Time:", self.start_time_spin)
        
        # Duration
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0, 9999)
        self.duration_spin.setValue(self.config.duration)
        self.duration_spin.setSuffix(" s (0 = until end)")
        self.duration_spin.setDecimals(1)
        timing_layout.addRow("Duration:", self.duration_spin)
        
        timing_tab.setLayout(timing_layout)
        tab_widget.addTab(timing_tab, "⏱️ Timing")
        
        # === TAB 4: POSITION & SIZE ===
        pos_tab = QWidget()
        pos_layout = QFormLayout()
        
        # Size
        size_layout = QHBoxLayout()
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(5, 100)
        self.size_slider.setValue(self.config.size_percent)
        self.size_slider.valueChanged.connect(self._update_preview)
        self.size_label = QLabel(f"{self.config.size_percent}%")
        size_layout.addWidget(self.size_slider, 1)
        size_layout.addWidget(self.size_label)
        pos_layout.addRow("Size:", size_layout)
        
        # Position preset (3x3 grid)
        self.position_combo = QComboBox()
        # Top row
        self.position_combo.addItem("↖ Top Left", OverlayPosition.TOP_LEFT)
        self.position_combo.addItem("⬆ Top Center", OverlayPosition.TOP_CENTER)
        self.position_combo.addItem("↗ Top Right", OverlayPosition.TOP_RIGHT)
        # Middle row
        self.position_combo.addItem("⬅ Center Left", OverlayPosition.CENTER_LEFT)
        self.position_combo.addItem("⊙ Center", OverlayPosition.CENTER)
        self.position_combo.addItem("➡ Center Right", OverlayPosition.CENTER_RIGHT)
        # Bottom row
        self.position_combo.addItem("↙ Bottom Left", OverlayPosition.BOTTOM_LEFT)
        self.position_combo.addItem("⬇ Bottom Center", OverlayPosition.BOTTOM_CENTER)
        self.position_combo.addItem("↘ Bottom Right", OverlayPosition.BOTTOM_RIGHT)
        # Custom
        self.position_combo.addItem("✎ Custom", OverlayPosition.CUSTOM)
        self.position_combo.currentIndexChanged.connect(self._update_preview)
        pos_layout.addRow("Position:", self.position_combo)
        
        # X offset
        self.x_offset_spin = QSpinBox()
        self.x_offset_spin.setRange(0, 1920)
        self.x_offset_spin.setValue(self.config.x_offset)
        self.x_offset_spin.setSuffix(" px")
        self.x_offset_spin.valueChanged.connect(self._update_preview)
        pos_layout.addRow("X Offset:", self.x_offset_spin)
        
        # Y offset
        self.y_offset_spin = QSpinBox()
        self.y_offset_spin.setRange(0, 1080)
        self.y_offset_spin.setValue(self.config.y_offset)
        self.y_offset_spin.setSuffix(" px")
        self.y_offset_spin.valueChanged.connect(self._update_preview)
        pos_layout.addRow("Y Offset:", self.y_offset_spin)
        
        pos_tab.setLayout(pos_layout)
        tab_widget.addTab(pos_tab, "📍 Position & Size")
        
        left_layout.addWidget(tab_widget)
        
        # Help text
        help_label = QLabel(
            "💡 <b>Tips:</b><br>"
            "• <b>Normal mode + Opacity</b>: Simple transparent overlay<br>"
            "• <b>Multiply</b>: Darken effect (good for adding shadows)<br>"
            "• <b>Screen</b>: Lighten effect (good for light/glow)<br>"
            "• <b>Chroma Key</b>: Remove solid color background<br>"
            "• Combine chroma key + blend mode for best results!"
        )
        help_label.setStyleSheet("padding: 10px; background: #2a2a2a; border-radius: 4px;")
        help_label.setWordWrap(True)
        left_layout.addWidget(help_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        left_layout.addLayout(btn_layout)
        
        # Right side: Preview
        right_widget = QGroupBox("Preview")
        right_layout = QVBoxLayout(right_widget)
        
        self.preview_frame = OverlayPreviewFrame()
        right_layout.addWidget(self.preview_frame, alignment=Qt.AlignCenter)
        
        preview_info = QLabel(
            "🎬 Live preview shows position, size, and opacity\n"
            "Actual blend mode and chroma key applied during export"
        )
        preview_info.setAlignment(Qt.AlignCenter)
        preview_info.setStyleSheet("color: #999; font-size: 11px;")
        right_layout.addWidget(preview_info)
        
        right_layout.addStretch()
        
        # Add to main layout
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 1)
        
        # Initial toggle states
        self._toggle_chroma_key(self.config.chroma_key_enabled)
        self._toggle_loop(self.config.loop)
    
    def _browse_file(self):
        """Browse for overlay file."""
        from PySide6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Overlay File",
            "",
            "Media Files (*.png *.jpg *.jpeg *.gif *.mp4 *.mov *.avi);;All Files (*)"
        )
        if filepath:
            self.file_input.setText(filepath)
    
    def _toggle_chroma_key(self, enabled):
        """Toggle chroma key controls."""
        self.color_btn.setEnabled(enabled)
        self.similarity_slider.setEnabled(enabled)
        self.blend_slider.setEnabled(enabled)
    
    def _toggle_loop(self, loop):
        """Toggle timing controls."""
        self.start_time_spin.setEnabled(not loop)
        self.duration_spin.setEnabled(not loop)
    
    def _load_config(self):
        """Load config into UI."""
        self.file_input.setText(self.config.filepath)
        
        # Blend mode
        for i in range(self.blend_mode_combo.count()):
            if self.blend_mode_combo.itemData(i) == self.config.blend_mode:
                self.blend_mode_combo.setCurrentIndex(i)
                break
        
        self.opacity_slider.setValue(int(self.config.opacity * 100))
        
        # Chroma key
        self.chroma_enable_check.setChecked(self.config.chroma_key_enabled)
        self.color_btn.set_color(self.config.key_color)
        self.similarity_slider.setValue(int(self.config.similarity * 100))
        self.blend_slider.setValue(int(self.config.blend * 100))
        
        # Timing
        self.loop_check.setChecked(self.config.loop)
        self.start_time_spin.setValue(self.config.start_time)
        self.duration_spin.setValue(self.config.duration)
        
        # Position
        self.size_slider.setValue(self.config.size_percent)
        for i in range(self.position_combo.count()):
            if self.position_combo.itemData(i) == self.config.position:
                self.position_combo.setCurrentIndex(i)
                break
        self.x_offset_spin.setValue(self.config.x_offset)
        self.y_offset_spin.setValue(self.config.y_offset)
        
        self._update_preview()
    
    def _update_preview(self):
        """Update preview."""
        # Update labels
        opacity = self.opacity_slider.value() / 100.0
        self.opacity_label.setText(f"{int(opacity * 100)}%")
        
        similarity = self.similarity_slider.value() / 100.0
        self.similarity_label.setText(f"{similarity:.2f}")
        
        blend = self.blend_slider.value() / 100.0
        self.blend_label.setText(f"{blend:.2f}")
        
        size = self.size_slider.value()
        self.size_label.setText(f"{size}%")
        
        # Update preview frame
        position = self.position_combo.currentData()
        self.preview_frame.update_preview(
            size,
            position,
            self.x_offset_spin.value(),
            self.y_offset_spin.value(),
            opacity
        )
    
    def get_config(self) -> OverlayConfig:
        """Get configured settings."""
        return OverlayConfig(
            enabled=True,
            filepath=self.file_input.text(),
            blend_mode=self.blend_mode_combo.currentData(),
            opacity=self.opacity_slider.value() / 100.0,
            chroma_key_enabled=self.chroma_enable_check.isChecked(),
            key_color=self.color_btn.get_color(),
            similarity=self.similarity_slider.value() / 100.0,
            blend=self.blend_slider.value() / 100.0,
            loop=self.loop_check.isChecked(),
            start_time=self.start_time_spin.value(),
            duration=self.duration_spin.value(),
            size_percent=self.size_slider.value(),
            position=self.position_combo.currentData(),
            x_offset=self.x_offset_spin.value(),
            y_offset=self.y_offset_spin.value()
        )


# Legacy alias
ChromaKeyDialog = OverlayDialog
