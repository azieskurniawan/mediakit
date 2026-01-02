"""
Dialog for configuring animated text item with visual preview.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSlider, QCheckBox,
    QDoubleSpinBox, QGroupBox, QTextEdit, QComboBox,
    QSpinBox, QFileDialog, QMessageBox, QInputDialog, QFrame
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from core.media_manager import AnimatedTextItem, OverlayPosition
from ui.font_selector import FontSelector


class TextPreviewFrame(QFrame):
    """Visual preview frame for text positioning and styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 360)  # 16:9 aspect ratio preview
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #64ffda;
                border-radius: 5px;
            }
        """)
        
        # Preview text properties
        self.preview_text = "Sample Text"
        self.font_size = 48
        self.font_color = QColor("white")
        self.position = OverlayPosition.CENTER
        self.x_offset = 0
        self.y_offset = 0
        self.shadow = True
        self.box = False
        self.font_family = "Arial"
    
    def update_preview(self, text: str, font_size: int, color: str, 
                       position: OverlayPosition, x_offset: int, y_offset: int,
                       shadow: bool, box: bool, font_family: str = "Arial"):
        """Update preview properties."""
        self.preview_text = text if text else "Sample Text"
        self.font_size = font_size
        self.font_color = QColor(color)
        self.position = position
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.shadow = shadow
        self.box = box
        self.font_family = font_family
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Paint the preview frame."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Draw video dimensions guide
        painter.setPen(QPen(QColor("#2a2a2a"), 1))
        for i in range(0, self.width(), 64):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 36):
            painter.drawLine(0, i, self.width(), i)
        
        # Draw center guides
        painter.setPen(QPen(QColor("#64ffda"), 1, Qt.DashLine))
        painter.drawLine(self.width() // 2, 0, self.width() // 2, self.height())
        painter.drawLine(0, self.height() // 2, self.width(), self.height() // 2)
        
        # Setup font
        font = QFont(self.font_family)
        font.setPixelSize(self.font_size)
        font.setBold(True)
        painter.setFont(font)
        
        # Calculate text metrics
        font_metrics = painter.fontMetrics()
        text_rect = font_metrics.boundingRect(self.preview_text)
        text_width = text_rect.width()
        text_height = text_rect.height()
        
        # Calculate position
        x, y = self._calculate_position(text_width, text_height)
        
        # Draw box if enabled
        if self.box:
            box_padding = 10
            box_rect = QRect(x - box_padding, y - text_height - box_padding,
                           text_width + 2 * box_padding, text_height + 2 * box_padding)
            painter.fillRect(box_rect, QColor(0, 0, 0, 128))
        
        # Draw shadow if enabled
        if self.shadow:
            painter.setPen(QColor(0, 0, 0, 128))
            painter.drawText(x + 2, y + 2, self.preview_text)
        
        # Draw main text
        painter.setPen(self.font_color)
        painter.drawText(x, y, self.preview_text)
        
        # Draw position indicator
        painter.setPen(QPen(QColor("#ffd700"), 2))
        painter.drawEllipse(x - 5, y - text_height - 5, 10, 10)
        
        # Draw dimension label
        painter.setPen(QColor("#8892b0"))
        painter.setFont(QFont("Arial", 10))
        dim_text = f"{self.width()}x{self.height()} preview | Text: {text_width}x{text_height}px"
        painter.drawText(10, 20, dim_text)
    
    def _calculate_position(self, text_width: int, text_height: int) -> tuple:
        """Calculate text position based on preset and offsets."""
        w = self.width()
        h = self.height()
        
        if self.position == OverlayPosition.TOP_LEFT:
            return (self.x_offset, self.y_offset + text_height)
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (w - text_width - self.x_offset, self.y_offset + text_height)
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (self.x_offset, h - self.y_offset)
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (w - text_width - self.x_offset, h - self.y_offset)
        elif self.position == OverlayPosition.CENTER:
            return ((w - text_width) // 2 + self.x_offset, 
                   (h + text_height) // 2 + self.y_offset)
        else:  # CUSTOM
            return (self.x_offset, self.y_offset + text_height)


class AnimatedTextDialog(QDialog):
    """Dialog for editing animated text item with live preview."""
    
    def __init__(self, parent=None, existing_config: AnimatedTextItem = None):
        super().__init__(parent)
        self.setWindowTitle("Configure Animated Text")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        main_layout = QHBoxLayout(self)
        
        # === LEFT SIDE: Settings ===
        settings_widget = QFrame()
        settings_widget.setMaximumWidth(400)
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setSpacing(10)
        
        # TEXT CONTENT
        content_group = QGroupBox("📝 Text Content")
        content_group.setStyleSheet(self._get_group_style())
        content_layout = QVBoxLayout()
        
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Enter your text here...")
        self._text_edit.setMaximumHeight(80)
        if existing_config:
            self._text_edit.setPlainText(existing_config.text)
        self._text_edit.textChanged.connect(self._update_preview)
        content_layout.addWidget(self._text_edit)
        
        content_group.setLayout(content_layout)
        settings_layout.addWidget(content_group)
        
        # TIMELINE
        timeline_group = QGroupBox("⏱️ Timeline")
        timeline_group.setStyleSheet(self._get_group_style())
        timeline_layout = QVBoxLayout()
        
        # Start time
        start_row = QHBoxLayout()
        start_row.addWidget(QLabel("Start Time:"))
        self._start_time_spin = QDoubleSpinBox()
        self._start_time_spin.setRange(0, 36000)
        self._start_time_spin.setValue(existing_config.start_time if existing_config else 0)
        self._start_time_spin.setSuffix(" sec")
        self._start_time_spin.setDecimals(1)
        start_row.addWidget(self._start_time_spin)
        convert_btn = QPushButton("⏰")
        convert_btn.setToolTip("Convert MM:SS")
        convert_btn.setMaximumWidth(35)
        convert_btn.clicked.connect(self._show_time_converter)
        start_row.addWidget(convert_btn)
        timeline_layout.addLayout(start_row)
        
        # Duration
        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Duration:"))
        self._duration_spin = QDoubleSpinBox()
        self._duration_spin.setRange(0.5, 300)
        self._duration_spin.setValue(existing_config.duration if existing_config else 5.0)
        self._duration_spin.setSuffix(" sec")
        self._duration_spin.setDecimals(1)
        dur_row.addWidget(self._duration_spin)
        timeline_layout.addLayout(dur_row)
        
        # Fade in/out
        fade_row = QHBoxLayout()
        fade_row.addWidget(QLabel("Fade In:"))
        self._fade_in_spin = QDoubleSpinBox()
        self._fade_in_spin.setRange(0, 10)
        self._fade_in_spin.setValue(existing_config.fade_in if existing_config else 1.0)
        self._fade_in_spin.setSuffix(" s")
        self._fade_in_spin.setDecimals(2)
        self._fade_in_spin.setMaximumWidth(90)
        fade_row.addWidget(self._fade_in_spin)
        
        fade_row.addWidget(QLabel("Fade Out:"))
        self._fade_out_spin = QDoubleSpinBox()
        self._fade_out_spin.setRange(0, 10)
        self._fade_out_spin.setValue(existing_config.fade_out if existing_config else 1.0)
        self._fade_out_spin.setSuffix(" s")
        self._fade_out_spin.setDecimals(2)
        self._fade_out_spin.setMaximumWidth(90)
        fade_row.addWidget(self._fade_out_spin)
        timeline_layout.addLayout(fade_row)
        
        timeline_group.setLayout(timeline_layout)
        settings_layout.addWidget(timeline_group)
        
        # STYLING
        style_group = QGroupBox("🎨 Styling")
        style_group.setStyleSheet(self._get_group_style())
        style_layout = QVBoxLayout()
        
        # Font size
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Font Size:"))
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(12, 200)
        self._font_size_spin.setValue(existing_config.font_size if existing_config else 48)
        self._font_size_spin.valueChanged.connect(self._update_preview)
        size_row.addWidget(self._font_size_spin)
        style_layout.addLayout(size_row)
        
        # Max Width (text wrapping)
        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Max Width (0=no wrap):"))
        self._max_width_spin = QSpinBox()
        self._max_width_spin.setRange(0, 3840)
        self._max_width_spin.setSingleStep(50)
        self._max_width_spin.setValue(existing_config.max_width if existing_config else 0)
        self._max_width_spin.setToolTip("Text akan wrap otomatis jika melebihi lebar ini (px)")
        width_row.addWidget(self._max_width_spin)
        style_layout.addLayout(width_row)
        
        # Font color
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self._font_color_combo = QComboBox()
        self._font_color_combo.addItems([
            "white", "black", "red", "green", "blue", 
            "yellow", "cyan", "magenta", "orange", "lime", "pink"
        ])
        if existing_config:
            index = self._font_color_combo.findText(existing_config.font_color)
            if index >= 0:
                self._font_color_combo.setCurrentIndex(index)
        self._font_color_combo.currentTextChanged.connect(self._update_preview)
        color_row.addWidget(self._font_color_combo)
        style_layout.addLayout(color_row)
        
        # Font selector with preview
        font_label = QLabel("Font:")
        style_layout.addWidget(font_label)
        self._font_selector = FontSelector()
        if existing_config and existing_config.font_file:
            self._font_selector.set_font_path(existing_config.font_file)
        self._font_selector.fontChanged.connect(self._update_preview)
        style_layout.addWidget(self._font_selector)
        
        # Effects
        self._shadow_checkbox = QCheckBox("✨ Enable Shadow")
        self._shadow_checkbox.setChecked(existing_config.shadow if existing_config else True)
        self._shadow_checkbox.toggled.connect(self._update_preview)
        style_layout.addWidget(self._shadow_checkbox)
        
        self._box_checkbox = QCheckBox("📦 Background Box")
        self._box_checkbox.setChecked(existing_config.box if existing_config else False)
        self._box_checkbox.toggled.connect(self._update_preview)
        style_layout.addWidget(self._box_checkbox)
        
        style_group.setLayout(style_layout)
        settings_layout.addWidget(style_group)
        
        # POSITION
        position_group = QGroupBox("📍 Position")
        position_group.setStyleSheet(self._get_group_style())
        position_layout = QVBoxLayout()
        
        pos_combo_row = QHBoxLayout()
        pos_combo_row.addWidget(QLabel("Preset:"))
        self._position_combo = QComboBox()
        for pos in OverlayPosition:
            self._position_combo.addItem(pos.value, pos)
        if existing_config:
            for i in range(self._position_combo.count()):
                if self._position_combo.itemData(i) == existing_config.position:
                    self._position_combo.setCurrentIndex(i)
                    break
        self._position_combo.currentIndexChanged.connect(self._update_preview)
        pos_combo_row.addWidget(self._position_combo)
        position_layout.addLayout(pos_combo_row)
        
        offset_row = QHBoxLayout()
        offset_row.addWidget(QLabel("X:"))
        self._x_offset_spin = QSpinBox()
        self._x_offset_spin.setRange(-1000, 2000)
        self._x_offset_spin.setValue(existing_config.x_offset if existing_config else 0)
        self._x_offset_spin.valueChanged.connect(self._update_preview)
        offset_row.addWidget(self._x_offset_spin)
        
        offset_row.addWidget(QLabel("Y:"))
        self._y_offset_spin = QSpinBox()
        self._y_offset_spin.setRange(-1000, 2000)
        self._y_offset_spin.setValue(existing_config.y_offset if existing_config else 0)
        self._y_offset_spin.valueChanged.connect(self._update_preview)
        offset_row.addWidget(self._y_offset_spin)
        position_layout.addLayout(offset_row)
        
        position_group.setLayout(position_layout)
        settings_layout.addWidget(position_group)
        
        settings_layout.addStretch()
        
        # BUTTONS
        btn_row = QHBoxLayout()
        ok_btn = QPushButton("✅ OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #64ffda;
                border: 1px solid #64ffda;
                padding: 10px 25px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(100, 255, 218, 0.2);
            }
        """)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_row.addWidget(ok_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        settings_layout.addLayout(btn_row)
        
        main_layout.addWidget(settings_widget)
        
        # === RIGHT SIDE: Preview ===
        preview_widget = QFrame()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_title = QLabel("🎬 Live Preview")
        preview_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #64ffda;
                padding: 5px;
            }
        """)
        preview_layout.addWidget(preview_title)
        
        self._preview_frame = TextPreviewFrame()
        preview_layout.addWidget(self._preview_frame)
        
        preview_info = QLabel(
            "💡 Tip: This is a 16:9 preview. Drag sliders to see text position in real-time!"
        )
        preview_info.setStyleSheet("color: #8892b0; font-size: 11px; padding: 5px;")
        preview_info.setWordWrap(True)
        preview_layout.addWidget(preview_info)
        
        main_layout.addWidget(preview_widget)
        
        # Initial preview update
        self._update_preview()
    
    def _get_group_style(self) -> str:
        """Get consistent group box style."""
        return """
            QGroupBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
                margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
    
    def _update_preview(self):
        """Update live preview frame."""
        text = self._text_edit.toPlainText()
        font_size = self._font_size_spin.value()
        color = self._font_color_combo.currentText()
        position = self._position_combo.currentData()
        x_offset = self._x_offset_spin.value()
        y_offset = self._y_offset_spin.value()
        shadow = self._shadow_checkbox.isChecked()
        box = self._box_checkbox.isChecked()
        
        # Get font family from selector
        font_family = "Arial"
        current_font = self._font_selector._font_combo.currentText()
        if current_font and not current_font.startswith("🎨"):
            font_family = current_font.replace("📁 ", "")
        
        self._preview_frame.update_preview(
            text, font_size, color, position, x_offset, y_offset,
            shadow, box, font_family
        )
    
    
    def _show_time_converter(self):
        """Show time converter dialog."""
        time_str, ok = QInputDialog.getText(
            self,
            "Time Converter",
            "Enter time (MM:SS or HH:MM:SS):"
        )
        if ok and time_str:
            try:
                parts = time_str.split(':')
                if len(parts) == 2:  # MM:SS
                    minutes, seconds = map(float, parts)
                    total_seconds = minutes * 60 + seconds
                elif len(parts) == 3:  # HH:MM:SS
                    hours, minutes, seconds = map(float, parts)
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                else:
                    raise ValueError("Invalid format")
                
                self._start_time_spin.setValue(total_seconds)
            except:
                QMessageBox.warning(self, "Invalid Format", "Please use MM:SS or HH:MM:SS format")
    
    def get_config(self) -> AnimatedTextItem:
        """Get configured text item."""
        return AnimatedTextItem(
            text=self._text_edit.toPlainText(),
            start_time=self._start_time_spin.value(),
            duration=self._duration_spin.value(),
            fade_in=self._fade_in_spin.value(),
            fade_out=self._fade_out_spin.value(),
            font_file=self._font_selector.get_font_path(),  # Use font selector
            font_size=self._font_size_spin.value(),
            font_color=self._font_color_combo.currentText(),
            position=self._position_combo.currentData(),
            x_offset=self._x_offset_spin.value(),
            y_offset=self._y_offset_spin.value(),
            shadow=self._shadow_checkbox.isChecked(),
            box=self._box_checkbox.isChecked(),
            max_width=self._max_width_spin.value(),
            enabled=True
        )

