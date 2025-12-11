# 🎵 Audio Source Modes - MediaKit Pro

## ✨ Fitur Baru: 3 Mode Audio Source

Sekarang Anda punya **3 pilihan** untuk sumber audio dalam export dan livestream!

---

## 📊 3 Mode Audio Source

### 1️⃣ **🎵 Audio Directory (Replace)** - DEFAULT
**Deskripsi:**  
- Menggunakan audio dari **Audio Directory**
- Audio original dari video **DIGANTI** dengan musik dari Audio Directory
- Behavior yang sama seperti versi sebelumnya

**Kapan pakai:**
- Buat music video compilation
- Lofi stream dengan background music
- Video montage dengan soundtrack terpisah

**Contoh:**
```
Input:
  Video: gameplay1.mp4 (ada suara game)
  Audio Directory: lofi1.mp3, lofi2.mp3

Output:
  Video: gameplay visual
  Audio: lofi1.mp3 + lofi2.mp3 (suara game hilang)
```

---

### 2️⃣ **🎬 Video Original Audio** - NEW!
**Deskripsi:**  
- Menggunakan audio **dari video itu sendiri**
- Audio Directory **TIDAK dipakai**
- Perfect untuk video yang sudah punya audio bagus

**Kapan pakai:**
- Video sudah ada narasi/dialog
- Gaming footage dengan commentary
- Vlog atau tutorial
- Music performance video

**Contoh:**
```
Input:
  Video: tutorial.mp4 (ada suara narasi)
  Audio Directory: (tidak dipakai)

Output:
  Video: tutorial visual
  Audio: narasi dari video original
```

**Catatan:**
- Audio Directory tetap bisa diisi tapi tidak akan digunakan
- Untuk static image mode, opsi ini tidak tersedia (error)

---

### 3️⃣ **🎚️ Mix Both (Video + Music)** - NEW!
**Deskripsi:**  
- **Menggabungkan** audio dari video DAN background music
- Volume masing-masing bisa di-adjust
- Perfect untuk gaming dengan background music

**Kapan pakai:**
- Gaming dengan narasi + BGM
- Tutorial dengan background music
- Vlog dengan soundtrack
- Stream dengan music background

**Contoh:**
```
Input:
  Video: gameplay.mp4 (suara narasi + game)
  Audio Directory: bgm.mp3

Output:
  Video: gameplay visual
  Audio: Narasi (100%) + BGM (50%) - mixed!
```

**Volume Controls:**
- **Video Audio:** 0-100% (default 100%)
- **Background Music:** 0-100% (default 100%)
- Adjust sesuai kebutuhan!

---

## 🎛️ Cara Menggunakan

### Di UI (Tab MEDIA):

```
Audio Source: [Dropdown]
├─ 🎵 Audio Directory (Replace)     ← Audio dari folder music
├─ 🎬 Video Original Audio           ← Audio dari video
└─ 🎚️ Mix Both (Video + Music)      ← Gabungan keduanya
```

**Jika pilih "Mix Both", muncul slider:**
```
Mix Volume Controls:
├─ Video Audio:        [────●────] 100%
└─ Background Music:   [────●────] 100%
```

---

## 🎯 Use Case Examples

### Use Case 1: Lofi Music Stream
```
Mode: Static Image
Audio Source: 🎵 Audio Directory (Replace)
  └─ Folder musik lofi

Result: Background image + lofi music playlist
```

### Use Case 2: Gaming Compilation (No Commentary)
```
Mode: Video Directory
Audio Source: 🎵 Audio Directory (Replace)
  └─ Epic gaming music

Result: Gaming clips + epic soundtrack (suara game hilang)
```

### Use Case 3: Gaming with Commentary
```
Mode: Video Directory  
Audio Source: 🎬 Video Original Audio

Result: Gaming clips + original audio (narasi tetap ada)
```

### Use Case 4: Gaming Stream with BGM
```
Mode: Video Directory
Audio Source: 🎚️ Mix Both (Video + Music)
  ├─ Video Audio: 100% (full narasi)
  └─ Background Music: 30% (BGM pelan di background)

Result: Gaming + narasi jelas + BGM halus
```

### Use Case 5: Tutorial with Background Music
```
Mode: Video Directory
Audio Source: 🎚️ Mix Both
  ├─ Video Audio: 100% (narasi tutorial)
  └─ Background Music: 20% (musik lembut)

Result: Tutorial dengan musik background yang tidak mengganggu
```

---

## ⚙️ Technical Details

### FFmpeg Command Examples:

**Audio Directory (Replace):**
```bash
ffmpeg -i video.mp4 -i music.mp3 \
  -map 0:v -map 1:a \  # Video dari input 0, audio dari input 1
  output.mp4
```

**Video Original Audio:**
```bash
ffmpeg -i video.mp4 \
  -map 0:v -map 0:a \  # Video dan audio dari input 0
  output.mp4
```

**Mix Both:**
```bash
ffmpeg -i video.mp4 -i music.mp3 \
  -filter_complex "\
    [0:a]volume=1.0[va]; \
    [1:a]volume=0.5[ma]; \
    [va][ma]amix=inputs=2:duration=first:normalize=0[aout]" \
  -map 0:v -map "[aout]" \
  output.mp4
```

---

## 🚨 Important Notes

### Static Image Mode:
- ❌ **"Video Original Audio" TIDAK tersedia**
- Kenapa? Static image tidak punya audio
- Gunakan "Audio Directory" atau "Mix Both" (tapi mix tidak make sense)

### Loop Mode Consideration:
- Untuk **Video Original Audio**, durasi dihitung dari video duration
- Untuk **Audio Directory**, durasi dari audio files
- Untuk **Mix Both**, durasi dari yang terpanjang (biasanya audio directory)

### Performance:
- **Audio Directory:** Fastest (no mixing)
- **Video Original Audio:** Fastest (no mixing)
- **Mix Both:** Slightly slower (realtime audio mixing)

---

## 📝 Migration Guide

### Dari Versi Lama:
Jika Anda sudah punya project dengan versi lama, defaultnya akan menggunakan:
```
Audio Source: 🎵 Audio Directory (Replace)
```
Ini sama persis dengan behavior lama, jadi tidak ada perubahan!

### Untuk Fitur Baru:
Cukup pilih mode yang sesuai di dropdown "Audio Source" 😊

---

## 🎨 UI Preview

```
┌─────────────────────────────────────────┐
│ AUDIO FILES                             │
├─────────────────────────────────────────┤
│                                         │
│ Audio Source:                           │
│ [🎵 Audio Directory (Replace)      ▼]   │
│                                         │
│ Selected Audio Files:                   │
│ ┌─────────────────────────────────────┐ │
│ │ lofi1.mp3                           │ │
│ │ lofi2.mp3                           │ │
│ │ lofi3.mp3                           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [+ Add Files] [+ Add Folder]           │
│ [- Remove] [Clear All]                  │
│                                         │
│ [🔀 Shuffle Order] [↑ Up] [↓ Down]     │
│                                         │
└─────────────────────────────────────────┘
```

**Saat pilih "Mix Both":**
```
┌─────────────────────────────────────────┐
│ Mix Volume Controls:                    │
│                                         │
│ Video Audio:                            │
│ [────────●──] 100%                      │
│                                         │
│ Background Music:                       │
│ [─●─────────] 30%                       │
│                                         │
└─────────────────────────────────────────┘
```

---

## ✅ Changelog

**Version 2.1 - Audio Source Modes**
- ✅ Added 3 audio source modes
- ✅ Audio Directory (Replace) - default/legacy behavior
- ✅ Video Original Audio - NEW! Use video's own audio
- ✅ Mix Both - NEW! Combine video audio + background music
- ✅ Volume controls for Mix Both mode
- ✅ Works for both Export and Livestream
- ✅ Smart UI: hides audio files list for Video Original Audio mode
- ✅ Validation: Static image mode can't use Video Original Audio

---

## 💡 Tips & Tricks

1. **Gaming Stream Perfect Mix:**
   - Video Audio: 80-100%
   - Background Music: 20-40%
   - Hasil: Narasi jelas, musik halus

2. **Podcast with Intro Music:**
   - Use Mix Both at start (music 70%, voice 100%)
   - Fade music manually in audio editor before import

3. **Music Video with Ambient Sound:**
   - Video Audio: 20% (ambient/environment)
   - Background Music: 100% (main music)

4. **Tutorial Clear Audio:**
   - Just use Video Original Audio
   - No background music = fokus ke penjelasan

---

**Happy Mixing! 🎵🎬**

