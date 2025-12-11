"""
Job Monitor Window - Shows active and completed jobs.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QGroupBox, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from datetime import datetime

from core.job_manager import JobManager, JobType, JobStatus


class JobMonitorWindow(QDialog):
    """Window for monitoring active and historical jobs."""
    
    # Signal emitted when window is closed
    closed = Signal()
    
    def __init__(self, job_manager: JobManager, parent=None):
        super().__init__(parent)
        self._job_manager = job_manager
        self._selected_job_id = None
        self._setup_ui()
        self._connect_signals()
        self._start_update_timer()
        self._refresh_job_list()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Job Monitor - MediaKit Pro")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 Active Jobs")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00d4ff;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_job_list)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Splitter for job list and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Job list
        job_list_widget = self._create_job_list_widget()
        splitter.addWidget(job_list_widget)
        
        # Job details/logs
        job_details_widget = self._create_job_details_widget()
        splitter.addWidget(job_details_widget)
        
        splitter.setSizes([300, 300])
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._cancel_btn = QPushButton("⏹ Stop Job")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_selected_job)
        button_layout.addWidget(self._cancel_btn)
        
        self._remove_btn = QPushButton("🗑 Remove")
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._remove_selected_job)
        button_layout.addWidget(self._remove_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dark theme
        self._apply_styles()
    
    def _create_job_list_widget(self) -> QGroupBox:
        """Create job list widget."""
        group = QGroupBox("Jobs")
        layout = QVBoxLayout()
        
        # Tree widget for jobs
        self._job_tree = QTreeWidget()
        self._job_tree.setHeaderLabels(["Type", "Name", "Status", "Duration", "Started"])
        self._job_tree.setColumnWidth(0, 80)
        self._job_tree.setColumnWidth(1, 200)
        self._job_tree.setColumnWidth(2, 120)
        self._job_tree.setColumnWidth(3, 100)
        self._job_tree.itemSelectionChanged.connect(self._on_job_selection_changed)
        self._job_tree.setAlternatingRowColors(True)
        layout.addWidget(self._job_tree)
        
        # Stats label
        self._stats_label = QLabel("Total: 0 | Running: 0 | Completed: 0 | Failed: 0")
        self._stats_label.setStyleSheet("color: #8892b0; font-size: 11px; padding: 5px;")
        layout.addWidget(self._stats_label)
        
        group.setLayout(layout)
        return group
    
    def _create_job_details_widget(self) -> QGroupBox:
        """Create job details widget."""
        group = QGroupBox("Job Details / Live Logs")
        layout = QVBoxLayout()
        
        # Log text area
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setPlaceholderText("Select a job to view details and logs...")
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f1419;
                color: #e6e1cf;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #0f3460;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self._log_text)
        
        group.setLayout(layout)
        return group
    
    def _connect_signals(self) -> None:
        """Connect job manager signals."""
        self._job_manager.job_added.connect(self._on_job_added)
        self._job_manager.job_started.connect(self._on_job_started)
        self._job_manager.job_progress.connect(self._on_job_progress)
        self._job_manager.job_completed.connect(self._on_job_completed)
        self._job_manager.job_failed.connect(self._on_job_failed)
        self._job_manager.job_cancelled.connect(self._on_job_cancelled)
    
    def _start_update_timer(self) -> None:
        """Start timer to update job durations."""
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_job_durations)
        self._update_timer.start(1000)  # Update every second
    
    def _refresh_job_list(self) -> None:
        """Refresh the job list."""
        self._job_tree.clear()
        
        jobs = self._job_manager.get_all_jobs()
        
        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        # Add to tree
        for job in jobs:
            self._add_job_to_tree(job)
        
        # Update stats
        self._update_stats()
    
    def _add_job_to_tree(self, job) -> None:
        """Add a job to the tree widget."""
        item = QTreeWidgetItem()
        
        # Type icon
        type_icon = "🎥" if job.type == JobType.EXPORT else "🔴"
        item.setText(0, f"{type_icon} {job.type.value.upper()}")
        
        # Name
        item.setText(1, job.name)
        
        # Status with color
        status_text = job.get_status_display()
        item.setText(2, status_text)
        
        # Set row color based on status
        if job.status == JobStatus.RUNNING:
            for i in range(5):
                item.setForeground(i, Qt.GlobalColor.green)
        elif job.status == JobStatus.COMPLETED:
            for i in range(5):
                item.setForeground(i, Qt.GlobalColor.white)
        elif job.status == JobStatus.FAILED:
            for i in range(5):
                item.setForeground(i, Qt.GlobalColor.red)
        elif job.status == JobStatus.CANCELLED:
            for i in range(5):
                item.setForeground(i, Qt.GlobalColor.yellow)
        
        # Duration
        duration = job.get_duration()
        if duration:
            mins, secs = divmod(int(duration), 60)
            hours, mins = divmod(mins, 60)
            if hours > 0:
                item.setText(3, f"{hours}h {mins}m {secs}s")
            else:
                item.setText(3, f"{mins}m {secs}s")
        else:
            item.setText(3, "-")
        
        # Started time
        if job.started_at:
            time_str = job.started_at.strftime("%H:%M:%S")
            item.setText(4, time_str)
        else:
            item.setText(4, "Not started")
        
        # Store job ID in item data
        item.setData(0, Qt.ItemDataRole.UserRole, job.id)
        
        self._job_tree.addTopLevelItem(item)
    
    def _update_job_durations(self) -> None:
        """Update duration display for running jobs."""
        for i in range(self._job_tree.topLevelItemCount()):
            item = self._job_tree.topLevelItem(i)
            job_id = item.data(0, Qt.ItemDataRole.UserRole)
            job = self._job_manager.get_job(job_id)
            
            if job and job.status == JobStatus.RUNNING:
                duration = job.get_duration()
                if duration:
                    mins, secs = divmod(int(duration), 60)
                    hours, mins = divmod(mins, 60)
                    if hours > 0:
                        item.setText(3, f"{hours}h {mins}m {secs}s")
                    else:
                        item.setText(3, f"{mins}m {secs}s")
                
                # Update status text
                item.setText(2, job.get_status_display())
    
    def _update_stats(self) -> None:
        """Update statistics label."""
        jobs = self._job_manager.get_all_jobs()
        total = len(jobs)
        running = sum(1 for j in jobs if j.status == JobStatus.RUNNING)
        completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
        failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
        
        self._stats_label.setText(
            f"Total: {total} | Running: {running} | Completed: {completed} | Failed: {failed}"
        )
    
    def _on_job_selection_changed(self) -> None:
        """Handle job selection change."""
        selected_items = self._job_tree.selectedItems()
        
        if not selected_items:
            self._selected_job_id = None
            self._log_text.clear()
            self._cancel_btn.setEnabled(False)
            self._remove_btn.setEnabled(False)
            return
        
        item = selected_items[0]
        job_id = item.data(0, Qt.ItemDataRole.UserRole)
        self._selected_job_id = job_id
        
        job = self._job_manager.get_job(job_id)
        if job:
            # Update log display
            self._update_log_display(job)
            
            # Update button states
            self._cancel_btn.setEnabled(job.status == JobStatus.RUNNING)
            self._remove_btn.setEnabled(job.status != JobStatus.RUNNING)
    
    def _update_log_display(self, job) -> None:
        """Update the log display for selected job."""
        log_lines = []
        
        # Job info
        log_lines.append(f"{'='*60}")
        log_lines.append(f"Job ID: {job.id}")
        log_lines.append(f"Type: {job.type.value.upper()}")
        log_lines.append(f"Name: {job.name}")
        log_lines.append(f"Status: {job.status.value.upper()}")
        log_lines.append(f"Created: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if job.started_at:
            log_lines.append(f"Started: {job.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if job.finished_at:
            log_lines.append(f"Finished: {job.finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        duration = job.get_duration()
        if duration:
            mins, secs = divmod(int(duration), 60)
            hours, mins = divmod(mins, 60)
            if hours > 0:
                log_lines.append(f"Duration: {hours}h {mins}m {secs}s")
            else:
                log_lines.append(f"Duration: {mins}m {secs}s")
        
        if job.error_message:
            log_lines.append(f"Error: {job.error_message}")
        
        log_lines.append(f"{'='*60}")
        log_lines.append("")
        log_lines.append("FFmpeg Command:")
        log_lines.append(" ".join(job.command))
        log_lines.append("")
        log_lines.append(f"{'='*60}")
        log_lines.append("Logs:")
        log_lines.append(f"{'='*60}")
        
        self._log_text.setPlainText("\n".join(log_lines))
    
    def _cancel_selected_job(self) -> None:
        """Cancel the selected job."""
        if not self._selected_job_id:
            return
        
        job = self._job_manager.get_job(self._selected_job_id)
        if not job:
            return
        
        result = QMessageBox.question(
            self,
            "Stop Job",
            f"Are you sure you want to stop '{job.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            self._job_manager.cancel_job(self._selected_job_id)
    
    def _remove_selected_job(self) -> None:
        """Remove the selected job from history."""
        if not self._selected_job_id:
            return
        
        job = self._job_manager.get_job(self._selected_job_id)
        if not job:
            return
        
        if job.status == JobStatus.RUNNING:
            QMessageBox.warning(
                self,
                "Cannot Remove",
                "Cannot remove a running job. Stop it first."
            )
            return
        
        self._job_manager.remove_job(self._selected_job_id)
        self._refresh_job_list()
    
    def _on_job_added(self, job_id: str) -> None:
        """Handle job added signal."""
        self._refresh_job_list()
    
    def _on_job_started(self, job_id: str) -> None:
        """Handle job started signal."""
        self._refresh_job_list()
    
    def _on_job_progress(self, job_id: str, log_line: str) -> None:
        """Handle job progress signal."""
        # If this is the selected job, append log
        if job_id == self._selected_job_id:
            self._log_text.append(log_line)
    
    def _on_job_completed(self, job_id: str) -> None:
        """Handle job completed signal."""
        self._refresh_job_list()
        self._update_stats()
    
    def _on_job_failed(self, job_id: str, error_message: str) -> None:
        """Handle job failed signal."""
        self._refresh_job_list()
        self._update_stats()
    
    def _on_job_cancelled(self, job_id: str) -> None:
        """Handle job cancelled signal."""
        self._refresh_job_list()
        self._update_stats()
    
    def _apply_styles(self) -> None:
        """Apply custom styles."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
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
            
            QTreeWidget {
                background-color: #16213e;
                color: #ccd6f6;
                border: 1px solid #0f3460;
                border-radius: 5px;
                alternate-background-color: #1a2842;
            }
            
            QTreeWidget::item:selected {
                background-color: #0f3460;
            }
            
            QTreeWidget::item:hover {
                background-color: #1a4f7a;
            }
            
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            
            QPushButton:hover {
                background-color: #1a4f7a;
            }
            
            QPushButton:disabled {
                background-color: #0a1f3f;
                color: #555555;
            }
            
            QLabel {
                color: #ccd6f6;
            }
        """)
    
    def closeEvent(self, event) -> None:
        """Handle close event."""
        self._update_timer.stop()
        self.closed.emit()
        event.accept()

