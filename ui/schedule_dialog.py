"""
Schedule Dialog - UI for creating/editing scheduled streams.
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDateTimeEdit, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QFormLayout, QButtonGroup, QRadioButton, QWidget
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont

from core.stream_scheduler import StreamSchedule, RecurrenceType


class ScheduleDialog(QDialog):
    """Dialog for creating/editing stream schedules."""
    
    def __init__(self, schedule: StreamSchedule = None, parent=None):
        super().__init__(parent)
        
        self._schedule = schedule
        self._is_edit_mode = schedule is not None
        
        self._setup_ui()
        self._apply_styles()
        
        if self._is_edit_mode:
            self._load_schedule_data()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        title = "Edit Schedule" if self._is_edit_mode else "Create Schedule"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Schedule name
        name_layout = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Daily Lofi Stream")
        name_layout.addRow("Schedule Name:", self._name_edit)
        layout.addLayout(name_layout)
        
        # Date & Time
        datetime_group = QGroupBox("Start Time")
        datetime_layout = QFormLayout()
        
        self._datetime_edit = QDateTimeEdit()
        self._datetime_edit.setCalendarPopup(True)
        self._datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # +1 hour
        self._datetime_edit.setDisplayFormat("dd MMM yyyy - HH:mm")
        datetime_layout.addRow("Date & Time:", self._datetime_edit)
        
        datetime_group.setLayout(datetime_layout)
        layout.addWidget(datetime_group)
        
        # Recurrence
        recurrence_group = QGroupBox("Recurrence")
        recurrence_layout = QVBoxLayout()
        
        self._recurrence_group = QButtonGroup()
        
        self._once_radio = QRadioButton("Once only")
        self._once_radio.setChecked(True)
        self._once_radio.toggled.connect(self._on_recurrence_changed)
        self._recurrence_group.addButton(self._once_radio, 0)
        recurrence_layout.addWidget(self._once_radio)
        
        self._daily_radio = QRadioButton("Daily (every day at same time)")
        self._daily_radio.toggled.connect(self._on_recurrence_changed)
        self._recurrence_group.addButton(self._daily_radio, 1)
        recurrence_layout.addWidget(self._daily_radio)
        
        self._weekly_radio = QRadioButton("Weekly (specific days)")
        self._weekly_radio.toggled.connect(self._on_recurrence_changed)
        self._recurrence_group.addButton(self._weekly_radio, 2)
        recurrence_layout.addWidget(self._weekly_radio)
        
        # Weekday selection (hidden by default)
        self._weekday_widget = QWidget()
        weekday_layout = QHBoxLayout(self._weekday_widget)
        weekday_layout.setContentsMargins(30, 5, 0, 5)
        
        self._weekday_checks = []
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in weekdays:
            cb = QCheckBox(day)
            self._weekday_checks.append(cb)
            weekday_layout.addWidget(cb)
        
        self._weekday_widget.hide()
        recurrence_layout.addWidget(self._weekday_widget)
        
        recurrence_group.setLayout(recurrence_layout)
        layout.addWidget(recurrence_group)
        
        # Duration
        duration_group = QGroupBox("Stream Duration")
        duration_layout = QVBoxLayout()
        
        self._duration_group = QButtonGroup()
        
        self._infinite_radio = QRadioButton("Run infinitely (until manually stopped)")
        self._infinite_radio.setChecked(True)
        self._infinite_radio.toggled.connect(self._on_duration_changed)
        self._duration_group.addButton(self._infinite_radio, 0)
        duration_layout.addWidget(self._infinite_radio)
        
        duration_row = QHBoxLayout()
        self._timed_radio = QRadioButton("Auto-stop after:")
        self._timed_radio.toggled.connect(self._on_duration_changed)
        self._duration_group.addButton(self._timed_radio, 1)
        duration_row.addWidget(self._timed_radio)
        
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 1440)  # 1 min to 24 hours
        self._duration_spin.setValue(60)
        self._duration_spin.setSuffix(" minutes")
        self._duration_spin.setEnabled(False)
        duration_row.addWidget(self._duration_spin)
        
        duration_row.addStretch()
        duration_layout.addLayout(duration_row)
        
        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)
        
        # Info
        self._info_label = QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #00d4ff; padding: 10px; background-color: rgba(0, 212, 255, 0.1); border-radius: 5px;")
        layout.addWidget(self._info_label)
        self._update_info_label()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_text = "Update" if self._is_edit_mode else "Create"
        save_btn = QPushButton(save_text)
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Connect signals for live update
        self._datetime_edit.dateTimeChanged.connect(self._update_info_label)
    
    def _on_recurrence_changed(self, checked: bool) -> None:
        """Handle recurrence type change."""
        if not checked:
            return
        
        # Show/hide weekday selection
        self._weekday_widget.setVisible(self._weekly_radio.isChecked())
        self._update_info_label()
    
    def _on_duration_changed(self, checked: bool) -> None:
        """Handle duration type change."""
        if not checked:
            return
        
        self._duration_spin.setEnabled(self._timed_radio.isChecked())
        self._update_info_label()
    
    def _update_info_label(self) -> None:
        """Update info label with schedule summary."""
        dt = self._datetime_edit.dateTime().toPython()
        now = datetime.now()
        
        # Time until start
        delta = dt - now
        if delta.total_seconds() > 0:
            if delta.days > 0:
                time_str = f"in {delta.days} day{'s' if delta.days > 1 else ''}"
            else:
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                if hours > 0:
                    time_str = f"in {hours}h {minutes}m"
                else:
                    time_str = f"in {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            time_str = "in the past (will not run)"
        
        # Build info text
        info_parts = [f"📅 Start: {dt.strftime('%d %b %Y at %H:%M')} ({time_str})"]
        
        # Recurrence
        if self._once_radio.isChecked():
            info_parts.append("🔄 Recurrence: Once only")
        elif self._daily_radio.isChecked():
            info_parts.append(f"🔄 Recurrence: Daily at {dt.strftime('%H:%M')}")
        elif self._weekly_radio.isChecked():
            selected_days = [i for i, cb in enumerate(self._weekday_checks) if cb.isChecked()]
            if selected_days:
                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                day_names = [days[i] for i in selected_days]
                info_parts.append(f"🔄 Recurrence: Weekly on {', '.join(day_names)}")
            else:
                info_parts.append("🔄 Recurrence: Weekly (no days selected!)")
        
        # Duration
        if self._infinite_radio.isChecked():
            info_parts.append("⏱️ Duration: Infinite (manual stop)")
        else:
            mins = self._duration_spin.value()
            if mins >= 60:
                hours = mins // 60
                remaining_mins = mins % 60
                if remaining_mins > 0:
                    info_parts.append(f"⏱️ Duration: {hours}h {remaining_mins}m")
                else:
                    info_parts.append(f"⏱️ Duration: {hours} hour{'s' if hours > 1 else ''}")
            else:
                info_parts.append(f"⏱️ Duration: {mins} minutes")
        
        self._info_label.setText("\n".join(info_parts))
    
    def _load_schedule_data(self) -> None:
        """Load data from existing schedule."""
        if not self._schedule:
            return
        
        # Name
        self._name_edit.setText(self._schedule.name)
        
        # DateTime
        try:
            dt = datetime.fromisoformat(self._schedule.start_datetime)
            qdt = QDateTime(dt)
            self._datetime_edit.setDateTime(qdt)
        except (ValueError, TypeError):
            pass
        
        # Recurrence
        if self._schedule.recurrence == RecurrenceType.ONCE:
            self._once_radio.setChecked(True)
        elif self._schedule.recurrence == RecurrenceType.DAILY:
            self._daily_radio.setChecked(True)
        elif self._schedule.recurrence == RecurrenceType.WEEKLY:
            self._weekly_radio.setChecked(True)
            for day_idx in self._schedule.weekdays:
                if 0 <= day_idx < len(self._weekday_checks):
                    self._weekday_checks[day_idx].setChecked(True)
        
        # Duration
        if self._schedule.duration_minutes == 0:
            self._infinite_radio.setChecked(True)
        else:
            self._timed_radio.setChecked(True)
            self._duration_spin.setValue(self._schedule.duration_minutes)
    
    def _on_save(self) -> None:
        """Handle save button."""
        # Validate
        if not self._name_edit.text().strip():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a schedule name.")
            return
        
        dt = self._datetime_edit.dateTime().toPython()
        if dt <= datetime.now() and self._once_radio.isChecked():
            from PySide6.QtWidgets import QMessageBox
            result = QMessageBox.question(
                self,
                "Past Time",
                "The scheduled time is in the past. This schedule will not run.\n\nContinue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return
        
        # Validate weekly selection
        if self._weekly_radio.isChecked():
            if not any(cb.isChecked() for cb in self._weekday_checks):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Invalid Selection", "Please select at least one day for weekly recurrence.")
                return
        
        self.accept()
    
    def get_schedule_data(self) -> dict:
        """Get schedule data from form."""
        # Recurrence
        if self._once_radio.isChecked():
            recurrence = RecurrenceType.ONCE
        elif self._daily_radio.isChecked():
            recurrence = RecurrenceType.DAILY
        else:
            recurrence = RecurrenceType.WEEKLY
        
        # Weekdays
        weekdays = [i for i, cb in enumerate(self._weekday_checks) if cb.isChecked()]
        
        # Duration
        duration = 0 if self._infinite_radio.isChecked() else self._duration_spin.value()
        
        return {
            'name': self._name_edit.text().strip(),
            'start_datetime': self._datetime_edit.dateTime().toPython().isoformat(),
            'recurrence': recurrence,
            'weekdays': weekdays,
            'duration_minutes': duration
        }
    
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
                padding-top: 15px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QLabel {
                color: #ccd6f6;
            }
            
            QLineEdit, QDateTimeEdit, QSpinBox {
                background-color: #0f3460;
                color: white;
                border: 1px solid #1a4f7a;
                border-radius: 5px;
                padding: 8px;
                min-height: 25px;
            }
            
            QLineEdit:focus, QDateTimeEdit:focus, QSpinBox:focus {
                border: 1px solid #00d4ff;
            }
            
            QRadioButton, QCheckBox {
                color: #ccd6f6;
                spacing: 8px;
            }
            
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #0f3460;
            }
            
            QRadioButton::indicator:checked {
                background-color: #00d4ff;
                border-color: #00d4ff;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #0f3460;
            }
            
            QCheckBox::indicator:checked {
                background-color: #00d4ff;
                border-color: #00d4ff;
            }
            
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #1a4f7a;
            }
            
            QPushButton#primaryButton {
                background-color: #00d4ff;
                color: #16213e;
                font-weight: bold;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #00b8e6;
            }
        """)

