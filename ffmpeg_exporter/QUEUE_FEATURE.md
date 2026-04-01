# Export Queue Feature

## Overview

The Export Queue feature allows you to batch process multiple export jobs sequentially. Instead of exporting immediately, you can add multiple jobs to a queue and process them all at once.

## Features

### 1. Add to Queue
- From Export Dialog, click **"📋 Add to Queue"** button
- Enter a name for the job
- Job is added to queue (but not started yet)
- Can continue adding more jobs

### 2. Queue Management
- Open Queue Panel from main window (click **📋** button in header)
- View all queued jobs with their settings
- See status: ⏳ Pending, ⚙️ Processing, ✅ Completed, ❌ Failed

### 3. Queue Controls
- **▶ Start Queue**: Begin processing all pending jobs sequentially
- **⏸ Stop Queue**: Stop after current job finishes
- **🗑 Clear Completed**: Remove all completed/failed jobs
- **🔄 Refresh**: Update queue view

### 4. Job Actions
- **❌ Remove**: Remove job from queue (cannot remove currently processing job)
- **ℹ Details**: View full job information and settings

### 5. Progress Tracking
- Real-time progress bar for current job
- Progress percentage for each job in table
- Status indicators for each job

### 6. Queue Persistence
- Queue is automatically saved to `config/export_queue.json`
- Queue is restored when app restarts
- Jobs that were processing are reset to pending

## Usage Example

### Batch Export Workflow

1. **Setup first export**
   - Configure media, effects, overlays
   - Set export settings (resolution, codec, etc.)
   - Click "📋 Add to Queue" instead of "Export Now"
   - Enter job name (e.g., "1080p Version")

2. **Setup more exports**
   - Change resolution to 720p
   - Click "📋 Add to Queue"
   - Enter job name (e.g., "720p Version")
   
3. **Change effects and add another**
   - Modify overlays or effects
   - Click "📋 Add to Queue"
   - Enter job name (e.g., "Alternative Version")

4. **Start batch processing**
   - Open Queue Panel (📋 button in header)
   - Click "▶ Start Queue"
   - Go to sleep! 😴

5. **Wake up to completed exports**
   - All jobs processed sequentially
   - Check status for any failures
   - Output files ready in specified locations

## Technical Details

### Queue Manager (`core/queue_manager.py`)
- Singleton pattern (one queue manager per app)
- Manages job list, status, and persistence
- Callbacks for job events (started, progress, completed, failed)
- Save/load queue state to JSON

### Queue Panel (`ui/queue_panel.py`)
- Qt Widget for queue visualization
- Table view with job details
- Controls for queue processing
- Background thread for FFmpeg execution

### Export Dialog Integration
- "Add to Queue" button alongside "Export Now"
- Reuses existing validation and settings building
- Creates ExportJob with MediaConfig and ExportSettings

### Job Structure
```python
ExportJob:
- id: str (UUID)
- name: str
- media_config: MediaConfig
- export_settings: ExportSettings
- status: JobStatus (pending/processing/completed/failed)
- progress: float (0-100)
- created_time: datetime
- started_time: datetime
- finished_time: datetime
- error_message: str
```

### Processing Flow
```
Pending Jobs → Sequential Processing → Completed
     ↓                    ↓
  Job Queue      FFmpeg Execution
                        ↓
                Progress Updates
                        ↓
                  Cleanup & Next
```

## Benefits

✅ **Batch Processing**: Setup multiple exports and process overnight
✅ **No Supervision**: Start queue and leave it running
✅ **Flexible**: Can add jobs while queue is processing
✅ **Resume**: Queue persists across app restarts
✅ **Organized**: Track all exports in one place
✅ **Efficient**: Sequential processing avoids resource conflicts

## Future Enhancements

- ⏭️ Parallel processing (multiple jobs at once)
- 🔄 Reorder jobs (drag & drop)
- ✏️ Edit job settings before processing
- 📧 Email notification when queue finishes
- 📊 Detailed progress for each job (frame count, ETA)
- 🔁 Retry failed jobs
- 📝 Export presets for queue jobs
