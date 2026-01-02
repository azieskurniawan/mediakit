"""
Font selector widget with system font listing and preview.
"""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFileDialog, QLineEdit
)
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import Qt, Signal


class FontSelector(QWidget):
    """Widget for selecting fonts from system or custom files with preview."""
    
    fontChanged = Signal(str)  # Emits font file path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._font_file_path = ""
        self._init_ui()
        self._load_system_fonts()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Font selector row
        selector_row = QHBoxLayout()
        
        # Font dropdown with preview
        self._font_combo = QComboBox()
        self._font_combo.setMinimumWidth(200)
        self._font_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
            }
            QComboBox::drop-down {
                width: 30px;
            }
            QComboBox QAbstractItemView {
                selection-background-color: #64ffda;
                selection-color: #0a192f;
            }
        """)
        self._font_combo.currentTextChanged.connect(self._on_font_selected)
        selector_row.addWidget(self._font_combo, stretch=1)
        
        # Browse button for custom font
        browse_btn = QPushButton("📁 Browse .ttf")
        browse_btn.setToolTip("Select custom TrueType Font file")
        browse_btn.clicked.connect(self._browse_font)
        browse_btn.setMaximumWidth(120)
        selector_row.addWidget(browse_btn)
        
        layout.addLayout(selector_row)
        
        # Preview label (shows sample text in selected font)
        self._preview_label = QLabel("AaBbCc 123 — Preview Text")
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setMinimumHeight(40)
        self._preview_label.setStyleSheet("""
            QLabel {
                background-color: #0a192f;
                border: 1px solid #233554;
                border-radius: 4px;
                padding: 8px;
                color: #64ffda;
            }
        """)
        layout.addWidget(self._preview_label)
        
        # Current font path display
        self._path_label = QLabel("System Font")
        self._path_label.setStyleSheet("color: #8892b0; font-size: 10px;")
        self._path_label.setWordWrap(True)
        layout.addWidget(self._path_label)
    
    def _load_system_fonts(self):
        """Load system fonts from Windows fonts directory."""
        self._font_combo.clear()
        
        # Get system font families
        font_families = QFontDatabase.families()
        
        # Add "System Fonts" category
        self._font_combo.addItem("🎨 --- System Fonts ---", "")
        
        # Map to store font family -> font file path
        self._font_paths = {}
        
        # Add system fonts
        for family in sorted(font_families):
            self._font_combo.addItem(family, "system")
            # Try to find the actual font file
            font_path = self._find_font_file(family)
            if font_path:
                self._font_paths[family] = font_path
        
        # Set default to first actual font
        if self._font_combo.count() > 1:
            self._font_combo.setCurrentIndex(1)
    
    def _find_font_file(self, font_family: str) -> str:
        """
        Try to find the .ttf file for a font family.
        
        Args:
            font_family: Font family name
            
        Returns:
            Path to .ttf file if found, empty string otherwise
        """
        # Common Windows font directories
        font_dirs = [
            Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts',
            Path.home() / 'AppData' / 'Local' / 'Microsoft' / 'Windows' / 'Fonts'
        ]
        
        # Common font file patterns
        patterns = [
            f"{font_family}.ttf",
            f"{font_family.replace(' ', '')}.ttf",
            f"{font_family.lower().replace(' ', '')}.ttf",
            f"{font_family}Regular.ttf",
            f"{font_family.replace(' ', '')}Regular.ttf",
        ]
        
        for font_dir in font_dirs:
            if not font_dir.exists():
                continue
            
            for pattern in patterns:
                font_path = font_dir / pattern
                if font_path.exists():
                    return str(font_path)
            
            # Try case-insensitive search
            try:
                for file in font_dir.glob("*.ttf"):
                    if font_family.lower() in file.stem.lower():
                        return str(file)
            except PermissionError:
                pass
        
        return ""
    
    def _on_font_selected(self, font_name: str):
        """Handle font selection from dropdown."""
        if not font_name or font_name.startswith("🎨"):
            return
        
        # Update preview with selected font
        font = QFont(font_name)
        font.setPointSize(14)
        self._preview_label.setFont(font)
        
        # Try to get font file path
        if font_name in self._font_paths:
            self._font_file_path = self._font_paths[font_name]
            self._path_label.setText(f"📂 {self._font_file_path}")
        else:
            self._font_file_path = ""
            self._path_label.setText(f"System Font: {font_name} (no .ttf path found)")
        
        # Emit signal
        self.fontChanged.emit(self._font_file_path)
    
    def _browse_font(self):
        """Browse for custom font file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Font File",
            "",
            "TrueType Fonts (*.ttf);;All Files (*.*)"
        )
        
        if file_path:
            # Load custom font
            font_id = QFontDatabase.addApplicationFont(file_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font_family = font_families[0]
                    
                    # Add to combo if not exists
                    existing_idx = self._font_combo.findText(font_family)
                    if existing_idx == -1:
                        self._font_combo.addItem(f"📁 {font_family}", "custom")
                        self._font_combo.setCurrentIndex(self._font_combo.count() - 1)
                    else:
                        self._font_combo.setCurrentIndex(existing_idx)
                    
                    # Set font path
                    self._font_file_path = file_path
                    self._font_paths[font_family] = file_path
                    self._path_label.setText(f"📂 {file_path}")
                    
                    # Update preview
                    font = QFont(font_family)
                    font.setPointSize(14)
                    self._preview_label.setFont(font)
                    
                    # Emit signal
                    self.fontChanged.emit(file_path)
    
    def get_font_path(self) -> str:
        """Get current selected font file path."""
        return self._font_file_path
    
    def set_font_path(self, path: str):
        """Set font by file path."""
        if not path or not os.path.isfile(path):
            return
        
        # Load font from file
        font_id = QFontDatabase.addApplicationFont(path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                font_family = font_families[0]
                
                # Find or add to combo
                idx = self._font_combo.findText(font_family)
                if idx == -1:
                    self._font_combo.addItem(f"📁 {font_family}", "custom")
                    idx = self._font_combo.count() - 1
                
                self._font_combo.setCurrentIndex(idx)
                self._font_file_path = path
                self._font_paths[font_family] = path

