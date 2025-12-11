# 🚀 Quick Start Guide - MediaKit Pro

## 1️⃣ Installation (5 menit)

### Windows
```bash
# 1. Clone/Download project
cd C:\Project\Python\exportVideo

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
cd ffmpeg_exporter
pip install -r requirements.txt

# 5. Run aplikasi
python app.py
```

### First Launch Setup
1. Aplikasi akan terbuka
2. Klik **⚙** (Settings)
3. Klik **"Auto-detect FFmpeg"** atau browse ke `ffmpeg.exe`
4. Klik **"Save"**

✅ Setup selesai!

---

## 2️⃣ Export Video Pertama (5 menit)

### Langkah-langkah:

**1. MEDIA Tab:**
```
☐ Pilih "Video Directory"
☐ Browse ke folder video Anda
☐ (Opsional) Pilih cover video
☐ Browse ke folder audio Anda
☐ Loop Mode: "Match Audio Duration"
```

**2. EFFECTS Tab (Opsional):**
```
☐ Skip dulu untuk test pertama
```

**3. Export:**
```
☐ Klik "EXPORT VIDEO"
☐ Preset: "YouTube 1080p (FHD)"
☐ Output filename: "test_video.mp4"
☐ Output directory: pilih folder output
☐ Klik "EXPORT VIDEO"
```

**4. Monitor:**
```
☐ Lihat real-time logs
☐ Tunggu sampai selesai (beberapa menit)
☐ Video siap di folder output!
```

---

## 3️⃣ Livestream Pertama ke YouTube (10 menit)

### Persiapan YouTube:

1. Buka [YouTube Studio](https://studio.youtube.com)
2. Klik **"Go Live"** → **"Stream"**
3. Copy **Stream Key** Anda

### Di MediaKit Pro:

**1. MEDIA Tab:**
```
☐ Video Directory: pilih folder video
☐ Audio Directory: pilih folder musik
```

**2. EFFECTS Tab (Opsional):**
```
☐ Enable Logo Overlay
  • Select File: logo.png
  • Size: 15%
  • Position: Bottom Right (BR)

☐ Enable Text Overlay
  • Text: "Subscribe!"
  • Font Size: 48
  • Color: #ffffff (white)
  • Position: Bottom Center
```

**3. LIVESTREAM Tab:**
```
☐ RTMP URL: rtmp://a.rtmp.youtube.com/live2/
☐ Stream Key: [paste dari YouTube]
☐ Preset: "YouTube 1080p 30fps"
☐ Auto-stop: OFF (untuk stream terus menerus)
☐ Klik "🔴 START LIVESTREAM"
```

**4. Monitor:**
```
☐ Klik "📊" (Job Monitor)
☐ Lihat status "Running"
☐ Tunggu 30 detik
☐ Refresh YouTube Studio → Stream live! 🔴
```

### Stop Stream:
```
☐ Buka Job Monitor (📊)
☐ Pilih stream yang running
☐ Klik "⏹ Stop Job"
☐ Confirm → Stream berhenti
```

---

## 4️⃣ Multi-Job Demo (5 menit)

### Export 2 Video Sekaligus:

**Video 1:**
```
1. MEDIA: Pilih folder video A + audio A
2. EXPORT VIDEO → filename: "video1.mp4"
3. Start export
```

**Video 2 (saat video 1 masih running):**
```
1. MEDIA: Pilih folder video B + audio B
2. EXPORT VIDEO → filename: "video2.mp4"
3. Start export
```

**Monitor:**
```
☐ Job Monitor shows 2 exports running
☐ Each has own progress
☐ Both complete independently
```

### Export + Livestream Bersamaan:

**Step 1: Start Livestream**
```
1. Setup media + livestream settings
2. Start stream
```

**Step 2: Start Export (stream tetap jalan)**
```
1. Ganti media settings
2. Export video baru
```

**Result:**
```
✓ Stream tetap live di YouTube
✓ Export berjalan paralel
✓ Tidak saling ganggu
```

---

## 5️⃣ Tips & Tricks

### 🎯 Kualitas Stream

**Test koneksi dulu:**
```bash
# Speedtest
# Upload speed minimal:
• 720p 30fps  = 5 Mbps
• 1080p 30fps = 7 Mbps
• 1080p 60fps = 13 Mbps
```

**Mulai dari yang rendah:**
```
1. Test dulu: 720p 30fps
2. Kalau lancar, naik ke 1080p 30fps
3. Kalau masih lancar, naik ke 1080p 60fps
```

### 💻 Performance

**Kalau lag/berat:**
```
☐ Gunakan GPU encoding (NVENC)
☐ Tutup aplikasi lain
☐ Turunkan resolusi/FPS
☐ Batasi jumlah jobs (max 2-3)
```

**Untuk 24/7 stream:**
```
☐ Auto-stop: OFF
☐ Encoding: NVENC (lebih stabil)
☐ Monitor suhu CPU/GPU
☐ Pastikan listrik stabil
```

### 🔧 Troubleshooting Cepat

**FFmpeg not found:**
```
Settings → Auto-detect FFmpeg
atau
Settings → Browse → pilih ffmpeg.exe
```

**Stream tidak muncul di YouTube:**
```
1. Cek stream key benar?
2. Tunggu 30-60 detik
3. Refresh YouTube Studio
4. Cek koneksi internet
```

**Export/Stream gagal:**
```
1. Buka Job Monitor
2. Lihat FFmpeg logs (bagian bawah)
3. Cari kata "error" di logs
4. Biasanya: file not found, codec issue, atau disk full
```

---

## 6️⃣ Shortcuts

| Action | Method |
|--------|--------|
| Open Settings | Klik **⚙** |
| Open Job Monitor | Klik **📊** |
| Toggle Preview | Klik **👁** |
| Start Export | Klik **EXPORT VIDEO** |
| Start Stream | Go to LIVESTREAM tab → Klik **🔴 START** |
| Stop Job | Job Monitor → Select → **⏹ Stop Job** |

---

## 7️⃣ Common Workflows

### Workflow 1: Daily Video Export
```
Morning Routine:
1. Open MediaKit Pro
2. MEDIA: Select today's clips + music
3. EFFECTS: Add logo + date text
4. EXPORT: YouTube 1080p preset
5. Upload ke YouTube saat selesai
```

### Workflow 2: 24/7 Lofi Stream
```
Setup Once:
1. MEDIA: 1 lofi background image + folder musik lofi
2. EFFECTS: Channel logo + "Lofi Radio 24/7" text
3. LIVESTREAM: 1080p 30fps, auto-stop OFF
4. Start → Biarkan running
5. Monitor sekali-kali via Job Monitor
```

### Workflow 3: Compilation Channel
```
Weekly Batch:
1. Prepare 7 compilation videos
2. Setup Media for Video 1
3. Export Video 1
4. Immediately setup Video 2 and export (parallel)
5. Setup Video 3 and export (parallel)
6. Max 2-3 exports running bersamaan
7. Monitor via Job Monitor
8. All 7 videos done in fraction of time!
```

### Workflow 4: Multi-Channel Streaming
```
Channel A (Main):
1. Setup premium content
2. Stream 1080p 60fps
3. Start stream A

Channel B (Secondary):
1. Change to different media
2. Stream 720p 30fps
3. Start stream B

Monitor both in Job Monitor
Both run independently
```

---

## 📚 Next Steps

Setelah familiar dengan basics:

1. **Explore Effects:**
   - Coba berbagai posisi logo
   - Experiment dengan text overlay
   - Mix and match effects

2. **Optimize Settings:**
   - Test berbagai encoding methods
   - Find sweet spot bitrate untuk internet Anda
   - Compare GPU vs CPU encoding

3. **Advanced Usage:**
   - Multi-stream different channels
   - Batch export workflows
   - Schedule streams dengan auto-stop

4. **Read Full Documentation:**
   - `README.md` - Complete features
   - `LIVESTREAM_GUIDE_ID.md` - Panduan lengkap streaming
   - `TESTING.md` - Test scenarios
   - `ARCHITECTURE.md` - Technical details

---

## ✅ Checklist Sebelum Production

- [ ] FFmpeg configured dan working
- [ ] Test export berhasil (1 video)
- [ ] Test livestream berhasil (5 menit test)
- [ ] Understand Job Monitor
- [ ] Tahu cara stop job
- [ ] Backup files penting
- [ ] Test koneksi internet stabil

---

## 🎉 You're Ready!

**Export pertama:**  ✅  
**Livestream pertama:**  ✅  
**Multi-job:**  ✅  

Sekarang tinggal:
- Buat content
- Atur schedule
- Start automation
- Grow channel! 🚀

---

**Need Help?**
- Check `LIVESTREAM_GUIDE_ID.md` untuk troubleshooting
- Check `TESTING.md` untuk test scenarios
- Check FFmpeg logs di Job Monitor untuk errors

**Happy Creating! 🎬✨**

