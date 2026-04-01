"""
Now Playing Preview Dialog - Preview judul lagu (posisi, font, warna, ukuran).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter, QFontDatabase

from core.media_manager import OverlayPosition


class NowPlayingPreviewDialog(QDialog):
    """Dialog untuk preview styling Now Playing (judul lagu dari nama file)."""
    
    def __init__(self, now_playing_config, sample_titles=None, parent=None):
        super().__init__(parent)
        self.now_playing_config = now_playing_config
        self.sample_titles = sample_titles or ["Judul Lagu - Artist"]
        self.setWindowTitle("Preview Now Playing")
        self.setModal(True)
        self.resize(900, 560)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_widget = NowPlayingPreviewWidget(
            self.now_playing_config,
            self.sample_titles[0] if self.sample_titles else "Now Playing"
        )
        layout.addWidget(self.preview_widget)
        
        pos = self.now_playing_config.position
        pos_name = getattr(pos, 'name', str(pos))
        info_parts = [
            f"Font Size: {self.now_playing_config.font_size}",
            f"Color: {self.now_playing_config.font_color}",
            f"Position: {pos_name}"
        ]
        info_label = QLabel(" | ".join(info_parts))
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
        
        close_btn = QPushButton("Tutup")
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


class NowPlayingPreviewWidget(QWidget):
    """Widget untuk render teks Now Playing dengan styling."""
    
    def __init__(self, now_playing_config, sample_title="Now Playing", parent=None):
        super().__init__(parent)
        self.config = now_playing_config
        self.sample_title = sample_title
        self.setMinimumHeight(400)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        
        painter.fillRect(self.rect(), QColor("#0a0a14"))
        
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(15, 52, 96, 50))
        gradient.setColorAt(1, QColor(10, 10, 20, 50))
        painter.fillRect(self.rect(), gradient)
        
        font = QFont()
        if self.config.font_file:
            font_id = QFontDatabase.addApplicationFont(self.config.font_file)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    font.setFamily(families[0])
        font.setPixelSize(self.config.font_size)
        painter.setFont(font)
        
        text = self.sample_title
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        
        pos = self.config.position
        x_offset = self.config.x_offset
        y_offset = self.config.y_offset
        
        if pos == OverlayPosition.TOP_LEFT:
            x = x_offset
            y = y_offset + text_height
        elif pos == OverlayPosition.TOP_RIGHT:
            x = self.width() - text_width - x_offset
            y = y_offset + text_height
        elif pos == OverlayPosition.TOP_CENTER:
            x = (self.width() - text_width) // 2 + x_offset
            y = y_offset + text_height
        elif pos == OverlayPosition.BOTTOM_LEFT:
            x = x_offset
            y = self.height() - text_height - y_offset
        elif pos == OverlayPosition.BOTTOM_RIGHT:
            x = self.width() - text_width - x_offset
            y = self.height() - text_height - y_offset
        elif pos == OverlayPosition.BOTTOM_CENTER:
            x = (self.width() - text_width) // 2 + x_offset
            y = self.height() - text_height - y_offset
        elif pos == OverlayPosition.CENTER:
            x = (self.width() - text_width) // 2 + x_offset
            y = (self.height() - text_height) // 2 + y_offset
        else:
            x = x_offset
            y = y_offset + text_height
        
        try:
            text_color = QColor(self.config.font_color)
        except Exception:
            text_color = QColor("white")
        painter.setPen(text_color)
        painter.drawText(x, y, text)
