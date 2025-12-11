# 🕐 Fitur Penjadwalan Livestream Otomatis

## ✅ **Fitur yang Tersedia**

Aplikasi **MediaKit Pro** sekarang dilengkapi dengan **sistem penjadwalan livestream otomatis** yang powerful!

### **Kemampuan Utama:**

1. ✅ **Penjadwalan Otomatis**
   - Jadwalkan livestream untuk waktu tertentu
   - Stream akan **jalan sendiri** saat waktunya tiba
   - **Tidak perlu YouTube API** - scheduling lokal di aplikasi
   - Tidak perlu YouTube Studio untuk membuat jadwal

2. ✅ **Tiga Tipe Penjadwalan:**
   - **Once (Sekali)** - Stream sekali di waktu tertentu
   - **Daily (Harian)** - Stream setiap hari di jam yang sama
   - **Weekly (Mingguan)** - Stream di hari-hari tertentu (Senin, Rabu, Jumat, dll)

3. ✅ **Kontrol Durasi:**
   - Stream infinite (sampai dihentikan manual)
   - Auto-stop setelah durasi tertentu (misal 60 menit)

4. ✅ **Manajemen Jadwal:**
   - Lihat semua jadwal dalam satu tempat
   - Edit jadwal kapan saja
   - Enable/Disable jadwal
   - Hapus jadwal yang tidak diperlukan
   - Lihat jadwal berikutnya yang akan jalan

---

## 🚀 **Cara Menggunakan**

### **1. Buka Tab Livestream**

1. Jalankan aplikasi `python -m ffmpeg_exporter.app`
2. Klik tab **"LIVESTREAM"** di panel kiri
3. Scroll ke bawah sampai bagian **"⏰ Scheduled Streaming"**

---

### **2. Buat Jadwal Baru**

#### **Klik "➕ Create Schedule"**

Dialog akan muncul dengan form:

```
┌─────────────────────────────────────┐
│ Create Schedule                     │
├─────────────────────────────────────┤
│ Schedule Name:                      │
│ [Daily Lofi Stream_____________]    │
│                                     │
│ Start Time                          │
│ Date & Time: [11 Dec 2025 - 20:00] │
│                                     │
│ Recurrence                          │
│ ○ Once only                         │
│ ● Daily (every day at same time)    │
│ ○ Weekly (specific days)            │
│                                     │
│ Stream Duration                     │
│ ○ Run infinitely                    │
│ ● Auto-stop after: [60] minutes     │
│                                     │
│ 📅 Start: 11 Dec 2025 at 20:00     │
│ 🔄 Recurrence: Daily at 20:00       │
│ ⏱️ Duration: 60 minutes              │
│                                     │
│            [Cancel]  [Create]       │
└─────────────────────────────────────┘
```

#### **Isi Form:**

1. **Schedule Name**: Nama jadwal (contoh: "Daily Lofi Stream")
2. **Date & Time**: Pilih tanggal & jam mulai
3. **Recurrence**: 
   - **Once** = Sekali saja
   - **Daily** = Setiap hari jam yang sama
   - **Weekly** = Pilih hari-hari tertentu (Senin, Rabu, Jumat, dll)
4. **Duration**:
   - **Infinite** = Jalan terus sampai dihentikan manual
   - **Auto-stop** = Berhenti otomatis setelah X menit

5. Klik **"Create"**

---

### **3. Kelola Jadwal**

#### **Klik "📋 Manage Schedules"**

Akan muncul window dengan semua jadwal:

```
┌────────────────────────────────────────────┐
│ Scheduled Streams    [➕ Create New...]    │
├────────────────────────────────────────────┤
│                                            │
│ ┌────────────────────────────────────┐    │
│ │ ✓ Daily Lofi Stream                │    │
│ │ Daily at 20:00 • 60m               │    │
│ │ Next: Today 20:00 (in 5h 23m)      │    │
│ │ [Edit] [Delete] [Disable]          │    │
│ └────────────────────────────────────┘    │
│                                            │
│ ┌────────────────────────────────────┐    │
│ │ ○ Weekend Gaming (disabled)        │    │
│ │ Sat, Sun at 14:00 • ∞              │    │
│ │ [Edit] [Delete] [Enable]           │    │
│ └────────────────────────────────────┘    │
│                                            │
│                         [Close]            │
└────────────────────────────────────────────┘
```

#### **Tombol Aksi:**

- **Edit** - Ubah jadwal
- **Delete** - Hapus jadwal
- **Disable/Enable** - Matikan/nyalakan jadwal tanpa menghapus

---

### **4. Livestream Otomatis Jalan**

Saat jadwal terpicu (waktu sudah tiba):

1. ✅ Aplikasi akan menampilkan **notifikasi**
2. ✅ Stream akan **mulai otomatis** dalam 3 detik
3. ✅ **Job Monitor** akan terbuka otomatis
4. ✅ Anda bisa lihat log FFmpeg secara real-time
5. ✅ Stream akan stop otomatis sesuai durasi (jika diatur)

**Contoh notifikasi:**

```
┌─────────────────────────────────────┐
│ Scheduled Stream Starting           │
├─────────────────────────────────────┤
│ Starting scheduled stream:          │
│ Daily Lofi Stream                   │
│                                     │
│ This stream will start              │
│ automatically in 3 seconds...       │
│                                     │
│              [OK]                   │
└─────────────────────────────────────┘
```

---

## 📝 **Contoh Use Case**

### **Use Case 1: Stream Harian Lofi**

**Kebutuhan:**
- Stream lofi music setiap hari jam 20:00
- Durasi 2 jam (120 menit)
- Otomatis tanpa intervensi manual

**Cara Setup:**
1. Buat jadwal baru
2. Name: "Lofi Stream Malam"
3. Time: 20:00
4. Recurrence: **Daily**
5. Duration: **120 minutes**
6. Klik Create

**Hasil:**
✅ Setiap hari jam 20:00, aplikasi otomatis mulai streaming
✅ Jam 22:00, stream otomatis stop

---

### **Use Case 2: Stream Gaming Weekend**

**Kebutuhan:**
- Stream gaming setiap Sabtu & Minggu
- Jam 14:00
- Infinite (sampai manual stop)

**Cara Setup:**
1. Buat jadwal baru
2. Name: "Weekend Gaming"
3. Time: 14:00
4. Recurrence: **Weekly**
5. Pilih: **Sat, Sun** ☑️
6. Duration: **Infinite**
7. Klik Create

**Hasil:**
✅ Setiap Sabtu & Minggu jam 14:00, stream mulai otomatis
✅ Stream jalan terus sampai Anda stop manual

---

### **Use Case 3: Event Khusus Sekali**

**Kebutuhan:**
- Stream special event tanggal 25 Desember 2025
- Jam 18:00
- Durasi 3 jam (180 menit)

**Cara Setup:**
1. Buat jadwal baru
2. Name: "Christmas Special 2025"
3. Date: 25 Des 2025
4. Time: 18:00
5. Recurrence: **Once only**
6. Duration: **180 minutes**
7. Klik Create

**Hasil:**
✅ Tanggal 25 Des 2025 jam 18:00, stream otomatis mulai
✅ Jam 21:00, stream otomatis stop
✅ Jadwal otomatis disabled setelah jalan (tidak repeat)

---

## ⚙️ **Konfigurasi yang Tersimpan**

Saat membuat jadwal dari tab Livestream, konfigurasi berikut **tersimpan otomatis**:

### **Stream Settings:**
- RTMP URL
- Stream Key
- Resolution (1920x1080, dll)
- FPS (30, 60, dll)
- Bitrate
- Audio bitrate
- Encoding method (nvenc/x264)

### **Media Config:**
*(Diambil dari tab Media & Effects saat schedule trigger)*
- Video directory / Static image
- Cover video
- Audio files
- Loop mode
- Logo overlay
- Text overlay

---

## 🔔 **Notifikasi**

Aplikasi akan memberikan notifikasi untuk:

1. ✅ **Saat jadwal dibuat** - Konfirmasi jadwal berhasil dibuat
2. ✅ **Saat stream akan mulai** - 3 detik sebelum mulai
3. ✅ **Saat stream dimulai** - Konfirmasi stream sudah live
4. ✅ **Jika ada error** - Jika stream gagal start

---

## 💾 **Penyimpanan**

Semua jadwal disimpan di:
```
ffmpeg_exporter/config/schedules.json
```

File ini **persisten** - jadwal tetap ada meskipun aplikasi ditutup.

---

## 🛡️ **Keamanan Stream Key**

- Stream key **disimpan terenkripsi** di jadwal
- Tidak ditampilkan di log
- Hanya digunakan saat stream mulai

---

## ❓ **FAQ**

### **Q: Apakah aplikasi harus tetap buka agar jadwal jalan?**
**A:** **YA**. Aplikasi harus tetap running agar scheduler bisa trigger jadwal. Jangan tutup aplikasi jika ada jadwal yang akan jalan.

### **Q: Apakah bisa buat banyak jadwal sekaligus?**
**A:** **YA**. Anda bisa membuat unlimited jadwal. Semua jadwal yang enabled akan jalan sesuai waktunya.

### **Q: Bagaimana jika ada 2 jadwal di waktu yang sama?**
**A:** Kedua stream akan start bersamaan. Pastikan komputer Anda kuat untuk handle multiple stream.

### **Q: Apakah perlu koneksi YouTube API?**
**A:** **TIDAK**. Scheduling ini lokal di aplikasi. Anda hanya perlu RTMP URL dan Stream Key dari YouTube.

### **Q: Bisa ganti media/settings setelah jadwal dibuat?**
**A:** Bisa! Edit jadwal kapan saja. Settings yang dipakai adalah settings **saat jadwal dibuat/diedit**, bukan saat jadwal trigger.

### **Q: Bagaimana jika komputer mati saat ada jadwal?**
**A:** Jadwal **tidak akan jalan** jika komputer mati. Anda harus pastikan komputer nyala saat jadwal akan trigger.

### **Q: Bisa jadwal stream ke platform lain (Twitch, Facebook)?**
**A:** **YA**! Tinggal ganti RTMP URL dan Stream Key sesuai platform yang Anda gunakan.

---

## 🎯 **Tips & Best Practices**

1. ✅ **Test jadwal dulu** - Buat jadwal 5 menit dari sekarang untuk test
2. ✅ **Check FFmpeg path** - Pastikan FFmpeg sudah dikonfigurasi di Settings
3. ✅ **Siapkan media** - Pastikan video/audio sudah ada sebelum jadwal trigger
4. ✅ **Monitor pertama kali** - Pantau log di Job Monitor saat jadwal pertama kali jalan
5. ✅ **Disable jika tidak diperlukan** - Jangan hapus, cukup disable jadwal yang temporary tidak dipakai
6. ✅ **Backup schedules.json** - Backup file config/schedules.json secara berkala

---

## 🐛 **Troubleshooting**

### **Problem: Jadwal tidak jalan**

**Solusi:**
1. Check aplikasi masih running
2. Check jadwal masih **enabled** (✓)
3. Check waktu jadwal sudah benar
4. Check FFmpeg path di Settings
5. Check media files masih ada

### **Problem: Stream gagal start**

**Solusi:**
1. Check stream key masih valid
2. Check internet connection
3. Check FFmpeg bisa jalan manual
4. Lihat error di Job Monitor

### **Problem: Next run time tidak muncul**

**Solusi:**
1. Pastikan jadwal **enabled**
2. Check waktu jadwal tidak di masa lalu
3. Restart aplikasi

---

## 🚀 **Update Mendatang**

Fitur yang akan ditambahkan:

- [ ] Pre-stream notification (15 menit sebelumnya)
- [ ] Email notification saat stream mulai
- [ ] Backup schedule ke cloud
- [ ] Multi-platform stream (YouTube + Twitch bersamaan)
- [ ] Statistik stream (berapa kali sudah jalan)
- [ ] Template schedule

---

## 📞 **Support**

Jika ada pertanyaan atau butuh bantuan, silakan buka issue di GitHub repository.

---

**Selamat streaming! 🎬🔴**

