"""
Settings Dialog - FFmpeg path configuration.
"""
import os
import subprocess
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.settings_manager import SettingsManager


class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings_manager = settings_manager
        self._setup_ui()
        self._apply_styles()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Settings - FFmpeg Exporter")
        self.setMinimumSize(500, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Application Settings")
        title.setObjectName("dialogTitle")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # FFmpeg settings group
        ffmpeg_group = self._create_ffmpeg_section()
        layout.addWidget(ffmpeg_group)
        
        # Status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #8892b0;")
        layout.addWidget(self._status_label)
        
        layout.addStretch()
        
        # Buttons
        button_row = QHBoxLayout()
        button_row.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("saveButton")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._save_settings)
        button_row.addWidget(save_btn)
        
        layout.addLayout(button_row)
    
    def _create_ffmpeg_section(self) -> QGroupBox:
        """Create FFmpeg configuration section."""
        group = QGroupBox("FFmpeg Configuration")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # FFmpeg path
        ffmpeg_label = QLabel("FFmpeg Executable Path:")
        layout.addWidget(ffmpeg_label)
        
        ffmpeg_row = QHBoxLayout()
        self._ffmpeg_edit = QLineEdit()
        self._ffmpeg_edit.setPlaceholderText("Path to ffmpeg.exe...")
        ffmpeg_row.addWidget(self._ffmpeg_edit)
        
        ffmpeg_btn = QPushButton("Browse...")
        ffmpeg_btn.setFixedWidth(100)
        ffmpeg_btn.clicked.connect(self._browse_ffmpeg)
        ffmpeg_row.addWidget(ffmpeg_btn)
        
        detect_btn = QPushButton("Auto-detect")
        detect_btn.setFixedWidth(100)
        detect_btn.clicked.connect(self._auto_detect_ffmpeg)
        ffmpeg_row.addWidget(detect_btn)
        layout.addLayout(ffmpeg_row)
        
        # FFprobe path
        ffprobe_label = QLabel("FFprobe Executable Path (Optional):")
        layout.addWidget(ffprobe_label)
        
        ffprobe_row = QHBoxLayout()
        self._ffprobe_edit = QLineEdit()
        self._ffprobe_edit.setPlaceholderText("Path to ffprobe.exe (usually in same folder as ffmpeg)...")
        ffprobe_row.addWidget(self._ffprobe_edit)
        
        ffprobe_btn = QPushButton("Browse...")
        ffprobe_btn.setFixedWidth(100)
        ffprobe_btn.clicked.connect(self._browse_ffprobe)
        ffprobe_row.addWidget(ffprobe_btn)
        layout.addLayout(ffprobe_row)
        
        # Verify button
        verify_btn = QPushButton("Verify FFmpeg Installation")
        verify_btn.clicked.connect(self._verify_ffmpeg)
        layout.addWidget(verify_btn)
        
        return group
    
    def _apply_styles(self) -> None:
        """Apply styles to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            
            #dialogTitle {
                color: #00d4ff;
            }
            
            QLabel {
                color: #ccd6f6;
            }
            
            QLineEdit {
                background-color: #0f3460;
                color: white;
                border: 1px solid #1a4f7a;
                border-radius: 5px;
                padding: 8px;
                min-height: 20px;
            }
            
            QLineEdit:focus {
                border: 1px solid #00d4ff;
            }
            
            QGroupBox {
                color: #8892b0;
                font-weight: bold;
                border: 1px solid #0f3460;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
            }
            
            QPushButton:hover {
                background-color: #1a4f7a;
            }
            
            #saveButton {
                background-color: #00d4ff;
                color: #16213e;
                font-weight: bold;
            }
            
            #saveButton:hover {
                background-color: #00b8e6;
            }
        """)
    
    def _load_settings(self) -> None:
        """Load current settings into UI."""
        settings = self._settings_manager.settings
        self._ffmpeg_edit.setText(settings.ffmpeg_path)
        self._ffprobe_edit.setText(settings.ffprobe_path)
    
    def _browse_ffmpeg(self) -> None:
        """Browse for FFmpeg executable."""
        file_filter = "Executable (*.exe)" if os.name == 'nt' else "All Files (*)"
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select FFmpeg Executable", "", file_filter
        )
        if filepath:
            self._ffmpeg_edit.setText(filepath)
            # Auto-detect ffprobe in same directory
            ffprobe_path = self._find_ffprobe_near(filepath)
            if ffprobe_path and not self._ffprobe_edit.text():
                self._ffprobe_edit.setText(ffprobe_path)
    
    def _browse_ffprobe(self) -> None:
        """Browse for FFprobe executable."""
        file_filter = "Executable (*.exe)" if os.name == 'nt' else "All Files (*)"
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select FFprobe Executable", "", file_filter
        )
        if filepath:
            self._ffprobe_edit.setText(filepath)
    
    def _find_ffprobe_near(self, ffmpeg_path: str) -> str:
        """Find ffprobe near ffmpeg."""
        directory = os.path.dirname(ffmpeg_path)
        
        if os.name == 'nt':
            ffprobe_name = "ffprobe.exe"
        else:
            ffprobe_name = "ffprobe"
        
        ffprobe_path = os.path.join(directory, ffprobe_name)
        if os.path.isfile(ffprobe_path):
            return ffprobe_path
        
        return ""
    
    def _auto_detect_ffmpeg(self) -> None:
        """Try to auto-detect FFmpeg in system PATH."""
        try:
            # Try to find ffmpeg in PATH
            if os.name == 'nt':
                result = subprocess.run(
                    ['where', 'ffmpeg'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    ['which', 'ffmpeg'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            if result.returncode == 0 and result.stdout.strip():
                ffmpeg_path = result.stdout.strip().split('\n')[0]
                self._ffmpeg_edit.setText(ffmpeg_path)
                
                # Try to find ffprobe too
                ffprobe_path = self._find_ffprobe_near(ffmpeg_path)
                if ffprobe_path:
                    self._ffprobe_edit.setText(ffprobe_path)
                
                self._status_label.setText("✓ FFmpeg found in system PATH")
                self._status_label.setStyleSheet("color: #00ff00;")
            else:
                self._status_label.setText("✗ FFmpeg not found in system PATH")
                self._status_label.setStyleSheet("color: #ff6b6b;")
        
        except Exception as e:
            self._status_label.setText(f"✗ Auto-detect failed: {str(e)}")
            self._status_label.setStyleSheet("color: #ff6b6b;")
    
    def _verify_ffmpeg(self) -> None:
        """Verify FFmpeg installation."""
        ffmpeg_path = self._ffmpeg_edit.text().strip()
        
        if not ffmpeg_path:
            QMessageBox.warning(
                self, "No Path",
                "Please enter or browse for FFmpeg path first."
            )
            return
        
        if not os.path.isfile(ffmpeg_path):
            QMessageBox.warning(
                self, "File Not Found",
                f"The specified FFmpeg path does not exist:\n{ffmpeg_path}"
            )
            return
        
        try:
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                # Extract version info
                version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
                self._status_label.setText(f"✓ {version_line}")
                self._status_label.setStyleSheet("color: #00ff00;")
                
                QMessageBox.information(
                    self, "FFmpeg Verified",
                    f"FFmpeg is working correctly!\n\n{version_line}"
                )
            else:
                self._status_label.setText("✗ FFmpeg returned an error")
                self._status_label.setStyleSheet("color: #ff6b6b;")
                
                QMessageBox.warning(
                    self, "Verification Failed",
                    f"FFmpeg returned an error:\n{result.stderr}"
                )
        
        except subprocess.TimeoutExpired:
            self._status_label.setText("✗ FFmpeg verification timed out")
            self._status_label.setStyleSheet("color: #ff6b6b;")
            QMessageBox.warning(self, "Timeout", "FFmpeg verification timed out.")
        
        except Exception as e:
            self._status_label.setText(f"✗ Error: {str(e)}")
            self._status_label.setStyleSheet("color: #ff6b6b;")
            QMessageBox.warning(self, "Error", f"Failed to verify FFmpeg:\n{str(e)}")
    
    def _save_settings(self) -> None:
        """Save settings and close dialog."""
        ffmpeg_path = self._ffmpeg_edit.text().strip()
        ffprobe_path = self._ffprobe_edit.text().strip()
        
        # Validate FFmpeg path
        if ffmpeg_path and not os.path.isfile(ffmpeg_path):
            QMessageBox.warning(
                self, "Invalid Path",
                "The specified FFmpeg path does not exist."
            )
            return
        
        # Auto-detect ffprobe if not provided but ffmpeg is
        if ffmpeg_path and not ffprobe_path:
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            auto_ffprobe = os.path.join(ffmpeg_dir, 'ffprobe.exe' if os.name == 'nt' else 'ffprobe')
            if os.path.isfile(auto_ffprobe):
                ffprobe_path = auto_ffprobe
                print(f"Auto-detected ffprobe: {ffprobe_path}")
        
        # Validate FFprobe path if provided
        if ffprobe_path and not os.path.isfile(ffprobe_path):
            QMessageBox.warning(
                self, "Invalid Path",
                "The specified FFprobe path does not exist."
            )
            return
        
        # Save settings
        self._settings_manager.update(
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path
        )
        
        self.accept()
