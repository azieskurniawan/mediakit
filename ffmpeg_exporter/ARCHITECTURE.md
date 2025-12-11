# MediaKit Pro - Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           MEDIAKIT PRO v2.0                                  ║
║                     Python Desktop Application (PySide6)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         MAIN WINDOW                                   │  │
│  │  [◆ MEDIAKIT PRO]        [📊] [⚙] [👁] [EXPORT VIDEO]              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────┬────────────────────────────────────┐  │
│  │  LEFT PANEL (Tabs)             │  RIGHT PANEL (Preview)             │  │
│  │                                 │                                     │  │
│  │  ┌──────────────────────────┐  │  ┌─────────────────────────────┐  │  │
│  │  │ 📁 MEDIA                 │  │  │                             │  │  │
│  │  ├──────────────────────────┤  │  │      Video Preview          │  │  │
│  │  │ • Video Directory        │  │  │      (Optional - Toggle)    │  │  │
│  │  │ • Cover Video            │  │  │                             │  │  │
│  │  │ • Audio Directory        │  │  │   [▶] [⏸] [⏹]              │  │  │
│  │  │ • Loop Mode              │  │  │   ━━━━━●──────────          │  │  │
│  │  └──────────────────────────┘  │  │   🔊 ━━━━●─────             │  │  │
│  │                                 │  └─────────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  │                                     │  │
│  │  │ ✨ EFFECTS               │  │  Can be hidden with [👁] button    │  │
│  │  ├──────────────────────────┤  │                                     │  │
│  │  │ • Logo Overlay           │  │                                     │  │
│  │  │ • Text Overlay           │  │                                     │  │
│  │  │ • Position Controls      │  │                                     │  │
│  │  └──────────────────────────┘  │                                     │  │
│  │                                 │                                     │  │
│  │  ┌──────────────────────────┐  │                                     │  │
│  │  │ 🔴 LIVESTREAM    (NEW!)  │  │                                     │  │
│  │  ├──────────────────────────┤  │                                     │  │
│  │  │ • Stream Destination     │  │                                     │  │
│  │  │   - RTMP URL             │  │                                     │  │
│  │  │   - Stream Key [👁]      │  │                                     │  │
│  │  │ • Video Settings         │  │                                     │  │
│  │  │   - Preset Selector      │  │                                     │  │
│  │  │   - Resolution           │  │                                     │  │
│  │  │   - FPS, Bitrate         │  │                                     │  │
│  │  │ • Audio Settings         │  │                                     │  │
│  │  │ • Duration               │  │                                     │  │
│  │  │   - Infinite ∞           │  │                                     │  │
│  │  │   - Timed (auto-stop)    │  │                                     │  │
│  │  │                          │  │                                     │  │
│  │  │ [🔴 START LIVESTREAM]    │  │                                     │  │
│  │  └──────────────────────────┘  │                                     │  │
│  └────────────────────────────────┴────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                          JOB MONITOR WINDOW                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│  📊 Active Jobs                                              [🔄] [Refresh]  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Type    │ Name                       │ Status      │ Duration │ Started │ │
│  ├─────────────────────────────────────────────────────────────────────────┤ │
│  │ 🔴 STREAM│ YouTube 1080p (∞)         │ Running     │ 45m 23s  │ 14:30  │ │
│  │ 🎥 EXPORT│ video_final.mp4           │ Running     │ 2m 15s   │ 15:10  │ │
│  │ 🎥 EXPORT│ compilation.mp4           │ Completed   │ 8m 45s   │ 14:55  │ │
│  │ 🔴 STREAM│ YouTube 720p (60min)      │ Completed   │ 60m 0s   │ 13:00  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  Total: 4 | Running: 2 | Completed: 2 | Failed: 0                            │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Job Details / Live Logs                                                 │ │
│  ├─────────────────────────────────────────────────────────────────────────┤ │
│  │ Job ID: stream_1                                                        │ │
│  │ Type: LIVESTREAM                                                        │ │
│  │ Status: RUNNING                                                         │ │
│  │ Duration: 45m 23s                                                       │ │
│  │ ════════════════════════════════════════════════════════════════        │ │
│  │ FFmpeg Logs:                                                            │ │
│  │ frame= 81690 fps= 30 q=28.0 size=  524288kB time=00:45:23.00 ...       │ │
│  │ [output stream] packets sent: 81690                                     │ │
│  │ [output stream] bitrate: 4500 kbps                                      │ │
│  │ ...                                                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│                           [⏹ Stop Job] [🗑 Remove] [Close]                   │
└───────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                              CORE COMPONENTS                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────┐      ┌──────────────────────────┐              │
│  │   JOB MANAGER           │◄─────│   MAIN WINDOW            │              │
│  │                         │      │                          │              │
│  │ • create_job()          │      │ • Media Config           │              │
│  │ • start_job()           │      │ • Effects Config         │              │
│  │ • cancel_job()          │      │ • Start Export           │              │
│  │ • get_all_jobs()        │      │ • Start Livestream       │              │
│  │                         │      └──────────────────────────┘              │
│  │ Manages:                │                                                 │
│  │ - Job Queue             │                                                 │
│  │ - Background Threads    │      ┌──────────────────────────┐              │
│  │ - Status Tracking       │      │   EXPORT DIALOG          │              │
│  │ - Temp File Cleanup     │◄─────│                          │              │
│  └─────────────────────────┘      │ • Settings UI            │              │
│             │                      │ • Real-time Logs         │              │
│             │                      │ • Progress Bar           │              │
│             ▼                      └──────────────────────────┘              │
│  ┌─────────────────────────┐                                                 │
│  │   FFmpeg Process        │                                                 │
│  │                         │                                                 │
│  │ subprocess.Popen()      │      ┌──────────────────────────┐              │
│  │   ├─ stdout (logs)      │      │  FFMPEG BUILDER          │              │
│  │   ├─ stderr (logs)      │◄─────│  (Export Mode)           │              │
│  │   └─ returncode         │      │                          │              │
│  └─────────────────────────┘      │ • build_command()        │              │
│                                    │ • Image mode             │              │
│                                    │ • Video mode             │              │
│                                    │ • Concat files           │              │
│                                    │ • Overlays               │              │
│                                    │ • Encoding settings      │              │
│                                    └──────────────────────────┘              │
│                                                                               │
│                                    ┌──────────────────────────┐              │
│                                    │  LIVESTREAM BUILDER      │              │
│                                    │  (Streaming Mode)        │              │
│                                    │                          │              │
│                                    │ • build_command()        │              │
│                                    │ • Infinite loop mode     │              │
│                                    │ • RTMP output            │              │
│                                    │ • Real-time encoding     │              │
│                                    │ • Stream presets         │              │
│                                    └──────────────────────────┘              │
│                                                                               │
│  ┌─────────────────────────┐      ┌──────────────────────────┐              │
│  │   MEDIA MANAGER         │      │   SETTINGS MANAGER       │              │
│  │                         │      │                          │              │
│  │ • MediaConfig           │      │ • FFmpeg Path            │              │
│  │ • Validate Config       │      │ • FFprobe Path           │              │
│  │ • Get Video List        │      │ • Save/Load Settings     │              │
│  └─────────────────────────┘      └──────────────────────────┘              │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW - LIVESTREAM                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  User Clicks "START LIVESTREAM"                                              │
│       │                                                                       │
│       ▼                                                                       │
│  Collect Media Config (videos, audio, logo, text)                            │
│       │                                                                       │
│       ▼                                                                       │
│  Collect Livestream Settings (RTMP, key, resolution, bitrate)                │
│       │                                                                       │
│       ▼                                                                       │
│  LivestreamBuilder.build_command()                                           │
│       │                                                                       │
│       ├─► Create video concat file (infinite loop)                           │
│       ├─► Create audio concat file (infinite loop)                           │
│       ├─► Build filter_complex (scale, overlay, fps)                         │
│       ├─► Add encoding options (nvenc, cbr, bitrate)                         │
│       └─► Add RTMP output URL                                                │
│       │                                                                       │
│       ▼                                                                       │
│  JobManager.create_job(type=LIVESTREAM, command, duration)                   │
│       │                                                                       │
│       ▼                                                                       │
│  JobManager.start_job(job_id)                                                │
│       │                                                                       │
│       ▼                                                                       │
│  Background Thread: subprocess.Popen(command)                                │
│       │                                                                       │
│       ├─► Read stdout line by line                                           │
│       ├─► Emit log_output signal                                             │
│       ├─► Update job status                                                  │
│       └─► (Optional) Auto-stop after duration                                │
│       │                                                                       │
│       ▼                                                                       │
│  Job Monitor displays real-time logs                                         │
│       │                                                                       │
│       ▼                                                                       │
│  YouTube receives RTMP stream ───► Live! 🔴                                  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-JOB ARCHITECTURE                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│                        ┌─────────────────┐                                   │
│                        │   JOB MANAGER   │                                   │
│                        └────────┬────────┘                                   │
│                                 │                                             │
│                ┌────────────────┼────────────────┐                           │
│                │                │                │                           │
│                ▼                ▼                ▼                           │
│         ┌──────────┐     ┌──────────┐     ┌──────────┐                      │
│         │  Job 1   │     │  Job 2   │     │  Job 3   │                      │
│         │ (Stream) │     │ (Export) │     │ (Stream) │                      │
│         └─────┬────┘     └─────┬────┘     └─────┬────┘                      │
│               │                │                │                             │
│               ▼                ▼                ▼                             │
│         ┌──────────┐     ┌──────────┐     ┌──────────┐                      │
│         │ Thread 1 │     │ Thread 2 │     │ Thread 3 │                      │
│         └─────┬────┘     └─────┬────┘     └─────┬────┘                      │
│               │                │                │                             │
│               ▼                ▼                ▼                             │
│         ┌──────────┐     ┌──────────┐     ┌──────────┐                      │
│         │ FFmpeg 1 │     │ FFmpeg 2 │     │ FFmpeg 3 │                      │
│         └─────┬────┘     └─────┬────┘     └─────┬────┘                      │
│               │                │                │                             │
│               ▼                ▼                ▼                             │
│         ┌──────────┐     ┌──────────┐     ┌──────────┐                      │
│         │  RTMP    │     │ video.mp4│     │  RTMP    │                      │
│         │ YouTube  │     │  (disk)  │     │ YouTube  │                      │
│         └──────────┘     └──────────┘     └──────────┘                      │
│                                                                               │
│  All jobs run independently, with their own:                                 │
│  • FFmpeg process                                                            │
│  • Background thread                                                         │
│  • Temporary files                                                           │
│  • Log stream                                                                │
│  • Status tracking                                                           │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════════╗
║                         SIGNAL/SLOT CONNECTIONS                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

JobManager Signals:
├─ job_added(job_id)        ──► JobMonitorWindow.refresh()
├─ job_started(job_id)      ──► JobMonitorWindow.refresh()
├─ job_progress(job_id, log)──► JobMonitorWindow.append_log()
├─ job_completed(job_id)    ──► JobMonitorWindow.refresh() + Notification
├─ job_failed(job_id, error)──► JobMonitorWindow.refresh() + Error Dialog
└─ job_cancelled(job_id)    ──► JobMonitorWindow.refresh()

LivestreamPanel Signals:
└─ start_stream_requested(settings) ──► MainWindow.start_livestream()

ExportDialog Signals:
└─ export_finished(success, msg) ──► MainWindow.show_notification()
```

