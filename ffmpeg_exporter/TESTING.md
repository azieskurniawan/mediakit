# MediaKit Pro - Testing Guide

## Multi-Job Testing Scenarios

### ✅ Scenario 1: Single Export
**Steps:**
1. Launch MediaKit Pro
2. Go to MEDIA tab
3. Select video directory or static image
4. Select audio directory
5. (Optional) Configure effects in EFFECTS tab
6. Click "EXPORT VIDEO"
7. Configure export settings
8. Click "EXPORT VIDEO" in dialog
9. Monitor real-time FFmpeg logs

**Expected Result:**
- Export job appears in Job Monitor (if opened)
- Real-time logs display in export dialog
- Progress updates shown
- On completion, video file created in output directory

---

### ✅ Scenario 2: Single Livestream
**Steps:**
1. Launch MediaKit Pro
2. Go to MEDIA tab and configure media (videos/audio)
3. (Optional) Add logo/text in EFFECTS tab
4. Go to LIVESTREAM tab
5. Enter YouTube stream key
6. Select preset (e.g., "YouTube 1080p 30fps")
7. (Optional) Enable auto-stop with duration
8. Click "🔴 START LIVESTREAM"
9. Open Job Monitor (📊 button)
10. Verify stream is running

**Expected Result:**
- Livestream starts immediately
- Job Monitor shows running stream
- Real-time FFmpeg logs visible in Job Monitor
- Stream key hidden by default
- YouTube should receive stream

---

### ✅ Scenario 3: Export While Livestreaming
**Steps:**
1. Start a livestream (follow Scenario 2)
2. Without stopping stream, go back to MEDIA tab
3. Change media selection if desired
4. Click "EXPORT VIDEO"
5. Configure and start export
6. Open Job Monitor

**Expected Result:**
- Both jobs visible in Job Monitor
- Both show "Running" status
- Each has independent logs
- No interference between jobs
- Both complete successfully

---

### ✅ Scenario 4: Multiple Simultaneous Exports
**Steps:**
1. Configure media and start first export
2. While first export is running, change media settings
3. Start second export with different output filename
4. Repeat for third export
5. Monitor all in Job Monitor

**Expected Result:**
- All exports run in parallel
- Each shows independent progress
- CPU/GPU utilization increases
- All complete successfully
- All output files created

---

### ✅ Scenario 5: Multiple Livestreams (Different Channels)
**Steps:**
1. Setup first stream configuration
2. Enter stream key for Channel A
3. Start stream A
4. Change media/settings if needed
5. Go to LIVESTREAM tab
6. Enter stream key for Channel B
7. Start stream B
8. Open Job Monitor

**Expected Result:**
- Both streams run simultaneously
- Each appears as separate job
- Both show running status
- Independent FFmpeg processes
- Both channels receive streams

---

### ✅ Scenario 6: Stop Running Job
**Steps:**
1. Start any job (export or stream)
2. Open Job Monitor
3. Select the running job
4. Click "⏹ Stop Job"
5. Confirm the action

**Expected Result:**
- Job status changes to "Cancelled"
- FFmpeg process terminates
- Temporary files cleaned up
- Job remains in history

---

### ✅ Scenario 7: Auto-Stop Livestream
**Steps:**
1. Configure livestream
2. Enable "Auto-stop after"
3. Set duration (e.g., 2 minutes for testing)
4. Start stream
5. Wait for specified duration
6. Check Job Monitor

**Expected Result:**
- Stream runs for exact duration
- Automatically stops after time expires
- Job status changes to "Completed"
- No manual intervention needed

---

### ✅ Scenario 8: Remove Completed Jobs
**Steps:**
1. Complete several jobs (exports/streams)
2. Open Job Monitor
3. Select a completed job
4. Click "🗑 Remove"

**Expected Result:**
- Job removed from history
- Temporary files cleaned up
- Job no longer visible in list
- Cannot remove running jobs

---

### ✅ Scenario 9: Preview Toggle
**Steps:**
1. Launch app (preview visible by default)
2. Click "👁" button in header
3. Preview panel hides
4. Click "👁" again
5. Preview panel reappears

**Expected Result:**
- Preview toggles on/off smoothly
- More space for left panel when hidden
- State remembered during session
- No impact on functionality

---

### ✅ Scenario 10: Job Monitor Live Logs
**Steps:**
1. Start an export or stream
2. Open Job Monitor immediately
3. Select the running job
4. Watch logs in real-time

**Expected Result:**
- FFmpeg logs appear line by line
- No lag or buffering
- Logs auto-scroll
- Can see progress information
- Duration updates every second

---

## Performance Notes

### Resource Usage
- **Single Export**: ~15-30% CPU (GPU encoding), ~1-2 GB RAM
- **Single Stream**: ~20-40% CPU (realtime encoding), ~1-2 GB RAM
- **Multiple Jobs**: Linear scaling (2 exports = ~2x resources)
- **GPU Encoding (NVENC)**: Offloads to GPU, lower CPU usage

### Recommended Limits
- **Exports**: Up to 4 simultaneous (depends on hardware)
- **Streams**: Up to 2-3 simultaneous (network bandwidth dependent)
- **Mixed**: 1-2 streams + 1-2 exports safely

### System Requirements
- **Minimum**: 4 cores CPU, 8 GB RAM, 10 Mbps upload (for streaming)
- **Recommended**: 6+ cores CPU, 16 GB RAM, NVIDIA GPU, 20+ Mbps upload

---

## Known Limitations

1. **Stream Key Security**: Stored in memory only, cleared on app close
2. **Network Issues**: No automatic reconnection for streams
3. **FFmpeg Errors**: Displayed but not parsed for specific error types
4. **Job History**: Not persisted between app sessions
5. **Preview**: Limited codec support (OS-dependent)

---

## Troubleshooting

### Job Fails Immediately
- Check FFmpeg path in Settings
- Verify media files exist and are readable
- Check disk space for exports
- Verify internet connection for streams

### Stream Not Appearing on YouTube
- Ensure stream is started in YouTube Studio first
- Verify stream key is correct
- Check firewall/antivirus isn't blocking RTMP
- Wait 10-30 seconds for stream to appear

### High CPU Usage
- Use GPU encoding (NVENC/NVENC_HQ)
- Reduce simultaneous jobs
- Lower resolution/FPS for streams
- Close other applications

### Memory Leaks
- Remove completed jobs from history
- Restart app after many jobs
- Check for large temporary files

---

## Testing Checklist

- [ ] Single export completes successfully
- [ ] Single livestream runs without errors
- [ ] Export + Stream simultaneously works
- [ ] Multiple exports run in parallel
- [ ] Multiple streams (different keys) work
- [ ] Job Monitor shows all jobs correctly
- [ ] Stop job works immediately
- [ ] Remove completed job works
- [ ] Auto-stop stream terminates on time
- [ ] Preview toggle works smoothly
- [ ] Real-time logs appear without lag
- [ ] Temp files cleaned up after jobs
- [ ] App stable after 10+ jobs
- [ ] GPU encoding works (if available)
- [ ] Error messages displayed properly

---

**Last Updated:** December 2025 (v2.0)

