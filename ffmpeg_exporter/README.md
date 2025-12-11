# 🎬 MediaKit Pro

A Python desktop application for exporting videos and livestreaming using FFmpeg, combining visuals, audio, and overlays with a modern GUI.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-red.svg)

## ✨ Features

### Video Export
- **Media Management**
  - Video directory mode (random order export)
  - Static image mode (loop to match audio)
  - Optional cover video (plays first)
  - Audio directory selection with random or sequential playback

### Livestreaming (NEW!)
- **YouTube Livestreaming**
  - Stream directly to YouTube via RTMP
  - Auto-shuffled video and audio playlists
  - Infinite loop or timed duration (auto-stop)
  - Real-time status monitoring
  - Multiple simultaneous streams supported

- **⏰ Scheduled Streaming (NEW!)**
  - Automatic stream scheduling without YouTube API
  - Three scheduling modes: Once, Daily, Weekly
  - Auto-start at scheduled time
  - Auto-stop with duration control
  - Manage multiple schedules
  - Enable/disable schedules on demand

### Multi-Job Management
- **Parallel Processing**
  - Run multiple exports simultaneously
  - Multiple livestreams at once
  - Export while livestreaming
  - Real-time job monitoring
  - Individual job control (stop, remove)

### Effects & Overlays
- Custom logo overlay with size and position controls
- Text overlay with custom fonts, colors, and positioning
- Position presets (Top Left, Top Right, Bottom Left, Bottom Right, Center)

### Preview Panel (Optional)
- Video playback with controls
- Progress slider and volume control
- Image preview support
- Can be hidden for more workspace

### Export Options
- Presets for YouTube, Instagram, TikTok
- Resolution (1080p, 720p, 4K, custom)
- Frame rate (1-120 FPS)
- Codec (H.264, H.265, VP9)
- GPU acceleration (NVIDIA NVENC)
- Rate control (CRF, CBR, VBR)
- Bitrate configuration

### Real-Time FFmpeg Logging
- Live console output during export/streaming
- Progress tracking
- Cancel export/stream support
- Job history with detailed logs

## 📋 Requirements

- Python 3.11 or higher
- PySide6 6.5.0 or higher
- FFmpeg (must be installed separately)

## 🚀 Installation

1. **Clone or download the project**

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**
   - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Windows: Download the release build, extract, and note the path to `ffmpeg.exe`
   - Linux: `sudo apt install ffmpeg` or equivalent
   - macOS: `brew install ffmpeg`

## 🎯 Usage

1. **Run the application**
   ```bash
   python app.py
   ```

2. **Configure FFmpeg**
   - Click the ⚙ (Settings) button
   - Browse to or auto-detect FFmpeg path
   - Verify the installation

3. **Setup Media**
   - **MEDIA tab**: Select video directory or static image
   - Optionally select a cover video
   - Select audio directory

4. **Add Effects** (optional)
   - **EFFECTS tab**: Enable and configure logo overlay
   - Enable and configure text overlay

5. **Export Video**
   - Click **EXPORT VIDEO** button
   - Choose preset or customize settings
   - Select output filename and folder
   - Click **EXPORT VIDEO** in the dialog
   - Watch real-time FFmpeg progress

6. **Start Livestream** (NEW!)
   - **LIVESTREAM tab**: Enter your YouTube stream key
   - Configure video quality (resolution, FPS, bitrate)
   - Set auto-stop duration or run infinitely
   - Click **🔴 START LIVESTREAM**
   - Monitor status in Job Monitor window

7. **Schedule Streams** (NEW!)
   - **LIVESTREAM tab**: Scroll to "Scheduled Streaming" section
   - Click **➕ Create Schedule**
   - Set date/time, recurrence type, and duration
   - Stream will start automatically at scheduled time
   - Click **📋 Manage Schedules** to view/edit all schedules
   - See [FITUR_JADWAL_LIVESTREAM.md](FITUR_JADWAL_LIVESTREAM.md) for detailed guide

8. **Manage Jobs**
   - Click **📊 Job Monitor** to view all active jobs
   - Monitor multiple exports/streams simultaneously
   - Stop or remove jobs as needed
   - View detailed logs for each job

## 📂 Project Structure

```
mediakit_pro/
├── app.py                 # Main entry point
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── core/                 # Core business logic
│   ├── __init__.py
│   ├── settings_manager.py    # Configuration handling
│   ├── audio_utils.py         # Audio analysis (ffprobe)
│   ├── media_manager.py       # Media file management
│   ├── ffmpeg_builder.py      # FFmpeg command builder (export)
│   ├── livestream_builder.py  # FFmpeg command builder (streaming)
│   ├── stream_scheduler.py    # Scheduled streaming (NEW!)
│   └── job_manager.py         # Multi-job management
├── ui/                   # User interface
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   ├── media_panel.py         # Media selection panel
│   ├── effects_panel.py       # Effects configuration
│   ├── preview_panel.py       # Video preview
│   ├── export_dialog.py       # Export settings & logging
│   ├── livestream_panel.py    # Livestream configuration
│   ├── schedule_dialog.py     # Schedule creation/editing (NEW!)
│   ├── schedule_list_widget.py # Schedule management (NEW!)
│   ├── job_monitor_window.py  # Job monitoring
│   └── settings_dialog.py     # Application settings
├── config/               # Configuration files
│   ├── settings.json          # User settings
│   └── schedules.json         # Stream schedules (NEW!)
└── resources/            # Static resources
    └── icons/                 # Application icons
```

## 🎨 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Space | Play/Pause preview |
| Escape | Close dialog |
| Ctrl+M | Open Job Monitor |

## ⚙️ Export Presets

| Preset | Resolution | FPS | Codec | Bitrate |
|--------|------------|-----|-------|---------|
| YouTube 1080p (FHD) | 1920x1080 | 30 | H.264 | CRF 18 |
| YouTube 720p (HD) | 1280x720 | 30 | H.264 | CRF 20 |
| YouTube 4K (UHD) | 3840x2160 | 30 | H.264 | CRF 18 |
| Instagram (Square) | 1080x1080 | 30 | H.264 | CRF 18 |
| TikTok (Vertical) | 1080x1920 | 30 | H.264 | CRF 18 |

## 🔴 Livestream Presets

| Preset | Resolution | FPS | Bitrate |
|--------|------------|-----|---------|
| YouTube 1080p 60fps | 1920x1080 | 60 | 9000 kbps |
| YouTube 1080p 30fps | 1920x1080 | 30 | 4500 kbps |
| YouTube 720p 60fps | 1280x720 | 60 | 6000 kbps |
| YouTube 720p 30fps | 1280x720 | 30 | 3000 kbps |

## 🔧 FFmpeg Command Examples

**Video concatenation with audio:**
```bash
ffmpeg -f concat -safe 0 -i concat.txt -i audio.mp3 -c:v libx264 -crf 18 -c:a aac -b:a 192k output.mp4
```

**Image loop with audio:**
```bash
ffmpeg -loop 1 -i image.png -i audio.mp3 -c:v libx264 -t DURATION -pix_fmt yuv420p output.mp4
```

**With overlays and livestreaming:**
```bash
ffmpeg -re -stream_loop -1 -f concat -safe 0 -i videos.txt -stream_loop -1 -i audio.mp3 \
  -filter_complex "[0:v]scale=1920:1080,fps=30[scaled];[scaled]overlay=W-w-20:20[vout]" \
  -map "[vout]" -map 1:a -c:v h264_nvenc -preset p6 -tune ll -rc cbr \
  -b:v 4500k -maxrate 4500k -bufsize 9000k -c:a aac -b:a 128k \
  -f flv rtmp://a.rtmp.youtube.com/live2/YOUR_STREAM_KEY
```

## 🐛 Troubleshooting

### FFmpeg not found
- Ensure FFmpeg is installed and the path is correctly configured in Settings
- Use the "Auto-detect" button to find FFmpeg in system PATH
- Manually browse to the ffmpeg.exe location

### Export fails immediately
- Check the FFmpeg log output for error messages
- Ensure all source files exist and are readable
- Verify sufficient disk space for output

### No audio in output
- Ensure audio directory contains supported formats (.mp3, .wav, .aac, etc.)
- Check if audio file is corrupted

### Livestream connection failed
- Verify your YouTube stream key is correct
- Check your internet connection
- Ensure you've started a stream in YouTube Studio first
- Try restarting the stream

### Multiple jobs not working
- Check if FFmpeg path is correctly configured
- Ensure sufficient system resources (CPU, RAM)
- GPU encoding (NVENC) requires NVIDIA graphics card

### Preview not working
- Install required media codecs
- Try a different video file format

## 🎯 Multi-Job Examples

### Scenario 1: Export while livestreaming
1. Start a livestream to YouTube
2. While streaming, configure and start a video export
3. Both will run simultaneously without interference

### Scenario 2: Multiple livestreams
1. Configure first stream (e.g., 1080p channel A)
2. Start streaming
3. Switch to different media/settings
4. Start second stream (e.g., 720p channel B)
5. Monitor both in Job Monitor

### Scenario 3: Batch exports
1. Configure export settings for first video
2. Start export
3. Change media selection and settings
4. Start another export
5. Repeat as needed - all exports run in parallel

## 📄 License

This project is provided as-is for educational and personal use.

## 🆕 What's New in v2.0

- **YouTube Livestreaming**: Stream directly to YouTube with RTMP
- **⏰ Scheduled Streaming (NEW!)**: Automatic stream scheduling with Once/Daily/Weekly modes
- **Multi-Job Support**: Run multiple exports/streams simultaneously
- **Job Monitor**: Real-time tracking of all active and completed jobs
- **Auto-Stop Streaming**: Set duration limits for automatic stream termination
- **Toggle Preview**: Hide preview panel for more workspace
- **GPU Encoding**: Optimized NVENC support for livestreaming
- **Improved UI**: Renamed to MediaKit Pro with enhanced interface

### Scheduled Streaming Features:
- ⏰ Schedule streams without YouTube API
- 📅 Three modes: Once, Daily, Weekly
- 🔄 Recurring schedules with weekday selection
- ⏱️ Auto-stop or infinite duration
- 📋 Manage multiple schedules
- ✅ Enable/disable schedules on demand
- 💾 Persistent storage (survives app restart)

See [FITUR_JADWAL_LIVESTREAM.md](FITUR_JADWAL_LIVESTREAM.md) for complete scheduling guide.

## 🙏 Acknowledgments

- [FFmpeg](https://ffmpeg.org/) - The backbone of video processing
- [PySide6](https://doc.qt.io/qtforpython/) - Qt for Python
- [Qt](https://www.qt.io/) - Cross-platform application framework
