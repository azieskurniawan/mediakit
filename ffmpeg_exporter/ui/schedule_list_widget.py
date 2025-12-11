"""
Schedule List Widget - Display and manage scheduled streams.
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QTimer

from core.stream_scheduler import StreamScheduler, StreamSchedule
from ui.schedule_dialog import ScheduleDialog


class ScheduleItemWidget(QFrame):
    """Widget for displaying a single schedule item."""
    
    # Signals
    edit_requested = Signal(str)  # schedule_id
    delete_requested = Signal(str)  # schedule_id
    toggle_requested = Signal(str, bool)  # schedule_id, enabled
    
    def __init__(self, schedule: StreamSchedule):
        super().__init__()
        
        self._schedule = schedule
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("scheduleItem")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Header row
        header_layout = QHBoxLayout()
        
        # Status indicator
        status_icon = "✓" if self._schedule.enabled else "○"
        self._status_label = QLabel(status_icon)
        self._status_label.setObjectName("statusIcon")
        self._status_label.setFixedWidth(20)
        header_layout.addWidget(self._status_label)
        
        # Schedule name
        self._name_label = QLabel(self._schedule.name)
        self._name_label.setObjectName("scheduleName")
        header_layout.addWidget(self._name_label, 1)
        
        layout.addLayout(header_layout)
        
        # Details row
        details_layout = QHBoxLayout()
        
        # Recurrence info
        recurrence_text = self._get_recurrence_text()
        recurrence_label = QLabel(recurrence_text)
        recurrence_label.setObjectName("scheduleDetails")
        details_layout.addWidget(recurrence_label)
        
        # Duration info
        duration_text = self._get_duration_text()
        duration_label = QLabel(f"• {duration_text}")
        duration_label.setObjectName("scheduleDetails")
        details_layout.addWidget(duration_label)
        
        details_layout.addStretch()
        
        layout.addLayout(details_layout)
        
        # Next run row
        if self._schedule.enabled and self._schedule.next_run:
            next_run_layout = QHBoxLayout()
            
            next_run_label = QLabel("Next run:")
            next_run_label.setObjectName("scheduleLabel")
            next_run_layout.addWidget(next_run_label)
            
            self._next_run_label = QLabel(self._get_next_run_text())
            self._next_run_label.setObjectName("nextRunText")
            next_run_layout.addWidget(self._next_run_label)
            
            next_run_layout.addStretch()
            
            layout.addLayout(next_run_layout)
        
        # Buttons row
        button_layout = QHBoxLayout()
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("scheduleActionButton")
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._schedule.id))
        button_layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("scheduleActionButton")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self._schedule.id))
        button_layout.addWidget(delete_btn)
        
        # Enable/Disable button
        toggle_text = "Disable" if self._schedule.enabled else "Enable"
        self._toggle_btn = QPushButton(toggle_text)
        self._toggle_btn.setObjectName("scheduleToggleButton")
        self._toggle_btn.clicked.connect(self._on_toggle)
        button_layout.addWidget(self._toggle_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def _get_recurrence_text(self) -> str:
        """Get recurrence description."""
        if not self._schedule.start_datetime:
            return "Not scheduled"
        
        try:
            dt = datetime.fromisoformat(self._schedule.start_datetime)
            time_str = dt.strftime('%H:%M')
        except (ValueError, TypeError):
            return "Invalid time"
        
        recurrence = self._schedule.recurrence.value
        
        if recurrence == "once":
            return f"Once at {dt.strftime('%d %b %Y, %H:%M')}"
        elif recurrence == "daily":
            return f"Daily at {time_str}"
        elif recurrence == "weekly":
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            selected = [days[i] for i in self._schedule.weekdays]
            return f"Weekly on {', '.join(selected)} at {time_str}"
        
        return "Unknown"
    
    def _get_duration_text(self) -> str:
        """Get duration description."""
        if self._schedule.duration_minutes == 0:
            return "∞ (infinite)"
        
        mins = self._schedule.duration_minutes
        if mins >= 60:
            hours = mins // 60
            remaining_mins = mins % 60
            if remaining_mins > 0:
                return f"{hours}h {remaining_mins}m"
            else:
                return f"{hours}h"
        
        return f"{mins}m"
    
    def _get_next_run_text(self) -> str:
        """Get next run description."""
        if not self._schedule.next_run:
            return "Not scheduled"
        
        try:
            next_dt = datetime.fromisoformat(self._schedule.next_run)
            now = datetime.now()
            
            # Time until next run
            delta = next_dt - now
            
            if delta.total_seconds() < 0:
                return "Overdue"
            
            if delta.days > 0:
                return f"{next_dt.strftime('%d %b %Y, %H:%M')} (in {delta.days} day{'s' if delta.days > 1 else ''})"
            else:
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                
                if hours > 0:
                    return f"Today at {next_dt.strftime('%H:%M')} (in {hours}h {minutes}m)"
                else:
                    return f"Today at {next_dt.strftime('%H:%M')} (in {minutes}m)"
        
        except (ValueError, TypeError):
            return "Invalid time"
    
    def _on_toggle(self) -> None:
        """Handle toggle button click."""
        new_state = not self._schedule.enabled
        self.toggle_requested.emit(self._schedule.id, new_state)
    
    def update_schedule(self, schedule: StreamSchedule) -> None:
        """Update display with new schedule data."""
        self._schedule = schedule
        
        # Update labels
        status_icon = "✓" if schedule.enabled else "○"
        self._status_label.setText(status_icon)
        self._name_label.setText(schedule.name)
        
        # Update toggle button
        toggle_text = "Disable" if schedule.enabled else "Enable"
        self._toggle_btn.setText(toggle_text)
    
    def _apply_styles(self) -> None:
        """Apply custom styles."""
        enabled_style = """
            #scheduleItem {
                background-color: #0f3460;
                border: 1px solid #1a4f7a;
                border-radius: 8px;
            }
        """
        
        disabled_style = """
            #scheduleItem {
                background-color: #1a1a2e;
                border: 1px solid #0f3460;
                border-radius: 8px;
            }
        """
        
        self.setStyleSheet(enabled_style if self._schedule.enabled else disabled_style)


class ScheduleListWidget(QDialog):
    """Widget for managing scheduled streams."""
    
    def __init__(self, scheduler: StreamScheduler, parent=None):
        super().__init__(parent)
        
        self._scheduler = scheduler
        self._item_widgets = {}
        
        self._setup_ui()
        self._apply_styles()
        self._load_schedules()
        
        # Update timer for relative times
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._refresh_display)
        self._update_timer.start(30000)  # Update every 30 seconds
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        self.setWindowTitle("Manage Scheduled Streams")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Scheduled Streams")
        title.setObjectName("dialogTitle")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Create new schedule button
        create_btn = QPushButton("➕ Create New Schedule")
        create_btn.setObjectName("primaryButton")
        create_btn.clicked.connect(self._create_new_schedule)
        header_layout.addWidget(create_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll area for schedules
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content widget
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(10)
        
        scroll.setWidget(self._content_widget)
        layout.addWidget(scroll, 1)
        
        # Empty state label
        self._empty_label = QLabel("No schedules yet.\nClick 'Create New Schedule' to get started!")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setObjectName("emptyLabel")
        self._content_layout.addWidget(self._empty_label)
        self._content_layout.addStretch()
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_schedules(self) -> None:
        """Load schedules from scheduler."""
        schedules = self._scheduler.get_all_schedules()
        
        if not schedules:
            self._empty_label.show()
            return
        
        self._empty_label.hide()
        
        for schedule in schedules:
            self._add_schedule_item(schedule)
    
    def _add_schedule_item(self, schedule: StreamSchedule) -> None:
        """Add a schedule item to the list."""
        item_widget = ScheduleItemWidget(schedule)
        
        # Connect signals
        item_widget.edit_requested.connect(self._on_edit_schedule)
        item_widget.delete_requested.connect(self._on_delete_schedule)
        item_widget.toggle_requested.connect(self._on_toggle_schedule)
        
        # Insert before stretch
        self._content_layout.insertWidget(self._content_layout.count() - 1, item_widget)
        self._item_widgets[schedule.id] = item_widget
    
    def _create_new_schedule(self) -> None:
        """Create a new schedule."""
        dialog = ScheduleDialog(parent=self)
        if dialog.exec():
            # Get schedule data
            data = dialog.get_schedule_data()
            
            # Generate unique ID
            import uuid
            schedule_id = str(uuid.uuid4())
            
            # Create schedule object
            schedule = StreamSchedule(
                id=schedule_id,
                name=data['name'],
                enabled=True,
                start_datetime=data['start_datetime'],
                recurrence=data['recurrence'],
                weekdays=data['weekdays'],
                duration_minutes=data['duration_minutes'],
                media_config={},  # Will be filled when user starts a scheduled stream
                stream_settings={}
            )
            
            # Add to scheduler
            self._scheduler.add_schedule(schedule)
            
            # Add to UI
            self._add_schedule_item(schedule)
            self._empty_label.hide()
    
    def _on_edit_schedule(self, schedule_id: str) -> None:
        """Handle edit request."""
        schedule = self._scheduler.get_schedule(schedule_id)
        if not schedule:
            return
        
        dialog = ScheduleDialog(schedule=schedule, parent=self)
        if dialog.exec():
            # Get updated data
            data = dialog.get_schedule_data()
            
            # Update schedule
            schedule.name = data['name']
            schedule.start_datetime = data['start_datetime']
            schedule.recurrence = data['recurrence']
            schedule.weekdays = data['weekdays']
            schedule.duration_minutes = data['duration_minutes']
            
            # Update in scheduler
            self._scheduler.update_schedule(schedule)
            
            # Update UI
            if schedule_id in self._item_widgets:
                self._item_widgets[schedule_id].update_schedule(schedule)
    
    def _on_delete_schedule(self, schedule_id: str) -> None:
        """Handle delete request."""
        schedule = self._scheduler.get_schedule(schedule_id)
        if not schedule:
            return
        
        result = QMessageBox.question(
            self,
            "Delete Schedule",
            f"Are you sure you want to delete '{schedule.name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Remove from scheduler
            self._scheduler.delete_schedule(schedule_id)
            
            # Remove from UI
            if schedule_id in self._item_widgets:
                widget = self._item_widgets[schedule_id]
                self._content_layout.removeWidget(widget)
                widget.deleteLater()
                del self._item_widgets[schedule_id]
            
            # Show empty label if no schedules
            if not self._item_widgets:
                self._empty_label.show()
    
    def _on_toggle_schedule(self, schedule_id: str, enabled: bool) -> None:
        """Handle toggle request."""
        self._scheduler.enable_schedule(schedule_id, enabled)
        
        # Update UI
        schedule = self._scheduler.get_schedule(schedule_id)
        if schedule and schedule_id in self._item_widgets:
            self._item_widgets[schedule_id].update_schedule(schedule)
    
    def _refresh_display(self) -> None:
        """Refresh schedule display."""
        for schedule_id, widget in self._item_widgets.items():
            schedule = self._scheduler.get_schedule(schedule_id)
            if schedule:
                widget.update_schedule(schedule)
    
    def _apply_styles(self) -> None:
        """Apply custom styles."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            
            #dialogTitle {
                color: #00d4ff;
            }
            
            #emptyLabel {
                color: #8892b0;
                font-size: 14px;
                padding: 40px;
            }
            
            #scheduleItem {
                padding: 10px;
            }
            
            #statusIcon {
                color: #00d4ff;
                font-size: 18px;
                font-weight: bold;
            }
            
            #scheduleName {
                color: #ccd6f6;
                font-size: 14px;
                font-weight: bold;
            }
            
            #scheduleDetails, #scheduleLabel {
                color: #8892b0;
                font-size: 11px;
            }
            
            #nextRunText {
                color: #00d4ff;
                font-size: 11px;
                font-weight: bold;
            }
            
            #scheduleActionButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 15px;
                min-width: 70px;
            }
            
            #scheduleActionButton:hover {
                background-color: #1a4f7a;
            }
            
            #scheduleToggleButton {
                background-color: #00d4ff;
                color: #16213e;
                border: none;
                border-radius: 5px;
                padding: 6px 15px;
                font-weight: bold;
                min-width: 70px;
            }
            
            #scheduleToggleButton:hover {
                background-color: #00b8e6;
            }
            
            QPushButton#primaryButton {
                background-color: #00d4ff;
                color: #16213e;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #00b8e6;
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
        """)

