# 🎵 Panduan Subtitle/Lirik dari File SRT

## 📝 Fitur

Aplikasi ini mendukung penambahan subtitle/lirik dari file **SRT** (SubRip Subtitle) yang otomatis ditampilkan di video.

**Keunggulan:**
- ✅ Auto-detect: Otomatis mencari file SRT dengan nama yang sama dengan audio
- ✅ Styling penuh: Kontrol ukuran, warna, outline, posisi
- ✅ Multi-audio: Mendukung beberapa lagu dengan SRT yang berbeda
- ✅ Preview: Lihat hasil styling dengan dummy text sebelum export

---

## 🎯 Cara Kerja

### 1. **Persiapan File**

Pastikan file SRT memiliki **nama yang sama** dengan file audio:

```
📁 Folder Audio/
   ├── 1 - Lagu Pertama.mp3
   ├── 1 - Lagu Pertama.srt  ← Nama sama!
   ├── 2 - Lagu Kedua.mp3
   ├── 2 - Lagu Kedua.srt    ← Nama sama!
   └── 3 - Tanpa Lirik.mp3   ← Tidak ada SRT (OK!)
```

**Penting:** Ekstensi audio (.mp3, .wav, dll) dan subtitle (.srt) berbeda, tapi **nama file harus sama persis**.

### 2. **Format File SRT**

File SRT adalah file teks biasa dengan format:

```srt
1
00:00:10,500 --> 00:00:13,000
♪ Ini baris pertama lirik ♪

2
00:00:13,000 --> 00:00:16,500
♪ Ini baris kedua lirik ♪

3
00:00:16,500 --> 00:00:20,000
♪ Dan seterusnya... ♪
```

**Format:**
- Baris 1: Nomor urut subtitle
- Baris 2: Waktu mulai --> Waktu selesai (HH:MM:SS,mmm)
- Baris 3+: Teks subtitle/lirik
- Baris kosong: Pemisah antar subtitle

**Encoding:** Gunakan UTF-8 untuk support karakter Indonesia/emoji.

---

## 🎨 Penggunaan di Aplikasi

### Step 1: Pilih Audio

1. Buka tab **"Media"**
2. Di bagian **AUDIO**, klik **"+ Add Files"** atau **"+ Add Folder"**
3. Pilih audio yang ingin digunakan

**Info SRT:** Setelah audio dipilih, akan muncul info:
- ✅ `5 audio file(s) selected | 3 file(s) dengan SRT` → Ada SRT
- ⚠ `5 audio file(s) selected | Tidak ada file SRT ditemukan` → Tidak ada SRT

### Step 2: Enable Subtitle

1. Buka tab **"Effects"**
2. Scroll ke bawah ke section **"SUBTITLE / LIRIK (SRT)"**
3. Centang **☑ Tampilkan Subtitle/Lirik dari SRT**

### Step 3: Atur Styling

**Font:**
- **Font (Opsional):** Pilih file .ttf/.otf jika ingin font custom
  - Kosong = font default sistem
- **Ukuran Font:** 12-80 (default: 28)

**Warna:**
- **Warna Teks:** Warna utama subtitle (default: putih)
- **Warna Outline:** Warna tepi teks (default: hitam)
- **Ketebalan Outline:** 0-5 pixel (default: 2)

**Posisi:**
- **Posisi:** Bottom Center (default), Top Center, Center, dll.
- **Margin Vertikal:** Jarak dari tepi (0-200px, default: 60)

### Step 4: Preview

Klik **"👁 Preview Dummy Text"** untuk melihat hasil styling dengan teks contoh:
```
♪ Ini adalah contoh lirik subtitle ♪
♪ Dengan styling yang Anda pilih ♪
```

### Step 5: Export

Lakukan export seperti biasa. Subtitle akan otomatis muncul di video!

---

## 📋 Skenario Penggunaan

### Skenario 1: Semua Lagu Punya SRT

```
📁 Audio/
   ├── song1.mp3 + song1.srt
   ├── song2.mp3 + song2.srt
   └── song3.mp3 + song3.srt
```

**Hasil:** Semua lirik ditampilkan sesuai timing masing-masing lagu.

### Skenario 2: Sebagian Lagu Punya SRT

```
📁 Audio/
   ├── song1.mp3 + song1.srt  ← Ada SRT
   ├── song2.mp3              ← Tidak ada SRT
   └── song3.mp3 + song3.srt  ← Ada SRT
```

**Hasil:** 
- Lagu 1 & 3: Lirik tampil
- Lagu 2: Tidak ada lirik (normal)

### Skenario 3: Tidak Ada SRT

```
📁 Audio/
   ├── song1.mp3
   ├── song2.mp3
   └── song3.mp3
```

**Hasil:** Video dibuat tanpa subtitle (checkbox subtitle tidak berpengaruh).

---

## 🔧 Tips & Trik

### 1. Membuat File SRT

**Cara Manual:**
1. Buka Notepad/Text Editor
2. Tulis format SRT (lihat contoh di atas)
3. Save as → **"nama_lagu.srt"** (BUKAN .txt!)
4. Pilih **"All Files (*.*)"** saat save
5. Encoding: **UTF-8**

**Cara Otomatis:**
- Gunakan software subtitle editor:
  - **Aegisub** (gratis, powerful)
  - **Subtitle Edit** (gratis, mudah)
  - **Subtitle Workshop** (gratis)

### 2. Timing yang Tepat

- Gunakan aplikasi subtitle editor untuk sync timing dengan lagu
- Test dulu 1-2 lagu sebelum membuat semua SRT
- Timing format: `HH:MM:SS,mmm` (jam:menit:detik,milidetik)

### 3. Styling Optimal

**Untuk Video YouTube:**
- Font Size: 28-32
- Warna: White + Black outline (paling terbaca)
- Posisi: Bottom Center
- Margin: 60-80px

**Untuk Video TikTok/Instagram:**
- Font Size: 32-40 (layar lebih kecil)
- Warna: Kontras tinggi (white/yellow + black outline)
- Posisi: Center atau Top Center (hindari UI bawah)

### 4. Multi-Language Support

SRT support berbagai bahasa dengan UTF-8:
- Indonesia: ✅
- English: ✅
- Emoji: ✅ (♪ ♫ 🎵 🎶)
- Karakter khusus: ✅

### 5. Troubleshooting

**❌ Subtitle tidak muncul:**
- Check nama file audio & SRT **sama persis**
- Check checkbox "Tampilkan Subtitle" aktif
- Check file SRT format benar

**❌ Karakter aneh/kotak-kotak:**
- Save file SRT dengan encoding **UTF-8**
- Buka SRT di Notepad → Save As → Encoding: UTF-8

**❌ Timing tidak sync:**
- Jika multiple audio, pastikan setiap SRT timing mulai dari 00:00:00
- Aplikasi akan auto-adjust timing per lagu

---

## 💡 Contoh SRT Lengkap

```srt
1
00:00:00,000 --> 00:00:03,500
♪ Baris pertama intro ♪

2
00:00:03,500 --> 00:00:07,000
♪ Baris kedua verse 1 ♪

3
00:00:07,000 --> 00:00:10,500
♪ Terus sampai chorus ♪

4
00:00:10,500 --> 00:00:14,000
♪ Chorus bisa panjang ♪
♪ Bisa multi-line juga ♪

5
00:00:14,000 --> 00:00:17,500
♪ Dan seterusnya... ♪
```

**Tips:**
- Gunakan simbol musik: ♪ ♫ 🎵
- Multi-line: Enter di dalam 1 subtitle
- Durasi tiap baris: 2-5 detik ideal

---

## 🎬 Workflow Lengkap

1. **Persiapan:**
   ```
   1. Kumpulkan audio files
   2. Buat/download SRT untuk tiap lagu
   3. Pastikan nama file match
   ```

2. **Di Aplikasi:**
   ```
   1. Import audio files
   2. Check info "X file(s) dengan SRT"
   3. Enable subtitle + atur styling
   4. Preview styling
   5. Export!
   ```

3. **Setelah Export:**
   ```
   1. Cek hasil video
   2. Jika timing kurang pas, edit SRT
   3. Re-export (cepat karena tidak perlu render ulang)
   ```

---

## 🆘 FAQ

**Q: Apakah harus semua audio punya SRT?**  
A: Tidak! Bisa sebagian saja, atau bahkan tidak ada sama sekali.

**Q: Bisa ganti styling di tengah video?**  
A: Tidak untuk sekarang. Styling berlaku untuk SEMUA subtitle.

**Q: Format subtitle lain (ASS, VTT) support?**  
A: Saat ini hanya SRT. Convert dulu ke SRT jika pakai format lain.

**Q: Subtitle bisa ditaruh di posisi custom pixel?**  
A: Ya, tapi harus edit manual di code. Untuk sekarang gunakan preset posisi.

**Q: Bisa pakai font system tanpa file TTF?**  
A: Ya! Kosongkan "Font (Opsional)" untuk pakai font default sistem.

---

## 📚 Resource Tambahan

**Download Font Gratis:**
- Google Fonts: https://fonts.google.com
- DaFont: https://www.dafont.com
- Font Squirrel: https://www.fontsquirrel.com

**Subtitle Editor:**
- Aegisub: http://www.aegisub.org
- Subtitle Edit: https://www.nikse.dk/subtitleedit

**Konversi Subtitle Format:**
- Subtitle Tools: https://subtitletools.com

---

🎉 **Selamat Berkreasi!**
