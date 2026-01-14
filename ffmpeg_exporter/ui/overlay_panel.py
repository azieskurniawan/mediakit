"""
Advanced Overlay Panel - Manage overlays with blend modes and chroma key.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QGroupBox,
    QMessageBox
)
from PySide6.QtCore import Qt
from core.media_manager import OverlayConfig
from ui.overlay_dialog import OverlayDialog


class OverlayPanel(QWidget):
    """Panel for managing advanced overlays."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlays = []  # List of OverlayConfig
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🎨 ADVANCED OVERLAYS")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #3b82f6;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Description
        desc = QLabel(
            "Add overlays with <b>blend modes</b> (like Photoshop) + optional <b>chroma key</b> removal.\n"
            "Perfect for audio spectrum, logos, effects, and creative compositions!"
        )
        desc.setStyleSheet("color: #999; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Overlay list
        list_group = QGroupBox("Overlay List")
        list_layout = QVBoxLayout()
        
        self.overlay_list = QListWidget()
        self.overlay_list.setMinimumHeight(200)
        self.overlay_list.itemDoubleClicked.connect(self._edit_overlay)
        list_layout.addWidget(self.overlay_list)
        
        # Buttons - Grid 3x2 layout
        from PySide6.QtWidgets import QGridLayout
        btn_layout = QGridLayout()
        btn_layout.setSpacing(5)
        
        # Row 1
        add_btn = QPushButton("➕ Add Overlay")
        add_btn.clicked.connect(self._add_overlay)
        btn_layout.addWidget(add_btn, 0, 0)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self._edit_overlay)
        btn_layout.addWidget(edit_btn, 0, 1)
        
        duplicate_btn = QPushButton("📋 Duplicate")
        duplicate_btn.clicked.connect(self._duplicate_overlay)
        btn_layout.addWidget(duplicate_btn, 0, 2)
        
        # Row 2
        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.clicked.connect(self._remove_overlay)
        btn_layout.addWidget(remove_btn, 1, 0)
        
        move_up_btn = QPushButton("⬆ Move Up")
        move_up_btn.clicked.connect(self._move_up)
        btn_layout.addWidget(move_up_btn, 1, 1)
        
        move_down_btn = QPushButton("⬇ Move Down")
        move_down_btn.clicked.connect(self._move_down)
        btn_layout.addWidget(move_down_btn, 1, 2)
        
        list_layout.addLayout(btn_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Tips
        tips = QLabel(
            "💡 <b>Tips:</b><br>"
            "• <b>Blend Modes:</b> Multiply (darken), Screen (lighten), Overlay (contrast)<br>"
            "• <b>Opacity:</b> Transparency level (0-100%)<br>"
            "• <b>Chroma Key:</b> Remove solid color backgrounds (green/blue/black screen)<br>"
            "• <b>Loop:</b> Play overlay for entire video duration (default)<br>"
            "• <b>Combine:</b> Chroma Key + Blend Mode for best results!<br>"
            "• Multiple overlays applied in order (top to bottom)"
        )
        tips.setStyleSheet("""
            QLabel {
                padding: 10px;
                background: #2a2a2a;
                border-radius: 4px;
                border-left: 3px solid #3b82f6;
            }
        """)
        tips.setWordWrap(True)
        layout.addWidget(tips)
        
        layout.addStretch()
    
    def _add_overlay(self):
        """Add new overlay."""
        dialog = OverlayDialog(parent=self)
        if dialog.exec():
            config = dialog.get_config()
            if config.filepath:
                self.overlays.append(config)
                self._update_list()
            else:
                QMessageBox.warning(self, "Invalid Config", "Please select an overlay file.")
    
    def _edit_overlay(self):
        """Edit selected overlay."""
        current_row = self.overlay_list.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an overlay to edit.")
            return
        
        config = self.overlays[current_row]
        dialog = OverlayDialog(config, parent=self)
        if dialog.exec():
            self.overlays[current_row] = dialog.get_config()
            self._update_list()
    
    def _duplicate_overlay(self):
        """Duplicate selected overlay."""
        current_row = self.overlay_list.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an overlay to duplicate.")
            return
        
        # Create a copy
        import copy
        config = copy.deepcopy(self.overlays[current_row])
        self.overlays.insert(current_row + 1, config)
        self._update_list()
        self.overlay_list.setCurrentRow(current_row + 1)
    
    def _remove_overlay(self):
        """Remove selected overlay."""
        current_row = self.overlay_list.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an overlay to remove.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Remove",
            "Remove this overlay?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.overlays[current_row]
            self._update_list()
    
    def _move_up(self):
        """Move selected overlay up."""
        current_row = self.overlay_list.currentRow()
        if current_row > 0:
            self.overlays[current_row], self.overlays[current_row - 1] = \
                self.overlays[current_row - 1], self.overlays[current_row]
            self._update_list()
            self.overlay_list.setCurrentRow(current_row - 1)
    
    def _move_down(self):
        """Move selected overlay down."""
        current_row = self.overlay_list.currentRow()
        if 0 <= current_row < len(self.overlays) - 1:
            self.overlays[current_row], self.overlays[current_row + 1] = \
                self.overlays[current_row + 1], self.overlays[current_row]
            self._update_list()
            self.overlay_list.setCurrentRow(current_row + 1)
    
    def _update_list(self):
        """Update overlay list display."""
        self.overlay_list.clear()
        for i, overlay in enumerate(self.overlays):
            filename = overlay.filepath.split('/')[-1].split('\\')[-1] if overlay.filepath else "No file"
            
            # Build display text
            mode_name = overlay.blend_mode.value.upper() if overlay.blend_mode else "NORMAL"
            opacity_pct = int(overlay.opacity * 100)
            timing = "LOOP" if overlay.loop else f"{overlay.start_time}s-{overlay.start_time + overlay.duration}s"
            
            text = (
                f"#{i+1} - {filename}\n"
                f"   Mode: {mode_name}  |  Opacity: {opacity_pct}%  |  "
                f"Size: {overlay.size_percent}%  |  {overlay.position.value.replace('_', ' ').title()}\n"
                f"   Timing: {timing}  |  "
                f"Chroma Key: {'ON' if overlay.chroma_key_enabled else 'OFF'}"
            )
            
            item = QListWidgetItem(text)
            if not overlay.enabled:
                item.setForeground(Qt.gray)
            self.overlay_list.addItem(item)
    
    def get_overlays(self):
        """Get all overlays."""
        return self.overlays
    
    def set_overlays(self, overlays):
        """Set overlays."""
        self.overlays = overlays or []
        self._update_list()


# Legacy alias
ChromaKeyPanel = OverlayPanel

