# 🔴 Panduan Livestreaming - MediaKit Pro

## Cara Mendapatkan Stream Key YouTube

1. Buka [YouTube Studio](https://studio.youtube.com)
2. Klik menu **"Go Live"** atau **"Mulai Streaming"**
3. Pilih **"Stream"** (bukan webcam)
4. Di bagian **"Stream Settings"**, copy **"Stream Key"**
5. **PENTING**: Jangan bagikan stream key ke siapapun!

---

## Setup Livestream Pertama Kali

### 1. Persiapan Media
- **Video**: Siapkan folder berisi video-video yang akan diputar
- **Audio**: Siapkan folder berisi musik/audio
- **Logo** (opsional): File PNG/JPG untuk watermark
- **Text** (opsional): Teks yang akan ditampilkan di video

### 2. Konfigurasi di MediaKit Pro

#### Tab MEDIA:
```
☑️ Pilih mode:
   • Video Directory (untuk video multiple)
   • Static Image (untuk background gambar)

☑️ Pilih file:
   • Video Directory: Pilih folder video
   • Cover Video (opsional): Video pembuka
   • Audio Directory: Pilih folder musik

☑️ Loop Mode:
   • Match Audio Duration (recommended untuk livestream)
```

#### Tab EFFECTS (Opsional):
```
☑️ Logo Overlay:
   • Enable: ✓
   • Select File: Pilih logo PNG
   • Size: 15-20% (recommended)
   • Position: Bottom Right (BR)

☑️ Text Overlay:
   • Enable: ✓
   • Text: "Subscribe!" atau channel name
   • Font Size: 40-60
   • Color: White atau sesuai branding
   • Position: Bottom Center
```

#### Tab LIVESTREAM:
```
☑️ Stream Destination:
   • RTMP URL: rtmp://a.rtmp.youtube.com/live2/
   • Stream Key: [paste dari YouTube Studio]

☑️ Video Settings:
   • Preset: YouTube 1080p 30fps (recommended)
   • Resolution: 1920x1080
   • Frame Rate: 30 fps
   • Video Bitrate: 4500 kbps
   • Encoding: nvenc_hq (jika punya NVIDIA GPU)

☑️ Audio Settings:
   • Audio Bitrate: 128 kbps

☑️ Stream Duration:
   • Auto-stop: OFF (untuk stream terus menerus)
   • Atau: ON dengan durasi tertentu (misalnya 60 menit)
```

### 3. Mulai Streaming

1. Pastikan di YouTube Studio, stream sudah di-create
2. Klik tombol **"🔴 START LIVESTREAM"**
3. Tunggu popup konfirmasi
4. Klik **"📊"** (Job Monitor) untuk lihat status
5. Tunggu 10-30 detik, cek YouTube apakah stream sudah muncul

---

## Tips & Best Practices

### Kualitas Stream

| Resolusi | FPS | Bitrate | Internet Upload |
|----------|-----|---------|-----------------|
| 720p | 30 | 3000 kbps | Min 5 Mbps |
| 1080p | 30 | 4500 kbps | Min 7 Mbps |
| 1080p | 60 | 9000 kbps | Min 13 Mbps |

**Recommended**: Test dulu dengan 720p 30fps sebelum naik ke 1080p

### Encoding Settings

- **NVENC** (NVIDIA GPU):
  - Paling cepat dan efisien
  - Minimal GTX 1050 atau lebih baru
  - Pilihan terbaik untuk multi-stream

- **NVENC_HQ** (High Quality):
  - Kualitas lebih bagus
  - Sedikit lebih lambat
  - Recommended untuk single stream

- **x264** (CPU):
  - Fallback jika tidak ada GPU
  - Lebih lambat dan berat
  - Bisa overheat jika multi-stream

### Durasi Stream

**Mode 1: Infinite Loop**
```
✓ Auto-stop: OFF
✓ Video dan audio akan loop terus
✓ Stop manual lewat Job Monitor
✓ Cocok untuk: 24/7 stream, afk stream
```

**Mode 2: Timed Stream**
```
✓ Auto-stop: ON
✓ Set durasi (misalnya 120 menit)
✓ Otomatis stop setelah waktu habis
✓ Cocok untuk: scheduled stream, auto-pilot
```

### Kombinasi Media

**Contoh 1: Music Radio**
```
• Video: 1 static image (background)
• Audio: Folder berisi 50 lagu
• Logo: Channel logo di pojok
• Text: "Lofi Music Radio 24/7"
• Duration: Infinite
```

**Contoh 2: Video Compilation**
```
• Video: Folder berisi 20 video klip
• Audio: Folder berisi 10 soundtrack
• Cover Video: Intro 10 detik
• Logo: Watermark
• Duration: 60 menit (auto-stop)
```

**Contoh 3: Gameplay Loop**
```
• Video: Folder berisi 5 gameplay video
• Audio: Background music folder
• Text: "Best Moments | Subscribe!"
• Logo: Channel logo
• Duration: Infinite
```

---

## Multi-Stream Setup

### Skenario: 2 Channel Bersamaan

**Channel A - Main Channel (1080p)**
1. Setup media untuk channel A
2. Enter stream key channel A
3. Preset: YouTube 1080p 30fps
4. Start stream A
5. Buka Job Monitor

**Channel B - Secondary Channel (720p)**
1. Ganti media di tab MEDIA
2. Ganti stream key di tab LIVESTREAM
3. Preset: YouTube 720p 30fps
4. Start stream B
5. Job Monitor akan show 2 streams running

**Monitoring:**
- Job Monitor menampilkan semua stream
- Masing-masing punya logs independen
- Bisa stop salah satu tanpa ganggu yang lain

---

## Troubleshooting Livestream

### ❌ "Stream key is required"
**Solusi:** Paste stream key dari YouTube Studio

### ❌ "FFmpeg Not Configured"
**Solusi:** 
1. Klik ⚙️ (Settings)
2. Browse ke `ffmpeg.exe`
3. Atau klik "Auto-detect FFmpeg"

### ❌ Stream tidak muncul di YouTube
**Cek:**
- Stream sudah di-create di YouTube Studio?
- Stream key sudah benar?
- Tunggu 30 detik
- Refresh halaman YouTube
- Cek koneksi internet

### ❌ Stream buffering/lagging
**Solusi:**
- Turunkan bitrate (misalnya 3000 kbps)
- Turunkan resolusi (720p)
- Turunkan FPS (30 fps)
- Close aplikasi lain
- Cek bandwidth dengan speedtest

### ❌ "Failed to start livestream"
**Cek:**
- FFmpeg path benar?
- Video/audio files bisa dibaca?
- Ada koneksi internet?
- Firewall tidak block RTMP?

### ❌ CPU 100% / Overheat
**Solusi:**
- Gunakan GPU encoding (NVENC)
- Turunkan resolusi
- Tutup stream yang tidak perlu
- Stop aplikasi lain yang berat

### ❌ Audio tidak sync
**Solusi:**
- Gunakan audio dengan sample rate yang sama (44100 Hz)
- Jangan mix MP3 dan WAV dalam satu folder
- Gunakan audio multiplier 1x saja

---

## Checklist Sebelum Stream

- [ ] FFmpeg sudah configured
- [ ] Stream sudah di-create di YouTube Studio
- [ ] Stream key sudah di-copy
- [ ] Video files siap dan bisa dibuka
- [ ] Audio files siap dan bisa dibuka
- [ ] Logo/Text sudah dikonfigurasi (jika pakai)
- [ ] Test internet speed (min 5 Mbps upload untuk 720p)
- [ ] GPU drivers up to date (jika pakai NVENC)
- [ ] Cukup storage untuk temp files
- [ ] Close aplikasi berat lainnya

---

## FAQ

### Q: Berapa lama bisa stream?
**A:** Tidak ada limit di MediaKit Pro. Tapi YouTube punya limit 12 jam per stream. Setelah 12 jam, create stream baru.

### Q: Bisa ganti media saat stream running?
**A:** Tidak. Media di-lock saat stream mulai. Kalau mau ganti, stop stream, ganti media, start stream baru.

### Q: Bisa stream ke Twitch/Facebook?
**A:** Saat ini hanya YouTube. Support platform lain coming soon.

### Q: Berapa banyak stream simultan yang aman?
**A:** Tergantung hardware. 1 NVIDIA GPU bisa handle 2-3 stream 1080p. Untuk lebih, butuh GPU lebih powerful.

### Q: Stream quality bagus tapi viewer bilang lag?
**A:** Itu masalah di sisi viewer. Pastikan mereka pilih quality yang sesuai koneksi mereka di YouTube.

### Q: Temporary files dimana?
**A:** Di system temp folder. Otomatis dihapus saat stream stop.

### Q: Bisa schedule stream otomatis?
**A:** Gunakan auto-stop duration, tapi start masih manual. Auto-start coming soon.

---

**Selamat Streaming! 🎉**

Jika ada masalah, cek Job Monitor untuk detail logs FFmpeg.

