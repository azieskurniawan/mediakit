"""
Subtitle Preview Dialog - Shows dummy subtitle with user's styling.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter, QPen
from typing import Optional


class SubtitlePreviewDialog(QDialog):
    """Dialog to preview subtitle styling with dummy text."""
    
    def __init__(self, subtitle_config, parent=None):
        super().__init__(parent)
        self.subtitle_config = subtitle_config
        self.setWindowTitle("Preview Subtitle Styling")
        self.setModal(True)
        self.resize(800, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview area (simulates video background)
        self.preview_widget = SubtitlePreviewWidget(self.subtitle_config)
        layout.addWidget(self.preview_widget)
        
        # Info label
        info_label = QLabel(
            f"Font Size: {self.subtitle_config.font_size} | "
            f"Color: {self.subtitle_config.font_color} | "
            f"Outline: {self.subtitle_config.outline_color} ({self.subtitle_config.outline_width}px)"
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #16213e;
                color: #00d4ff;
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(info_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #0a0a14;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #00b8e6;
            }
        """)
        layout.addWidget(close_btn)


class SubtitlePreviewWidget(QWidget):
    """Widget to render dummy subtitle with styling."""
    
    def __init__(self, subtitle_config, parent=None):
        super().__init__(parent)
        self.subtitle_config = subtitle_config
        self.setMinimumHeight(400)
        
        # Dummy subtitle text (multi-line)
        self.subtitle_lines = [
            "♪ Ini adalah contoh lirik subtitle ♪",
            "♪ Dengan styling yang Anda pilih ♪"
        ]
    
    def paintEvent(self, event):
        """Custom paint event to draw subtitle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background (simulate video background)
        painter.fillRect(self.rect(), QColor("#0a0a14"))
        
        # Draw gradient overlay
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(15, 52, 96, 50))
        gradient.setColorAt(1, QColor(10, 10, 20, 50))
        painter.fillRect(self.rect(), gradient)
        
        # Setup font
        font = QFont()
        if self.subtitle_config.font_file:
            from PySide6.QtGui import QFontDatabase
            font_id = QFontDatabase.addApplicationFont(self.subtitle_config.font_file)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font.setFamily(font_families[0])
        
        font.setPixelSize(self.subtitle_config.font_size)
        font.setBold(True)
        painter.setFont(font)
        
        # Calculate text position based on alignment
        text_width = 0
        text_height = 0
        
        # Measure text
        for line in self.subtitle_lines:
            metrics = painter.fontMetrics()
            line_width = metrics.horizontalAdvance(line)
            line_height = metrics.height()
            text_width = max(text_width, line_width)
            text_height += line_height
        
        # Position based on alignment
        # FFmpeg alignment: 1-9
        # 7 8 9 (top)
        # 4 5 6 (middle)
        # 1 2 3 (bottom)
        alignment = self.subtitle_config.alignment
        margin_v = self.subtitle_config.margin_v
        
        # X position
        if alignment in [1, 4, 7]:  # Left
            x = self.subtitle_config.margin_h
        elif alignment in [3, 6, 9]:  # Right
            x = self.width() - text_width - self.subtitle_config.margin_h
        else:  # Center (2, 5, 8)
            x = (self.width() - text_width) // 2
        
        # Y position
        if alignment in [7, 8, 9]:  # Top
            y = margin_v
        elif alignment in [4, 5, 6]:  # Middle
            y = (self.height() - text_height) // 2
        else:  # Bottom (1, 2, 3)
            y = self.height() - text_height - margin_v
        
        # Draw each line
        current_y = y
        for line in self.subtitle_lines:
            # Draw outline/stroke (multiple passes for thickness)
            outline_color = QColor(self.subtitle_config.outline_color)
            outline_width = self.subtitle_config.outline_width
            
            if outline_width > 0:
                painter.setPen(QPen(outline_color, outline_width * 2))
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx != 0 or dy != 0:
                            painter.drawText(x + dx, current_y + dy, line)
            
            # Draw main text
            text_color = QColor(self.subtitle_config.font_color)
            painter.setPen(text_color)
            painter.drawText(x, current_y, line)
            
            current_y += painter.fontMetrics().height()
