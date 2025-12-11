"""
Stream Scheduler - Manages scheduled livestreams.
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Callable, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger


class RecurrenceType(Enum):
    """Recurrence type for scheduled streams."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"


@dataclass
class StreamSchedule:
    """Represents a scheduled livestream."""
    id: str
    name: str
    enabled: bool = True
    
    # Timing
    start_datetime: str = ""  # ISO format: 2025-12-12T20:00:00
    recurrence: RecurrenceType = RecurrenceType.ONCE
    weekdays: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday
    
    # Duration
    duration_minutes: int = 0  # 0 = infinite
    
    # Media configuration (stored as dict)
    media_config: Dict = field(default_factory=dict)
    stream_settings: Dict = field(default_factory=dict)
    
    # Metadata
    created_at: str = ""
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['recurrence'] = self.recurrence.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StreamSchedule':
        """Create from dictionary."""
        data = data.copy()
        if 'recurrence' in data:
            data['recurrence'] = RecurrenceType(data['recurrence'])
        return cls(**data)
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Calculate next run time."""
        if not self.enabled:
            return None
        
        try:
            start_dt = datetime.fromisoformat(self.start_datetime)
        except (ValueError, TypeError):
            return None
        
        now = datetime.now()
        
        if self.recurrence == RecurrenceType.ONCE:
            return start_dt if start_dt > now else None
        
        elif self.recurrence == RecurrenceType.DAILY:
            # Same time every day
            next_run = start_dt.replace(
                year=now.year,
                month=now.month,
                day=now.day
            )
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif self.recurrence == RecurrenceType.WEEKLY:
            # Specific weekdays
            if not self.weekdays:
                return None
            
            # Find next matching weekday
            for i in range(7):
                check_date = now + timedelta(days=i)
                if check_date.weekday() in self.weekdays:
                    next_run = start_dt.replace(
                        year=check_date.year,
                        month=check_date.month,
                        day=check_date.day
                    )
                    if next_run > now:
                        return next_run
            return None
        
        return None


class StreamScheduler(QObject):
    """Manages scheduled livestreams."""
    
    # Signals
    schedule_added = Signal(str)  # schedule_id
    schedule_updated = Signal(str)  # schedule_id
    schedule_deleted = Signal(str)  # schedule_id
    schedule_triggered = Signal(str)  # schedule_id
    
    def __init__(self, config_dir: str = "config"):
        super().__init__()
        
        self._config_dir = Path(config_dir)
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._schedules_file = self._config_dir / "schedules.json"
        
        self._schedules: Dict[str, StreamSchedule] = {}
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        
        # Callback for when schedule triggers
        self._trigger_callback: Optional[Callable[[StreamSchedule], None]] = None
        
        # Update timer for next run times
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_next_runs)
        self._update_timer.start(60000)  # Update every minute
        
        # Load schedules
        self._load_schedules()
        self._reschedule_all()
    
    def set_trigger_callback(self, callback: Callable[[StreamSchedule], None]) -> None:
        """Set callback function for when schedule triggers."""
        self._trigger_callback = callback
    
    def add_schedule(self, schedule: StreamSchedule) -> None:
        """Add a new schedule."""
        if not schedule.created_at:
            schedule.created_at = datetime.now().isoformat()
        
        self._schedules[schedule.id] = schedule
        self._schedule_job(schedule)
        self._save_schedules()
        self.schedule_added.emit(schedule.id)
    
    def update_schedule(self, schedule: StreamSchedule) -> None:
        """Update existing schedule."""
        if schedule.id not in self._schedules:
            return
        
        # Remove old job
        self._remove_job(schedule.id)
        
        # Update schedule
        self._schedules[schedule.id] = schedule
        
        # Reschedule if enabled
        if schedule.enabled:
            self._schedule_job(schedule)
        
        self._save_schedules()
        self.schedule_updated.emit(schedule.id)
    
    def delete_schedule(self, schedule_id: str) -> None:
        """Delete a schedule."""
        if schedule_id not in self._schedules:
            return
        
        self._remove_job(schedule_id)
        del self._schedules[schedule_id]
        self._save_schedules()
        self.schedule_deleted.emit(schedule_id)
    
    def get_schedule(self, schedule_id: str) -> Optional[StreamSchedule]:
        """Get schedule by ID."""
        return self._schedules.get(schedule_id)
    
    def get_all_schedules(self) -> List[StreamSchedule]:
        """Get all schedules."""
        return list(self._schedules.values())
    
    def get_enabled_schedules(self) -> List[StreamSchedule]:
        """Get enabled schedules only."""
        return [s for s in self._schedules.values() if s.enabled]
    
    def enable_schedule(self, schedule_id: str, enabled: bool) -> None:
        """Enable or disable a schedule."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return
        
        schedule.enabled = enabled
        
        if enabled:
            self._schedule_job(schedule)
        else:
            self._remove_job(schedule_id)
        
        self._save_schedules()
        self.schedule_updated.emit(schedule_id)
    
    def _schedule_job(self, schedule: StreamSchedule) -> None:
        """Schedule a job in APScheduler."""
        if not schedule.enabled:
            return
        
        # Remove existing job if any
        self._remove_job(schedule.id)
        
        try:
            start_dt = datetime.fromisoformat(schedule.start_datetime)
        except (ValueError, TypeError):
            return
        
        if schedule.recurrence == RecurrenceType.ONCE:
            # One-time schedule
            if start_dt > datetime.now():
                self._scheduler.add_job(
                    self._trigger_schedule,
                    trigger=DateTrigger(run_date=start_dt),
                    id=schedule.id,
                    args=[schedule.id],
                    replace_existing=True
                )
        
        elif schedule.recurrence == RecurrenceType.DAILY:
            # Daily at specific time
            self._scheduler.add_job(
                self._trigger_schedule,
                trigger=CronTrigger(
                    hour=start_dt.hour,
                    minute=start_dt.minute
                ),
                id=schedule.id,
                args=[schedule.id],
                replace_existing=True
            )
        
        elif schedule.recurrence == RecurrenceType.WEEKLY:
            # Specific weekdays
            if schedule.weekdays:
                # CronTrigger uses 0=Sunday, 6=Saturday
                # Convert from Python weekday (0=Monday) to Cron (0=Sunday)
                cron_days = [(d + 1) % 7 for d in schedule.weekdays]
                day_of_week = ','.join(map(str, sorted(cron_days)))
                
                self._scheduler.add_job(
                    self._trigger_schedule,
                    trigger=CronTrigger(
                        day_of_week=day_of_week,
                        hour=start_dt.hour,
                        minute=start_dt.minute
                    ),
                    id=schedule.id,
                    args=[schedule.id],
                    replace_existing=True
                )
        
        # Update next run time
        schedule.next_run = schedule.get_next_run_time()
        if schedule.next_run:
            schedule.next_run = schedule.next_run.isoformat()
    
    def _remove_job(self, schedule_id: str) -> None:
        """Remove job from APScheduler."""
        try:
            self._scheduler.remove_job(schedule_id)
        except Exception:
            pass
    
    def _trigger_schedule(self, schedule_id: str) -> None:
        """Called when a schedule triggers."""
        schedule = self._schedules.get(schedule_id)
        if not schedule or not schedule.enabled:
            return
        
        # Update metadata
        schedule.last_run = datetime.now().isoformat()
        schedule.run_count += 1
        
        # Calculate next run for recurring schedules
        if schedule.recurrence != RecurrenceType.ONCE:
            next_run = schedule.get_next_run_time()
            schedule.next_run = next_run.isoformat() if next_run else None
        else:
            # One-time schedule - disable after running
            schedule.enabled = False
            schedule.next_run = None
        
        self._save_schedules()
        
        # Emit signal
        self.schedule_triggered.emit(schedule_id)
        
        # Call callback if set
        if self._trigger_callback:
            self._trigger_callback(schedule)
    
    def _update_next_runs(self) -> None:
        """Update next run times for all schedules."""
        for schedule in self._schedules.values():
            if schedule.enabled and schedule.recurrence != RecurrenceType.ONCE:
                next_run = schedule.get_next_run_time()
                schedule.next_run = next_run.isoformat() if next_run else None
    
    def _reschedule_all(self) -> None:
        """Reschedule all enabled schedules."""
        for schedule in self._schedules.values():
            if schedule.enabled:
                self._schedule_job(schedule)
    
    def _load_schedules(self) -> None:
        """Load schedules from file."""
        if not self._schedules_file.exists():
            return
        
        try:
            with open(self._schedules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for schedule_data in data.get('schedules', []):
                schedule = StreamSchedule.from_dict(schedule_data)
                self._schedules[schedule.id] = schedule
        
        except Exception as e:
            print(f"Error loading schedules: {e}")
    
    def _save_schedules(self) -> None:
        """Save schedules to file."""
        try:
            data = {
                'schedules': [s.to_dict() for s in self._schedules.values()]
            }
            
            with open(self._schedules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"Error saving schedules: {e}")
    
    def shutdown(self) -> None:
        """Shutdown scheduler."""
        self._update_timer.stop()
        self._scheduler.shutdown()

