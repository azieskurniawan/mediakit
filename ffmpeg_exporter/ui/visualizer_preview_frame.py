"""
Visualizer Preview Frame - Real-time preview for visualizers.
"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PIL import Image
from PIL.ImageQt import ImageQt
import numpy as np


class VisualizerPreviewFrame(QFrame):
    """Preview frame for visualizer (real-time single frame)."""
    
    refresh_requested = Signal()
    
    def __init__(self, width: int = 400, height: int = 300):
        """
        Initialize preview frame.
        
        Args:
            width: Preview width.
            height: Preview height.
        """
        super().__init__()
        self._preview_width = width
        self._preview_height = height
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.setMinimumSize(self._preview_width, self._preview_height)
        
        layout = QVBoxLayout(self)
        
        # Preview label
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumSize(self._preview_width, self._preview_height)
        self._preview_label.setScaledContents(False)
        self._preview_label.setStyleSheet("background-color: #1a1a1a; color: #888;")
        self._preview_label.setText("Preview will appear here\n\nAdd audio files and adjust settings")
        layout.addWidget(self._preview_label)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Preview")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        layout.addWidget(refresh_btn)
    
    def set_preview_image(self, image: Image.Image):
        """
        Set preview image.
        
        Args:
            image: PIL Image to display.
        """
        if image is None:
            self._preview_label.setText("No preview available")
            return
        
        # Convert PIL Image to QPixmap
        qimage = ImageQt(image.convert('RGBA'))
        pixmap = QPixmap.fromImage(qimage)
        
        # Scale to fit preview size while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self._preview_width - 20,
            self._preview_height - 60,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self._preview_label.setPixmap(scaled_pixmap)
    
    def clear_preview(self):
        """Clear preview."""
        self._preview_label.clear()
        self._preview_label.setText("Preview cleared")
    
    def show_error(self, message: str):
        """Show error message."""
        self._preview_label.clear()
        self._preview_label.setText(f"Error:\n{message}")
    
    def show_loading(self):
        """Show loading message."""
        self._preview_label.clear()
        self._preview_label.setText("Loading preview...")

