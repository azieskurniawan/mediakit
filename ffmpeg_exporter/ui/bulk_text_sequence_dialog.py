"""
Dialog for bulk text sequence creation with auto-loop.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QTextEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QFileDialog,
    QLineEdit, QFrame, QWidget
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from core.media_manager import AnimatedTextItem, OverlayPosition
from ui.font_selector import FontSelector


class BulkPreviewFrame(QFrame):
    """Compact preview frame for bulk text sequence."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 225)  # 16:9 aspect ratio, smaller
        self.setMaximumHeight(250)
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #64ffda;
                border-radius: 5px;
            }
        """)
        
        # Preview properties
        self.preview_text = "Sample Text (First Line)"
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
        self.update()
    
    def paintEvent(self, event):
        """Paint the preview frame."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Center guides
        painter.setPen(QPen(QColor("#2a2a2a"), 1, Qt.DashLine))
        painter.drawLine(self.width() // 2, 0, self.width() // 2, self.height())
        painter.drawLine(0, self.height() // 2, self.width(), self.height() // 2)
        
        # Setup font
        font = QFont(self.font_family)
        scaled_font_size = int(self.font_size * self.height() / 360)
        font.setPixelSize(scaled_font_size)
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
        
        # Draw preview label
        painter.setPen(QColor("#8892b0"))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(10, 20, "Preview (First Line)")
    
    def _calculate_position(self, text_width: int, text_height: int) -> tuple:
        """Calculate text position based on preset and offsets."""
        w = self.width()
        h = self.height()
        
        # Scale offsets to preview size
        scaled_x = int(self.x_offset * w / 640)
        scaled_y = int(self.y_offset * h / 360)
        
        if self.position == OverlayPosition.TOP_LEFT:
            return (scaled_x, scaled_y + text_height)
        elif self.position == OverlayPosition.TOP_RIGHT:
            return (w - text_width - scaled_x, scaled_y + text_height)
        elif self.position == OverlayPosition.BOTTOM_LEFT:
            return (scaled_x, h - scaled_y)
        elif self.position == OverlayPosition.BOTTOM_RIGHT:
            return (w - text_width - scaled_x, h - scaled_y)
        elif self.position == OverlayPosition.CENTER:
            return ((w - text_width) // 2 + scaled_x,
                   (h + text_height) // 2 + scaled_y)
        else:  # CUSTOM
            return (scaled_x, scaled_y + text_height)


class BulkTextSequenceDialog(QDialog):
    """Dialog for creating multiple texts with shared settings and auto-loop."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🚀 Bulk Text Sequence (Auto-Loop)")
        self.setModal(True)
        self.setMinimumWidth(900)  # Wider for preview
        self.setMinimumHeight(700)
        
        main_layout = QHBoxLayout(self)
        
        # === LEFT SIDE: Settings ===
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # === INFO ===
        info_group = QGroupBox("💡 Quick Setup")
        info_group.setStyleSheet(self._get_group_style())
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "✨ <b>Set Once, Apply to All!</b><br>"
            "1. Enter all your texts (one per line)<br>"
            "2. Set global style (position, font, duration, interval)<br>"
            "3. Enable auto-loop to repeat until video ends!<br><br>"
            "Example: 10 texts × 1 min duration × 1 min interval = repeats every 20 minutes"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #ccd6f6; border: none; padding: 5px;")
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # === TEXT LIST ===
        text_group = QGroupBox("📝 Text List (One Per Line)")
        text_group.setStyleSheet(self._get_group_style())
        text_layout = QVBoxLayout()
        
        self._text_list_edit = QTextEdit()
        self._text_list_edit.setPlaceholderText(
            "Enter texts here, one per line:\n\n"
            "Text 1\n"
            "Text 2\n"
            "Text 3\n"
            "..."
        )
        self._text_list_edit.setMinimumHeight(150)
        self._text_list_edit.setStyleSheet("""
            QTextEdit {
                background-color: #0a192f;
                color: #ccd6f6;
                border: 1px solid #233554;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
            }
        """)
        text_layout.addWidget(self._text_list_edit)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # === TIMING ===
        timing_group = QGroupBox("⏱️ Timing (Applies to All)")
        timing_group.setStyleSheet(self._get_group_style())
        timing_layout = QVBoxLayout()
        
        # Duration
        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Text Duration:"))
        self._duration_spin = QDoubleSpinBox()
        self._duration_spin.setRange(0.5, 300)
        self._duration_spin.setValue(60.0)  # 1 minute default
        self._duration_spin.setSuffix(" sec")
        self._duration_spin.setDecimals(1)
        dur_row.addWidget(self._duration_spin)
        timing_layout.addLayout(dur_row)
        
        # Interval
        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Interval (gap between texts):"))
        self._interval_spin = QDoubleSpinBox()
        self._interval_spin.setRange(0, 300)
        self._interval_spin.setValue(60.0)  # 1 minute default
        self._interval_spin.setSuffix(" sec")
        self._interval_spin.setDecimals(1)
        interval_row.addWidget(self._interval_spin)
        timing_layout.addLayout(interval_row)
        
        # Fade in/out
        fade_row = QHBoxLayout()
        fade_row.addWidget(QLabel("Fade In:"))
        self._fade_in_spin = QDoubleSpinBox()
        self._fade_in_spin.setRange(0, 10)
        self._fade_in_spin.setValue(1.0)
        self._fade_in_spin.setSuffix(" s")
        self._fade_in_spin.setDecimals(2)
        self._fade_in_spin.setMaximumWidth(90)
        fade_row.addWidget(self._fade_in_spin)
        
        fade_row.addWidget(QLabel("Fade Out:"))
        self._fade_out_spin = QDoubleSpinBox()
        self._fade_out_spin.setRange(0, 10)
        self._fade_out_spin.setValue(1.0)
        self._fade_out_spin.setSuffix(" s")
        self._fade_out_spin.setDecimals(2)
        self._fade_out_spin.setMaximumWidth(90)
        fade_row.addWidget(self._fade_out_spin)
        fade_row.addStretch()
        timing_layout.addLayout(fade_row)
        
        # Auto-loop checkbox
        self._auto_loop_checkbox = QCheckBox("🔁 Auto-loop: Repeat sequence until video ends")
        self._auto_loop_checkbox.setChecked(True)
        self._auto_loop_checkbox.setStyleSheet("color: #64ffda; font-weight: bold; border: none;")
        timing_layout.addWidget(self._auto_loop_checkbox)
        
        # Loop count (if not auto)
        loop_row = QHBoxLayout()
        loop_row.addWidget(QLabel("Or manually repeat:"))
        self._loop_count_spin = QSpinBox()
        self._loop_count_spin.setRange(1, 100)
        self._loop_count_spin.setValue(1)
        self._loop_count_spin.setSuffix(" times")
        self._loop_count_spin.setMaximumWidth(120)
        loop_row.addWidget(self._loop_count_spin)
        loop_row.addStretch()
        timing_layout.addLayout(loop_row)
        
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)
        
        # === STYLING ===
        style_group = QGroupBox("🎨 Style (Applies to All)")
        style_group.setStyleSheet(self._get_group_style())
        style_layout = QVBoxLayout()
        
        # Font size and color
        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font Size:"))
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(12, 200)
        self._font_size_spin.setValue(48)
        self._font_size_spin.setMaximumWidth(80)
        font_row.addWidget(self._font_size_spin)
        
        font_row.addWidget(QLabel("Color:"))
        self._font_color_combo = QComboBox()
        self._font_color_combo.addItems([
            "white", "black", "red", "green", "blue", 
            "yellow", "cyan", "magenta", "orange", "lime", "pink"
        ])
        font_row.addWidget(self._font_color_combo)
        font_row.addStretch()
        style_layout.addLayout(font_row)
        
        # Max Width (text wrapping)
        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Max Width (0=no wrap):"))
        self._max_width_spin = QSpinBox()
        self._max_width_spin.setRange(0, 3840)
        self._max_width_spin.setSingleStep(50)
        self._max_width_spin.setValue(0)
        self._max_width_spin.setToolTip("Text akan wrap otomatis jika melebihi lebar ini (px). Contoh: 500 = text max 500px lebar")
        self._max_width_spin.setMaximumWidth(120)
        width_row.addWidget(self._max_width_spin)
        width_row.addStretch()
        style_layout.addLayout(width_row)
        
        # Font selector with preview
        font_label = QLabel("Font:")
        style_layout.addWidget(font_label)
        self._font_selector = FontSelector()
        self._font_selector.fontChanged.connect(self._update_preview)
        style_layout.addWidget(self._font_selector)
        
        # Effects
        effects_row = QHBoxLayout()
        self._shadow_checkbox = QCheckBox("✨ Shadow")
        self._shadow_checkbox.setChecked(True)
        effects_row.addWidget(self._shadow_checkbox)
        
        self._box_checkbox = QCheckBox("📦 Background Box")
        self._box_checkbox.setChecked(False)
        effects_row.addWidget(self._box_checkbox)
        effects_row.addStretch()
        style_layout.addLayout(effects_row)
        
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)
        
        # === POSITION ===
        pos_group = QGroupBox("📍 Position (Applies to All)")
        pos_group.setStyleSheet(self._get_group_style())
        pos_layout = QVBoxLayout()
        
        pos_combo_row = QHBoxLayout()
        pos_combo_row.addWidget(QLabel("Preset:"))
        self._position_combo = QComboBox()
        for pos in OverlayPosition:
            self._position_combo.addItem(pos.value, pos)
        self._position_combo.setCurrentIndex(4)  # CENTER
        pos_combo_row.addWidget(self._position_combo)
        pos_layout.addLayout(pos_combo_row)
        
        offset_row = QHBoxLayout()
        offset_row.addWidget(QLabel("X Offset:"))
        self._x_offset_spin = QSpinBox()
        self._x_offset_spin.setRange(-1000, 2000)
        self._x_offset_spin.setValue(0)
        offset_row.addWidget(self._x_offset_spin)
        
        offset_row.addWidget(QLabel("Y Offset:"))
        self._y_offset_spin = QSpinBox()
        self._y_offset_spin.setRange(-1000, 2000)
        self._y_offset_spin.setValue(0)
        offset_row.addWidget(self._y_offset_spin)
        offset_row.addStretch()
        pos_layout.addLayout(offset_row)
        
        pos_group.setLayout(pos_layout)
        layout.addWidget(pos_group)
        
        # === BUTTONS ===
        btn_row = QHBoxLayout()
        
        generate_btn = QPushButton("✅ Generate Sequence")
        generate_btn.setStyleSheet("""
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
        generate_btn.clicked.connect(self.accept)
        generate_btn.setDefault(True)
        btn_row.addWidget(generate_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        layout.addLayout(btn_row)
        
        main_layout.addWidget(left_widget, stretch=1)
        
        # === RIGHT SIDE: Preview ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("🎬 LIVE PREVIEW (First Line)")
        preview_label.setStyleSheet("color: #64ffda; font-weight: bold; font-size: 14px;")
        preview_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(preview_label)
        
        self._preview_frame = BulkPreviewFrame()
        right_layout.addWidget(self._preview_frame)
        
        preview_info = QLabel(
            "Preview akan update otomatis saat kamu ubah:\n"
            "• Text (baris pertama)\n"
            "• Font & Size\n"
            "• Position & Color"
        )
        preview_info.setStyleSheet("color: #8892b0; font-size: 11px;")
        preview_info.setWordWrap(True)
        right_layout.addWidget(preview_info)
        
        right_layout.addStretch()
        main_layout.addWidget(right_widget, stretch=0)
        
        # Connect signals for live preview
        self._text_list_edit.textChanged.connect(self._update_preview)
        self._font_size_spin.valueChanged.connect(self._update_preview)
        self._font_color_combo.currentTextChanged.connect(self._update_preview)
        self._position_combo.currentIndexChanged.connect(self._update_preview)
        self._x_offset_spin.valueChanged.connect(self._update_preview)
        self._y_offset_spin.valueChanged.connect(self._update_preview)
        self._shadow_checkbox.toggled.connect(self._update_preview)
        self._box_checkbox.toggled.connect(self._update_preview)
        
        # Initial preview update
        self._update_preview()
    
    def _update_preview(self):
        """Update live preview with current settings."""
        # Get first line of text as preview
        text_content = self._text_list_edit.toPlainText()
        text_lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        preview_text = text_lines[0] if text_lines else "Sample Text (First Line)"
        
        # Get current font family from selector
        font_family = "Arial"  # Default
        current_font = self._font_selector._font_combo.currentText()
        if current_font and not current_font.startswith("🎨"):
            font_family = current_font.replace("📁 ", "")
        
        self._preview_frame.update_preview(
            text=preview_text,
            font_size=self._font_size_spin.value(),
            color=self._font_color_combo.currentText(),
            position=self._position_combo.currentData(),
            x_offset=self._x_offset_spin.value(),
            y_offset=self._y_offset_spin.value(),
            shadow=self._shadow_checkbox.isChecked(),
            box=self._box_checkbox.isChecked(),
            font_family=font_family
        )
    
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
    
    
    def get_sequence_items(self) -> list:
        """
        Generate sequence of AnimatedTextItem objects based on settings.
        
        Returns:
            List of AnimatedTextItem objects
        """
        # Get text list
        text_content = self._text_list_edit.toPlainText()
        text_lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        if not text_lines:
            return []
        
        # Get settings
        duration = self._duration_spin.value()
        interval = self._interval_spin.value()
        fade_in = self._fade_in_spin.value()
        fade_out = self._fade_out_spin.value()
        font_size = self._font_size_spin.value()
        font_color = self._font_color_combo.currentText()
        font_file = self._font_selector.get_font_path()  # Use font selector
        position = self._position_combo.currentData()
        x_offset = self._x_offset_spin.value()
        y_offset = self._y_offset_spin.value()
        shadow = self._shadow_checkbox.isChecked()
        box = self._box_checkbox.isChecked()
        max_width = self._max_width_spin.value()
        auto_loop = self._auto_loop_checkbox.isChecked()
        loop_count = self._loop_count_spin.value() if not auto_loop else 1
        
        # Calculate time per text (duration + interval)
        time_per_text = duration + interval
        
        # Generate items
        items = []
        current_time = 0.0
        
        # If auto-loop, we'll create a lot of repeats (e.g., 100 loops = ~33 hours of coverage)
        # User can always generate more if needed
        max_loops = 100 if auto_loop else loop_count
        
        for loop_idx in range(max_loops):
            for text_idx, text in enumerate(text_lines):
                item = AnimatedTextItem(
                    text=text,
                    start_time=current_time,
                    duration=duration,
                    fade_in=fade_in,
                    fade_out=fade_out,
                    font_file=font_file,
                    font_size=font_size,
                    font_color=font_color,
                    position=position,
                    x_offset=x_offset,
                    y_offset=y_offset,
                    shadow=shadow,
                    box=box,
                    max_width=max_width,
                    enabled=True
                )
                items.append(item)
                current_time += time_per_text
        
        return items

