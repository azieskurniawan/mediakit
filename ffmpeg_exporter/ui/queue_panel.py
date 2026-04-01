"""
Export Queue Panel UI
Shows and manages export queue with batch processing control.
"""

import os
import subprocess
import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QProgressBar, QMessageBox,
    QDialog, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QColor

from core.queue_manager import QueueManager, ExportJob, JobStatus
from core.ffmpeg_builder import FFmpegBuilder
import subprocess
import threading


class QueuePanel(QDialog):
    """Panel for managing export queue (as standalone dialog)."""
    
    # Signals for thread-safe UI updates
    queue_changed = Signal()
    job_progress_changed = Signal(str, float)  # job_id, progress
    current_job_changed = Signal(str)  # job_name
    queue_stopped = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Queue")
        self.resize(900, 600)
        self.setModal(False)  # Non-modal so user can interact with main window
        
        # Queue manager (singleton)
        self.queue_manager = QueueManager()
        
        # Processing state
        self.is_processing = False
        self.current_process = None
        self.processing_thread = None
        
        # Setup UI
        self._init_ui()
        
        # Connect signals to slots (thread-safe!)
        self.job_progress_changed.connect(self._update_progress_bar)
        self.current_job_changed.connect(self._update_current_job_label)
        self.queue_stopped.connect(self._on_queue_stopped)
        self.queue_changed.connect(self._refresh_table)  # Connect our signal to refresh
        
        # Setup callbacks - wrap in signal emits for thread safety
        self.queue_manager.set_on_queue_changed(lambda: self.queue_changed.emit())
        self.queue_manager.set_on_job_started(self._on_job_started)
        self.queue_manager.set_on_job_progress(self._on_job_progress)
        self.queue_manager.set_on_job_completed(self._on_job_completed)
        self.queue_manager.set_on_job_failed(self._on_job_failed)
        self.queue_manager.set_on_queue_finished(self._on_queue_finished)
        
        # Timer to update UI periodically
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(500)  # Update every 500ms
        
        # Initial refresh - defer to main event loop to avoid threading issues
        QTimer.singleShot(0, self._refresh_table)
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # === Header with stats ===
        header_group = QGroupBox("Queue Status")
        header_layout = QHBoxLayout()
        
        self.pending_label = QLabel("⏳ Pending: 0")
        self.pending_label.setStyleSheet("color: #ffa500; font-weight: bold; font-size: 13px;")
        
        self.processing_label = QLabel("⚙ Processing: 0")
        self.processing_label.setStyleSheet("color: #00bfff; font-weight: bold; font-size: 13px;")
        
        self.completed_label = QLabel("✅ Completed: 0")
        self.completed_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 13px;")
        
        self.failed_label = QLabel("❌ Failed: 0")
        self.failed_label.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 13px;")
        
        header_layout.addWidget(self.pending_label)
        header_layout.addWidget(self.processing_label)
        header_layout.addWidget(self.completed_label)
        header_layout.addWidget(self.failed_label)
        header_layout.addStretch()
        
        header_group.setLayout(header_layout)
        header_group.setStyleSheet("""
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #3e3e3e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(header_group)
        
        # === Queue Table ===
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Status", "Name", "Resolution", "Output", "Progress", "Created", "Actions"
        ])
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Resolution
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Output
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Progress
        header.setMinimumSectionSize(150)
        self.table.setColumnWidth(4, 150)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Created
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Actions
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        
        # Set explicit styling for text visibility
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                gridline-color: #3e3e3e;
                border: 1px solid #3e3e3e;
            }
            QTableWidget::item {
                padding: 5px;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTableWidget::item:alternate {
                background-color: #252525;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 5px;
                border: 1px solid #3e3e3e;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
        # === Current Job Progress ===
        progress_group = QGroupBox("Current Job")
        progress_layout = QVBoxLayout()
        
        self.current_job_label = QLabel("No job processing")
        self.current_job_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        
        self.current_progress_bar = QProgressBar()
        self.current_progress_bar.setRange(0, 100)
        self.current_progress_bar.setValue(0)
        self.current_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3e3e3e;
                border-radius: 3px;
                text-align: center;
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
        """)
        
        progress_layout.addWidget(self.current_job_label)
        progress_layout.addWidget(self.current_progress_bar)
        
        progress_group.setLayout(progress_layout)
        progress_group.setStyleSheet("""
            QGroupBox {
                color: #e0e0e0;
                border: 1px solid #3e3e3e;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        layout.addWidget(progress_group)
        
        # === Control Buttons ===
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Start Queue")
        self.start_button.clicked.connect(self._start_queue)
        self.start_button.setMinimumHeight(40)
        
        self.stop_button = QPushButton("⏸ Stop Queue")
        self.stop_button.clicked.connect(self._stop_queue)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(40)
        
        self.clear_button = QPushButton("🗑 Clear Completed")
        self.clear_button.clicked.connect(self._clear_completed)
        self.clear_button.setMinimumHeight(40)
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._refresh_table)
        self.refresh_button.setMinimumHeight(40)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.refresh_button)
        
        layout.addLayout(button_layout)
    
    def showEvent(self, event):
        """Called when dialog is shown. Force refresh to show current queue."""
        super().showEvent(event)
        # Force refresh when dialog opens (after UI is ready)
        QTimer.singleShot(100, self._refresh_table)
        QTimer.singleShot(100, self._update_stats)
    
    @Slot()
    def _refresh_table(self):
        """Refresh table with current queue."""
        # Get jobs with ultimate safety - validate each job individually
        jobs = []
        try:
            jobs_raw = self.queue_manager.get_jobs()
            # Validate each job individually
            for j in jobs_raw:
                try:
                    # Test if accessible without causing recursion
                    _ = j.id
                    jobs.append(j)
                except:
                    # Skip corrupt job
                    continue
        except:
            jobs = []
        
        # Set row count
        try:
            self.table.setRowCount(len(jobs))
        except:
            try:
                self.table.setRowCount(0)
            except:
                pass
            return
        
        # Render each row
        for row, job in enumerate(jobs):
            try:
                # Status icon
                status_item = QTableWidgetItem(self._get_status_icon(job.status))
                try:
                    status_item.setTextAlignment(Qt.AlignCenter)
                except:
                    pass
                self.table.setItem(row, 0, status_item)
                
                # Name
                try:
                    name_item = QTableWidgetItem(str(job.name))
                    self.table.setItem(row, 1, name_item)
                except:
                    self.table.setItem(row, 1, QTableWidgetItem("???"))
                
                # Resolution
                try:
                    resolution = f"{job.export_settings.width}x{job.export_settings.height} @ {job.export_settings.fps}fps"
                    resolution_item = QTableWidgetItem(resolution)
                    self.table.setItem(row, 2, resolution_item)
                except:
                    self.table.setItem(row, 2, QTableWidgetItem("???"))
                
                # Output path (SAFE - don't use property)
                try:
                    # Manually construct path to avoid property getter
                    output_path = f"{job.export_settings.output_directory}/{job.export_settings.output_filename}"
                    output_item = QTableWidgetItem(output_path)
                    output_item.setToolTip(output_path)
                    self.table.setItem(row, 3, output_item)
                except:
                    self.table.setItem(row, 3, QTableWidgetItem("???"))
                
                # Progress bar
                try:
                    progress_widget = QProgressBar()
                    progress_widget.setRange(0, 100)
                    progress_widget.setValue(int(job.progress))
                    progress_widget.setFormat(f"{job.progress:.1f}%")
                    self.table.setCellWidget(row, 4, progress_widget)
                except:
                    pass
                
                # Created time
                try:
                    created_time = job.created_time.split('T')[0] if 'T' in str(job.created_time) else str(job.created_time)
                    time_item = QTableWidgetItem(created_time)
                    self.table.setItem(row, 5, time_item)
                except:
                    self.table.setItem(row, 5, QTableWidgetItem("???"))
                
                # Actions buttons
                try:
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2, 2, 2, 2)
                    
                    # Remove button
                    remove_btn = QPushButton("❌")
                    remove_btn.setMaximumWidth(40)
                    remove_btn.setToolTip("Remove from queue")
                    remove_btn.clicked.connect(lambda checked, j=job: self._remove_job(j.id))
                    
                    # Details button
                    details_btn = QPushButton("ℹ")
                    details_btn.setMaximumWidth(40)
                    details_btn.setToolTip("View details")
                    details_btn.clicked.connect(lambda checked, j=job: self._show_job_details(j))
                    
                    actions_layout.addWidget(remove_btn)
                    actions_layout.addWidget(details_btn)
                    
                    self.table.setCellWidget(row, 6, actions_widget)
                except:
                    pass
                
                # Color row based on status
                try:
                    self._set_row_color(row, job.status)
                except:
                    pass
                    
            except:
                # Skip this entire row if any error
                continue
        
        # Always update stats after refresh
        try:
            self._update_stats()
        except:
            pass
    
    def _get_status_icon(self, status) -> str:
        """Get emoji icon for status. Ultra-safe against recursion."""
        # Multiple fallback strategies
        status_str = None
        
        # Strategy 1: Get .value
        try:
            if hasattr(status, 'value'):
                status_str = str(status.value)
        except:
            pass
        
        # Strategy 2: Direct string conversion
        if not status_str:
            try:
                status_str = str(status)
            except:
                pass
        
        # Strategy 3: Check type name
        if not status_str:
            try:
                status_str = type(status).__name__.lower()
            except:
                return "❓"
        
        # Map to icons
        icon_map = {
            'pending': '⏳',
            'processing': '⚙️',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }
        return icon_map.get(status_str, "❓")
    
    def _set_row_color(self, row: int, status):
        """Set row background color based on status. Ultra-safe against recursion."""
        # Multiple fallback strategies
        status_str = None
        
        # Strategy 1: Get .value
        try:
            if hasattr(status, 'value'):
                status_str = str(status.value)
        except:
            pass
        
        # Strategy 2: Direct string conversion
        if not status_str:
            try:
                status_str = str(status)
            except:
                pass
        
        # Strategy 3: Use default
        if not status_str:
            status_str = "unknown"
        
        # Map by string value
        color_map = {
            "pending": QColor(240, 240, 240),
            "processing": QColor(255, 255, 200),
            "completed": QColor(200, 255, 200),
            "failed": QColor(255, 200, 200),
            "cancelled": QColor(220, 220, 220)
        }
        
        color = color_map.get(status_str, QColor(255, 255, 255))
        
        try:
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(color)
        except:
            pass  # Silently ignore color setting errors
    
    def _update_stats(self):
        """Update statistics labels."""
        pending = processing = completed = failed = 0
        
        try:
            jobs = self.queue_manager.get_jobs()
        except:
            jobs = []
        
        # Safe status value extraction with multiple fallback strategies
        for job in jobs:
            try:
                status = job.status
                # Multiple strategies to get status value
                status_str = None
                
                # Strategy 1: Get .value
                try:
                    if hasattr(status, 'value'):
                        status_str = str(status.value)
                except:
                    pass
                
                # Strategy 2: Direct string conversion
                if not status_str:
                    try:
                        status_str = str(status)
                    except:
                        pass
                
                # Count by status
                if status_str == 'pending':
                    pending += 1
                elif status_str == 'processing':
                    processing += 1
                elif status_str == 'completed':
                    completed += 1
                elif status_str == 'failed':
                    failed += 1
            except:
                # Skip corrupt job
                continue
        
        # Update labels
        self.pending_label.setText(f"⏳ Pending: {pending}")
        self.processing_label.setText(f"⚙️ Processing: {processing}")
        self.completed_label.setText(f"✅ Completed: {completed}")
        self.failed_label.setText(f"❌ Failed: {failed}")
    
    def _update_ui(self):
        """Periodic UI update."""
        current_job = self.queue_manager.get_current_job()
        
        if current_job:
            self.current_job_label.setText(f"Processing: {current_job.name}")
            self.current_progress_bar.setValue(int(current_job.progress))
        else:
            self.current_job_label.setText("No job processing")
            self.current_progress_bar.setValue(0)
    
    def _start_queue(self):
        """Start processing queue."""
        if self.is_processing:
            return
        
        pending_count = self.queue_manager.get_pending_count()
        if pending_count == 0:
            QMessageBox.information(self, "Queue Empty", "No pending jobs in queue.")
            return
        
        self.is_processing = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Start processing in background thread
        self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.processing_thread.start()
    
    def _stop_queue(self):
        """Stop processing queue."""
        if not self.is_processing:
            return
        
        reply = QMessageBox.question(
            self,
            "Stop Queue",
            "Stop processing queue? Current job will be cancelled.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.is_processing = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Kill current process if running
            if self.current_process:
                try:
                    self.current_process.kill()
                except:
                    pass
    
    def _process_queue(self):
        """Process all pending jobs sequentially (runs in background thread)."""
        try:
            from core.settings_manager import SettingsManager
            
            print("[QUEUE] Starting queue processing...")
            settings_manager = SettingsManager()
            ffmpeg_path = settings_manager.get_ffmpeg_path()
            ffprobe_path = settings_manager.get_ffprobe_path()
            
            jobs = self.queue_manager.get_jobs()
            print(f"[QUEUE] Found {len(jobs)} total jobs")
            
            for job in jobs:
                if not self.is_processing:
                    print("[QUEUE] Processing stopped by user")
                    break
                
                if job.status != JobStatus.PENDING:
                    continue
                
                print(f"[QUEUE] Processing job: {job.name}")
                
                # Mark as started (DON'T save queue yet to avoid widget creation in bg thread)
                job.status = JobStatus.PROCESSING
                job.started_time = datetime.now().isoformat()
                
                try:
                    # Build FFmpeg command (SIMPLE!)
                    print(f"[QUEUE] Building FFmpeg command...")
                    builder = FFmpegBuilder(ffmpeg_path, ffprobe_path)
                    command, temp_files = builder.build_command(
                        job.media_config,
                        job.export_settings
                    )
                    
                    print(f"[QUEUE] Executing FFmpeg...")
                    # Execute FFmpeg (SIMPLE!)
                    success = self._execute_ffmpeg(command, job)
                    
                    print(f"[QUEUE] FFmpeg finished: success={success}")
                    
                    # Cleanup temp files
                    for temp_file in temp_files:
                        try:
                            if os.path.exists(temp_file):
                                os.remove(temp_file)
                        except:
                            pass
                    
                    # Mark result (DON'T save yet to avoid bg thread widget creation)
                    if success and self.is_processing:
                        job.status = JobStatus.COMPLETED
                        job.progress = 100.0
                        job.finished_time = datetime.now().isoformat()
                        # Emit signal to refresh UI
                        self.queue_changed.emit()
                    elif not self.is_processing:
                        job.status = JobStatus.FAILED
                        job.error_message = "Cancelled by user"
                        job.finished_time = datetime.now().isoformat()
                        # Emit signal to refresh UI
                        self.queue_changed.emit()
                    
                except Exception as e:
                    print(f"[QUEUE] Error processing job: {e}")
                    import traceback
                    traceback.print_exc()
                    job.status = JobStatus.FAILED
                    job.error_message = str(e)
                    job.finished_time = datetime.now().isoformat()
                    # Emit signal to refresh UI
                    self.queue_changed.emit()
            
            print("[QUEUE] Queue processing finished")
        except Exception as e:
            print(f"[QUEUE] FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Save queue state (no callbacks triggered)
            try:
                self.queue_manager.save_queue()
            except:
                pass
            
            # Queue finished
            self.is_processing = False
            self.queue_stopped.emit()  # Thread-safe signal!
    
    @Slot()
    def _on_queue_stopped(self):
        """Called when queue stops (runs in main thread)."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.current_job_label.setText("No job processing")
        self.current_progress_bar.setValue(0)
        
        # Force refresh table to show updated statuses
        self._refresh_table()
    
    def _execute_ffmpeg(self, command: list, job: ExportJob) -> bool:
        """Execute FFmpeg command and track progress. Returns True if successful."""
        import re
        
        # Emit signal to update UI (thread-safe!)
        self.current_job_changed.emit(job.name)
        
        self.current_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        duration = None
        last_progress = 0
        
        # Parse output for progress
        for line in self.current_process.stdout:
            if not self.is_processing:
                self.current_process.kill()
                break
            
            # Extract duration
            if duration is None:
                duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                if duration_match:
                    h, m, s = duration_match.groups()
                    duration = int(h) * 3600 + int(m) * 60 + float(s)
            
            # Extract progress
            time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
            if time_match and duration:
                h, m, s = time_match.groups()
                current_time = int(h) * 3600 + int(m) * 60 + float(s)
                progress = min(100.0, (current_time / duration) * 100)
                
                # Only update if changed significantly
                if progress - last_progress >= 0.5:
                    last_progress = progress
                    self.queue_manager.update_job_progress(job.id, progress)
                    
                    # Emit signal to update progress bar (thread-safe!)
                    self.job_progress_changed.emit(job.id, progress)
        
        # Wait for completion
        self.current_process.wait()
        exit_code = self.current_process.returncode
        self.current_process = None
        
        return exit_code == 0
    
    # Thread-safe slot methods (called via signals)
    @Slot(str, float)
    def _update_progress_bar(self, job_id: str, progress: float):
        """Update progress bar (called from signal in main thread)."""
        self.current_progress_bar.setValue(int(progress))
    
    @Slot(str)
    def _update_current_job_label(self, job_name: str):
        """Update current job label (called from signal in main thread)."""
        self.current_job_label.setText(f"Processing: {job_name}")
    
    def _remove_job(self, job_id: str):
        """Remove job from queue."""
        success = self.queue_manager.remove_job(job_id)
        
        if not success:
            QMessageBox.warning(
                self,
                "Cannot Remove",
                "Cannot remove job that is currently processing."
            )
        else:
            self._refresh_table()
    
    def _clear_completed(self):
        """Clear all completed/failed jobs."""
        self.queue_manager.clear_completed()
        self._refresh_table()
    
    def _show_job_details(self, job: ExportJob):
        """Show detailed job information."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Job Details: {job.name}")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Details text
        details = QTextEdit()
        details.setReadOnly(True)
        
        details_text = f"""
<h3>Job Information</h3>
<b>ID:</b> {job.id}<br>
<b>Name:</b> {job.name}<br>
<b>Status:</b> {job.status.value}<br>
<b>Progress:</b> {job.progress:.1f}%<br>
<br>
<h3>Export Settings</h3>
<b>Output:</b> {job.export_settings.output_path}<br>
<b>Resolution:</b> {job.export_settings.width}x{job.export_settings.height}<br>
<b>FPS:</b> {job.export_settings.fps}<br>
<b>Video Codec:</b> {job.export_settings.video_codec.value}<br>
<b>Bitrate:</b> {job.export_settings.bitrate_kbps} kbps<br>
<b>Audio Codec:</b> {job.export_settings.audio_codec.value}<br>
<b>Audio Bitrate:</b> {job.export_settings.audio_bitrate_kbps} kbps<br>
<br>
<h3>Timing</h3>
<b>Created:</b> {job.created_time}<br>
<b>Started:</b> {job.started_time or 'Not started'}<br>
<b>Finished:</b> {job.finished_time or 'Not finished'}<br>
"""
        
        if job.error_message:
            details_text += f"<br><h3 style='color: red;'>Error</h3><pre>{job.error_message}</pre>"
        
        details.setHtml(details_text)
        layout.addWidget(details)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _on_job_started(self, job: ExportJob):
        """Callback when job starts."""
        self._refresh_table()
    
    def _on_job_progress(self, job: ExportJob):
        """Callback for job progress."""
        # Table will be updated by periodic timer
        pass
    
    def _on_job_completed(self, job: ExportJob):
        """Callback when job completes."""
        self._refresh_table()
    
    def _on_job_failed(self, job: ExportJob):
        """Callback when job fails."""
        self._refresh_table()
        QMessageBox.critical(
            self,
            "Job Failed",
            f"Job '{job.name}' failed:\n{job.error_message}"
        )
    
    def _on_queue_finished(self):
        """Callback when entire queue finishes."""
        QMessageBox.information(
            self,
            "Queue Finished",
            "All jobs in queue have been processed!"
        )
