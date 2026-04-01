"""
Export Dialog - Video export settings and real-time FFmpeg logging.
"""
import os
import subprocess
import time
from typing import Optional, List
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QComboBox, QGroupBox, QFileDialog,
    QProgressBar, QTextEdit, QWidget, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtGui import QFont, QTextCursor

from core.settings_manager import SettingsManager
from core.media_manager import MediaConfig
from core.job_manager import JobManager, JobType
from core.ffmpeg_builder import (
    FFmpegBuilder, ExportSettings, VideoCodec, AudioCodec, RateControl, EncodingMethod
)


class ExportWorker(QObject):
    """Worker for running FFmpeg export in background thread."""
    
    # Signals
    log_output = Signal(str)
    progress_update = Signal(int)
    export_finished = Signal(bool, str)  # success, message
    
    def __init__(self, command: List[str], temp_files: List[str]):
        super().__init__()
        self._command = command
        self._temp_files = temp_files
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False
    
    def run(self) -> None:
        """Run the FFmpeg export process."""
        try:
            self.log_output.emit(f"Starting export...\n")
            self.log_output.emit(f"Command: {' '.join(self._command)}\n\n")
            
            # Create process with pipe for output
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            self._process = subprocess.Popen(
                self._command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags,
                universal_newlines=True
            )
            
            # Read output line by line in real-time
            duration_seconds = 0
            
            for line in iter(self._process.stdout.readline, ''):
                if self._cancelled:
                    self._process.terminate()
                    self.log_output.emit("\n\n[EXPORT CANCELLED]\n")
                    self._cleanup()
                    self.export_finished.emit(False, "Export cancelled by user")
                    return
                
                self.log_output.emit(line)
                
                # Try to extract progress from FFmpeg output
                if "Duration:" in line:
                    try:
                        time_str = line.split("Duration:")[1].split(",")[0].strip()
                        parts = time_str.split(":")
                        duration_seconds = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    except (IndexError, ValueError):
                        pass
                
                if "time=" in line and duration_seconds > 0:
                    try:
                        time_str = line.split("time=")[1].split()[0]
                        parts = time_str.split(":")
                        current_seconds = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                        progress = min(int((current_seconds / duration_seconds) * 100), 100)
                        self.progress_update.emit(progress)
                    except (IndexError, ValueError):
                        pass
            
            # Wait for process to complete
            self._process.wait()
            
            # Check exit code
            if self._process.returncode == 0:
                self.progress_update.emit(100)
                self.log_output.emit("\n\n✓ Export completed successfully!\n")
                self._cleanup()
                self.export_finished.emit(True, "Export completed successfully!")
            else:
                self.log_output.emit(f"\n\n✗ Export failed with exit code: {self._process.returncode}\n")
                self._cleanup()
                self.export_finished.emit(False, f"Export failed with exit code: {self._process.returncode}")
        
        except Exception as e:
            self.log_output.emit(f"\n\nError: {str(e)}\n")
            self._cleanup()
            self.export_finished.emit(False, str(e))
    
    def cancel(self) -> None:
        """Cancel the export process."""
        self._cancelled = True
        if self._process:
            self._process.terminate()
    
    def _cleanup(self) -> None:
        """Clean up temporary files."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except OSError:
                pass


class ExportDialog(QDialog):
    """Dialog for export settings and execution."""
    
    def __init__(
        self,
        settings_manager: SettingsManager,
        media_config: MediaConfig,
        job_manager: Optional[JobManager] = None,
        parent=None
    ):
        super().__init__(parent)
        
        self._settings_manager = settings_manager
        self._media_config = media_config
        self._job_manager = job_manager
        self._export_settings = ExportSettings()
        
        # Export state
        self._is_exporting = False
        self._worker: Optional[ExportWorker] = None
        self._worker_thread: Optional[QThread] = None
        
        self._setup_ui()
        self._apply_styles()
        self._load_default_preset()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Export Video - FFmpeg Exporter")
        self.setMinimumSize(600, 700)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Export Settings")
        title.setObjectName("dialogTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Hardware info
        self._hw_label = QLabel("Detected Hardware: Checking...")
        self._hw_label.setStyleSheet("color: #00d4ff; font-size: 11px;")
        layout.addWidget(self._hw_label)
        
        # Detect hardware
        self._detect_hardware()
        
        # Settings section
        settings_widget = self._create_settings_section()
        layout.addWidget(settings_widget)
        
        # Log output section
        log_group = self._create_log_section()
        layout.addWidget(log_group, 1)
        
        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.hide()
        layout.addWidget(self._progress_bar)
        
        # Buttons
        button_row = QHBoxLayout()
        
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedHeight(45)
        self._cancel_btn.clicked.connect(self._on_cancel)
        button_row.addWidget(self._cancel_btn)
        
        # ADD TO QUEUE button (NEW)
        self._queue_btn = QPushButton("📋 Add to Queue")
        self._queue_btn.setFixedHeight(45)
        self._queue_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B00;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF8500;
            }
        """)
        self._queue_btn.clicked.connect(self._add_to_queue)
        button_row.addWidget(self._queue_btn)
        
        self._export_btn = QPushButton("▶ EXPORT NOW")
        self._export_btn.setObjectName("exportButton")
        self._export_btn.setFixedHeight(45)
        self._export_btn.clicked.connect(self._start_export)
        button_row.addWidget(self._export_btn)
        
        layout.addLayout(button_row)
    
    def _create_settings_section(self) -> QWidget:
        """Create export settings section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Preset selection
        preset_label = QLabel("Preset")
        layout.addWidget(preset_label)
        
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(FFmpegBuilder.get_available_presets())
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        layout.addWidget(self._preset_combo)
        
        # Resolution and FPS row
        res_fps_row = QHBoxLayout()
        
        # Resolution
        res_col = QVBoxLayout()
        res_label = QLabel("Resolution")
        res_col.addWidget(res_label)
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems([
            "1920x1080", "2560x1440", "1280x720", "3840x2160", "1080x1920", "1080x1080"
        ])
        self._resolution_combo.setEditable(True)
        res_col.addWidget(self._resolution_combo)
        res_fps_row.addLayout(res_col)
        
        # FPS
        fps_col = QVBoxLayout()
        fps_label = QLabel("FPS")
        fps_col.addWidget(fps_label)
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 120)
        self._fps_spin.setValue(30)
        fps_col.addWidget(self._fps_spin)
        res_fps_row.addLayout(fps_col)
        
        layout.addLayout(res_fps_row)
        
        # Encoding Method section (GPU/CPU)
        method_label = QLabel("Metode Encoding Final")
        method_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(method_label)
        
        self._encoding_method_combo = QComboBox()
        self._encoding_method_combo.addItems([
            "copy = Cepat (Stream Copy)",
            "nvenc = GPU NVIDIA Fast",
            "nvenc_hq = GPU NVIDIA High Quality (Anti-glitch)",
            "x264 = CPU Standard",
            "x264_hq = CPU High Quality (Anti-glitch, lambat)",
        ])
        self._encoding_method_combo.setCurrentIndex(2)  # Default: nvenc_hq
        self._encoding_method_combo.currentIndexChanged.connect(self._on_encoding_method_changed)
        layout.addWidget(self._encoding_method_combo)
        
        # Method info label
        self._method_info_label = QLabel(
            "✓ Semua mode sudah dioptimalkan untuk livestreaming (keyframe ≤2 detik)\n"
            "⚡ Gunakan nvenc_hq untuk hasil terbaik dengan kecepatan tinggi (butuh GPU NVIDIA)"
        )
        self._method_info_label.setStyleSheet("color: #8892b0; font-size: 10px; margin-bottom: 5px;")
        self._method_info_label.setWordWrap(True)
        layout.addWidget(self._method_info_label)
        
        # Bitrate section (for non-copy modes)
        self._bitrate_widget = QWidget()
        bitrate_layout = QVBoxLayout(self._bitrate_widget)
        bitrate_layout.setContentsMargins(0, 0, 0, 0)
        
        bitrate_row = QHBoxLayout()
        bitrate_label = QLabel("Bitrate (kbps):")
        bitrate_row.addWidget(bitrate_label)
        self._bitrate_spin = QSpinBox()
        self._bitrate_spin.setRange(500, 100000)
        self._bitrate_spin.setValue(8000)
        bitrate_row.addWidget(self._bitrate_spin)
        bitrate_row.addStretch()
        bitrate_layout.addLayout(bitrate_row)
        
        layout.addWidget(self._bitrate_widget)
        
        # Destination section
        dest_label = QLabel("Destination")
        dest_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(dest_label)
        
        # Filename
        filename_label = QLabel("Filename")
        layout.addWidget(filename_label)
        
        self._filename_edit = QLineEdit()
        default_name = f"Export_{int(time.time())}"
        self._filename_edit.setText(default_name)
        layout.addWidget(self._filename_edit)
        
        # Folder
        folder_label = QLabel("Folder")
        layout.addWidget(folder_label)
        
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit()
        last_dir = self._settings_manager.settings.last_output_dir
        self._folder_edit.setText(last_dir if last_dir else os.path.expanduser("~"))
        self._folder_edit.setReadOnly(True)
        folder_row.addWidget(self._folder_edit)
        
        folder_btn = QPushButton("...")
        folder_btn.setFixedWidth(40)
        folder_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(folder_btn)
        layout.addLayout(folder_row)
        
        return widget
    
    def _create_log_section(self) -> QGroupBox:
        """Create FFmpeg log output section."""
        group = QGroupBox("FFmpeg Output")
        layout = QVBoxLayout(group)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a14;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #0f3460;
                border-radius: 5px;
            }
        """)
        self._log_text.setPlaceholderText("FFmpeg output will appear here...")
        layout.addWidget(self._log_text)
        
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
            
            QLineEdit, QSpinBox, QComboBox {
                background-color: #0f3460;
                color: white;
                border: 1px solid #1a4f7a;
                border-radius: 5px;
                padding: 8px;
                min-height: 20px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #00d4ff;
            }
            
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
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
                padding: 10px 20px;
            }
            
            QPushButton:hover {
                background-color: #1a4f7a;
            }
            
            #exportButton {
                background-color: #00d4ff;
                color: #16213e;
                font-weight: bold;
            }
            
            #exportButton:hover {
                background-color: #00b8e6;
            }
            
            #exportButton:disabled {
                background-color: #4a5568;
                color: #8892b0;
            }
            
            QProgressBar {
                background-color: #0f3460;
                border: none;
                border-radius: 5px;
                height: 20px;
                text-align: center;
            }
            
            QProgressBar::chunk {
                background-color: #00d4ff;
                border-radius: 5px;
            }
        """)
    
    def _detect_hardware(self) -> None:
        """Detect available hardware encoders."""
        ffmpeg_path = self._settings_manager.get_ffmpeg_path()
        if not ffmpeg_path:
            self._hw_label.setText("⚠️ FFmpeg not configured")
            return
        
        try:
            # Check for NVIDIA GPU support
            result = subprocess.run(
                [ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            encoders = result.stdout.lower()
            hardware = []
            
            if 'h264_nvenc' in encoders:
                hardware.append("NVIDIA (NVENC)")
            if 'h264_amf' in encoders:
                hardware.append("AMD (AMF)")
            if 'h264_qsv' in encoders:
                hardware.append("Intel (QSV)")
            
            if hardware:
                self._hw_label.setText(f"✓ Detected Hardware: {' + '.join(hardware)}")
                self._hw_label.setStyleSheet("color: #00ff00; font-size: 11px;")
            else:
                self._hw_label.setText("ℹ️ No GPU encoder detected - CPU mode only")
                self._hw_label.setStyleSheet("color: #ffaa00; font-size: 11px;")
                # Default to CPU encoding
                self._encoding_method_combo.setCurrentIndex(3)  # x264
        
        except Exception as e:
            self._hw_label.setText(f"⚠️ Could not detect hardware: {str(e)[:30]}")
            self._hw_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
    
    def _load_default_preset(self) -> None:
        """Load default preset settings."""
        preset = FFmpegBuilder.get_preset_settings("YouTube 1080p (FHD)")
        self._apply_preset_settings(preset)
    
    def _on_preset_changed(self, preset_name: str) -> None:
        """Handle preset selection change."""
        preset = FFmpegBuilder.get_preset_settings(preset_name)
        self._apply_preset_settings(preset)
    
    def _apply_preset_settings(self, settings: ExportSettings) -> None:
        """Apply preset settings to UI."""
        self._resolution_combo.setCurrentText(f"{settings.width}x{settings.height}")
        self._fps_spin.setValue(settings.fps)
        self._bitrate_spin.setValue(settings.bitrate_kbps)
    
    def _on_encoding_method_changed(self, index: int) -> None:
        """Handle encoding method change."""
        # Hide bitrate for copy mode
        if index == 0:  # copy
            self._bitrate_widget.hide()
            self._method_info_label.setText(
                "⚡ Mode tercepat - tidak ada encoding ulang\n"
                "⚠️ Hanya bisa digunakan jika format input sama dengan output"
            )
        elif index == 1:  # nvenc
            self._bitrate_widget.show()
            self._method_info_label.setText(
                "🎮 GPU NVIDIA Fast - encoding cepat dengan kualitas baik\n"
                "⚡ Cocok untuk export cepat atau livestreaming"
            )
        elif index == 2:  # nvenc_hq
            self._bitrate_widget.show()
            self._method_info_label.setText(
                "🎮 GPU NVIDIA High Quality - encoding berkualitas tinggi\n"
                "✓ Anti-glitch dengan B-frames, cocok untuk YouTube/hasil akhir"
            )
        elif index == 3:  # x264
            self._bitrate_widget.show()
            self._method_info_label.setText(
                "💻 CPU Standard - encoding dengan CPU\n"
                "✓ Kompatibilitas tinggi, tidak butuh GPU NVIDIA"
            )
        else:  # x264_hq
            self._bitrate_widget.show()
            self._method_info_label.setText(
                "💻 CPU High Quality - kualitas terbaik tapi lambat\n"
                "✓ Anti-glitch, cocok untuk hasil akhir berkualitas tinggi"
            )
    
    def _browse_folder(self) -> None:
        """Browse for output folder."""
        current = self._folder_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", current
        )
        if directory:
            self._folder_edit.setText(directory)
            self._settings_manager.update(last_output_dir=directory)
    
    def _collect_export_settings(self) -> ExportSettings:
        """Collect export settings from UI."""
        settings = ExportSettings()
        
        # Resolution
        resolution = self._resolution_combo.currentText()
        try:
            parts = resolution.split('x')
            settings.width = int(parts[0])
            settings.height = int(parts[1])
        except (IndexError, ValueError):
            settings.width = 1920
            settings.height = 1080
        
        # FPS
        settings.fps = self._fps_spin.value()
        
        # Encoding method
        method_map = {
            0: EncodingMethod.COPY,
            1: EncodingMethod.NVENC,
            2: EncodingMethod.NVENC_HQ,
            3: EncodingMethod.X264,
            4: EncodingMethod.X264_HQ
        }
        settings.encoding_method = method_map.get(
            self._encoding_method_combo.currentIndex(), 
            EncodingMethod.NVENC_HQ
        )
        
        # Bitrate
        settings.bitrate_kbps = self._bitrate_spin.value()
        
        # Output
        filename = self._filename_edit.text().strip()
        if not filename:
            filename = f"Export_{int(time.time())}"
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        settings.output_filename = filename
        settings.output_directory = self._folder_edit.text()
        
        return settings
    
    def _start_export(self) -> None:
        """Start the export process."""
        if self._is_exporting:
            return
        
        # Collect settings
        export_settings = self._collect_export_settings()
        
        # Validate output directory
        if not os.path.isdir(export_settings.output_directory):
            QMessageBox.warning(
                self, "Invalid Directory",
                "The output directory does not exist."
            )
            return
        
        # Check if file exists
        if os.path.exists(export_settings.output_path):
            result = QMessageBox.question(
                self, "File Exists",
                f"The file '{export_settings.output_filename}' already exists.\nDo you want to overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return
        
        # Build FFmpeg command
        builder = FFmpegBuilder(
            self._settings_manager.get_ffmpeg_path(),
            self._settings_manager.get_ffprobe_path()
        )
        
        try:
            command, temp_files = builder.build_command(
                self._media_config,
                export_settings
            )
        except ValueError as e:
            QMessageBox.critical(
                self, "Export Error",
                f"Failed to build export command:\n{str(e)}"
            )
            return
        
        # Start export
        self._is_exporting = True
        self._export_btn.setEnabled(False)
        self._export_btn.setText("Exporting...")
        self._cancel_btn.setText("Cancel Export")
        self._progress_bar.show()
        self._progress_bar.setValue(0)
        self._log_text.clear()
        
        # Create worker and thread
        self._worker = ExportWorker(command, temp_files)
        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        
        # Connect signals
        self._worker_thread.started.connect(self._worker.run)
        self._worker.log_output.connect(self._on_log_output)
        self._worker.progress_update.connect(self._on_progress_update)
        self._worker.export_finished.connect(self._on_export_finished)
        
        # Start thread
        self._worker_thread.start()
    
    def _on_log_output(self, text: str) -> None:
        """Handle log output from worker."""
        self._log_text.moveCursor(QTextCursor.MoveOperation.End)
        self._log_text.insertPlainText(text)
        self._log_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def _on_progress_update(self, progress: int) -> None:
        """Handle progress update from worker."""
        self._progress_bar.setValue(progress)
    
    def _on_export_finished(self, success: bool, message: str) -> None:
        """Handle export completion."""
        self._is_exporting = False
        self._export_btn.setEnabled(True)
        self._export_btn.setText("EXPORT VIDEO")
        self._cancel_btn.setText("Close")
        
        # Cleanup thread
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait()
            self._worker_thread = None
            self._worker = None
        
        if success:
            self._progress_bar.setValue(100)
            QMessageBox.information(
                self, "Export Complete",
                message
            )
        else:
            QMessageBox.warning(
                self, "Export Failed",
                message
            )
    
    def _add_to_queue(self) -> None:
        """Add current settings to export queue."""
        from core.queue_manager import QueueManager
        
        # Validate settings
        if not self._validate_settings():
            return
        
        # Get export settings
        export_settings = self._get_export_settings()
        if not export_settings:
            return
        
        # Ask for job name
        from PySide6.QtWidgets import QInputDialog
        job_name, ok = QInputDialog.getText(
            self,
            "Job Name",
            "Enter a name for this export job:",
            text=f"Export_{datetime.now().strftime('%H%M%S')}"
        )
        
        if not ok or not job_name:
            return
        
        # Add to queue
        queue_manager = QueueManager()
        job = queue_manager.add_job(self._media_config, export_settings, job_name)
        
        # Show success message
        QMessageBox.information(
            self,
            "Added to Queue",
            f"Job '{job.name}' has been added to export queue.\n\n"
            f"Open Queue Panel to start processing."
        )
    
    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if self._is_exporting:
            result = QMessageBox.question(
                self, "Cancel Export",
                "Are you sure you want to cancel the export?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.Yes:
                if self._worker:
                    self._worker.cancel()
        else:
            self.close()
    
    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        if self._is_exporting:
            event.ignore()
            self._on_cancel()
        else:
            # Cleanup
            if self._worker_thread:
                self._worker_thread.quit()
                self._worker_thread.wait()
            event.accept()
