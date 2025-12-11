"""
Quick Test Script for Stream Scheduler

This script tests the scheduling functionality without running the full GUI.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize Qt Application for QTimer to work properly
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from ffmpeg_exporter.core.stream_scheduler import StreamScheduler, StreamSchedule, RecurrenceType


def test_scheduler():
    """Test scheduler functionality."""
    print("=" * 60)
    print("STREAM SCHEDULER TEST")
    print("=" * 60)
    print()
    
    # Create scheduler
    print("1. Creating scheduler...")
    scheduler = StreamScheduler(config_dir="ffmpeg_exporter/config")
    print("   ✓ Scheduler created")
    print()
    
    # Define callback
    def on_trigger(schedule: StreamSchedule):
        print(f"\n🔴 SCHEDULE TRIGGERED: {schedule.name}")
        print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
        print()
    
    scheduler.set_trigger_callback(on_trigger)
    
    # Load existing schedules
    existing = scheduler.get_all_schedules()
    print(f"2. Loaded {len(existing)} existing schedule(s)")
    if existing:
        for s in existing:
            print(f"   - {s.name} ({'enabled' if s.enabled else 'disabled'})")
    print()
    
    # Create test schedule (1 minute from now)
    test_time = datetime.now() + timedelta(minutes=1)
    print(f"3. Creating test schedule for {test_time.strftime('%H:%M:%S')}...")
    
    test_schedule = StreamSchedule(
        id="test-schedule-001",
        name="Test Schedule (1 minute)",
        enabled=True,
        start_datetime=test_time.isoformat(),
        recurrence=RecurrenceType.ONCE,
        weekdays=[],
        duration_minutes=0,
        media_config={},
        stream_settings={}
    )
    
    scheduler.add_schedule(test_schedule)
    print("   ✓ Test schedule created")
    print()
    
    # Show next run
    next_run = test_schedule.get_next_run_time()
    if next_run:
        print(f"4. Next run: {next_run.strftime('%H:%M:%S')}")
        delta = next_run - datetime.now()
        print(f"   Time until trigger: {int(delta.total_seconds())} seconds")
    print()
    
    # Show all enabled schedules
    enabled = scheduler.get_enabled_schedules()
    print(f"5. Total enabled schedules: {len(enabled)}")
    for s in enabled:
        print(f"   - {s.name}")
        if s.next_run:
            print(f"     Next: {s.next_run}")
    print()
    
    print("=" * 60)
    print("TEST SETUP COMPLETE")
    print("=" * 60)
    print()
    print("The test schedule will trigger in ~1 minute.")
    print("Keep this script running to see the trigger.")
    print("Press Ctrl+C to stop.")
    print()
    
    # Return scheduler to keep it alive
    return scheduler


if __name__ == "__main__":
    # Create Qt Application
    app = QApplication(sys.argv)
    
    # Run test
    scheduler = test_scheduler()
    
    # Setup cleanup on exit
    def cleanup():
        print("\n\nStopping scheduler...")
        scheduler.shutdown()
        print("✓ Scheduler stopped")
    
    app.aboutToQuit.connect(cleanup)
    
    # Run Qt event loop
    sys.exit(app.exec())

