<div align="center">

# 🎓 Research Prospect Finder

**Platform Modern untuk Menemukan, Menganalisis, dan Menghubungi Bisnis Lokal Sebagai Objek Penelitian & Skripsi Berbasis AI**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![OmniRoute / Gemini](https://img.shields.io/badge/AI-OmniRoute%20%7C%20Gemini-7B61FF.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📖 Tentang Aplikasi

**Research Prospect Finder** adalah aplikasi Web UI yang dirancang khusus untuk membantu mahasiswa, akademisi, dan peneliti menemukan tempat studi kasus penelitian/skripsi yang potensial dari bisnis lokal di Indonesia.

Aplikasi ini mengintegrasikan data geospasial terbuka (OpenStreetMap), algoritma penilaian kelayakan riset, audit otomatis kehadiran digital (Website & Media Sosial), serta generator pesan komunikasi (*outreach*) bertenaga AI yang 100% berbahasa Indonesia.

---

## ✨ Fitur Utama

### 1. 🔍 Discovery Bisnis Geospasial (OpenStreetMap)
- Cari ribuan bisnis lokal berdasarkan nama kota, kecamatan, atau alamat spesifik.
- Atur radius pencarian (1 – 25 km) dan filter kategori bisnis (*Food & Dining, Retail, Technology, Health, Automotive, Services*).
- Sistem **Deduplikasi Cerdas** untuk mencegah penyimpanan data ganda.

### 2. 🎯 Scoring & Ranking Kelayakan Objek Riset
Algoritma komprehensif untuk menilai kesiapan bisnis menjadi subjek tugas akhir/skripsi:
- **Ukuran Bisnis (25%)**: Usaha lokal independen mendapat bobot prioritas lebih tinggi dibanding franchise.
- **Kompleksitas Operasional (30%)**: Menilai tingkat kompleksitas alur kerja (inventori, pesanan, layanan).
- **Kesenjangan Digitalisasi (25%)**: Keberadaan website, formulir order, atau e-commerce.
- **Ketersediaan Kontak (20%)**: Kemudahan menghubungi pemilik (WhatsApp/telepon dan email).

### 3. 🤖 AI Skripsi Insights (100% Bahasa Indonesia)
Didukung oleh LLM (Google Gemini / OmniRoute / OpenAI-compatible):
- ⚠️ **Identifikasi Masalah Operasional**: Analisis potensi bottleneck proses bisnis.
- 💡 **Peluang Solusi Sistem Informasi**: Rekomendasi solusi digital (POS, ERP mini, CRM, booking web).
- 🎓 **Relevansi Riset**: Alasan akademis mengapa bisnis layak diteliti.
- 📌 **5 Rekomendasi Judul Skripsi**: Format judul formal sesuai standar perguruan tinggi di Indonesia.
- ❓ **Daftar Pertanyaan Wawancara**: Panduan validasi lapangan untuk pemilik usaha.

### 4. 🌐 Audit Website & Deteksi Media Sosial
- Ekstraksi otomatis nomor WhatsApp, telepon, dan email dari situs resmi bisnis.
- Deteksi tautan profil **Instagram, Facebook, LinkedIn, TikTok, dan WhatsApp**.

### 5. 🚀 AI Dynamic Bulk Personalized Outreach Generator
- Menyusun draf pesan permohonan riset skripsi massal yang dibuat khusus secara dinamis per bisnis.
- **Pilihan Channel**:
  - 💬 **WhatsApp / DM Medsos**: Format santun, ringkas, dan nyaman dibaca di smartphone.
  - ✉️ **Email Resmi**: Format surat resmi proposal izin penelitian skripsi.
- **Batasan Kustom (Custom Batch Limit)**: Atur jumlah pesan yang ingin di-generate (1 s.d. 25+ bisnis per batch).

### 6. ⚡ Aksi Cepat 1-Klik
- 💬 **Chat WhatsApp (`wa.me`)**: Langsung membuka chat WhatsApp pemilik bisnis dengan pesan pembuka otomatis.
- 📍 **Buka Google Maps**: Membuka profil bisnis asli di Google Maps untuk melihat foto, jam buka, dan ulasan pengunjung.

### 7. 🗂️ Filter Canggih, Paginasi & Pengurutan Interaktif
- **Paginasi Cepat**: Navigasi lancar untuk ribuan data dengan pilihan 50, 100, 250, 500, hingga 1.000 data per halaman.
- **Filter Tag Interaktif**: Filter khusus bisnis yang memiliki WhatsApp, Website, Email, Media Sosial, atau yang sudah dianalisis AI.
- **Sorting Header**: Klik judul kolom untuk mengurutkan berdasarkan ID, Nama (A-Z), Kategori, Rating, atau Skor Riset.

### 8. 🌓 Desain Modern (Dark & Light Mode)
- Antarmuka responsif dengan skema warna ramah mata dan tombol pengubah tema gelap/terang.

### 9. 📊 Ekspor Multi-Format
- Unduh data prospek riset ke format **CSV (Excel / Google Sheets)**, **Markdown (.md)**, atau **JSON**.

---

## 🛠️ Instalasi & Persiapan

### 1. Prasyarat
- Python 3.10 atau versi yang lebih baru.
- Virtual Environment (direkomendasikan).

### 2. Kloning & Masuk ke Direktori Proyek
```bash
git clone <repository_url>
cd research-finder
```

### 3. Buat dan Aktifkan Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate   # Windows
```

### 4. Instal Dependensi
```bash
pip install -e .
```

---

## ⚙️ Konfigurasi Environment (`.env`)

Salin template konfigurasi `.env.example` ke file `.env`:

```bash
cp .env.example .env
```

Buka file `.env` dan sesuaikan parameter berikut:

```env
# Database SQLite
RF_DATABASE_URL=sqlite+aiosqlite:///data/research_finder.db

# Konfigurasi AI (OmniRoute / Gemini / OpenAI)
RF_AI_ENABLED=true
RF_AI_API_KEY=your_api_key_here
RF_AI_BASE_URL=http://localhost:20128/v1   # atau https://generativelanguage.googleapis.com/v1beta/openai
RF_AI_MODEL=auto/gemini                  # atau antigravity/gemini-2.5-flash, gpt-4o-mini
```

> [!TIP]
> Jika Anda menggunakan **OmniRoute Lokal**, pastikan Base URL mengarah ke endpoint `/v1` (misal: `http://localhost:20128/v1`).

---

## 🚀 Cara Menjalankan

Cukup jalankan satu perintah berikut di terminal:

```bash
research-finder
```

Aplikasi Web server FastAPI akan menyala dan otomatis membuka browser ke:

```
http://127.0.0.1:8000
```

### Opsi Tambahan CLI:
- Ganti port: `research-finder --port 8080`
- Akses jaringan lokal: `research-finder --host 0.0.0.0`
- Mode tanpa membuka browser: `research-finder --no-browser`
- Mode auto-reload (development): `research-finder --reload`

---

## 📁 Struktur Direktori

```
research-finder/
├── data/                       # Database SQLite lokal (dibuat otomatis)
├── src/
│   └── research_finder/
│       ├── application/        # Use cases, ranking service, dan AI orchestration
│       ├── cli/                # Entrypoint CLI dan runner aplikasi
│       ├── config/             # Pengaturan Pydantic Settings (.env)
│       ├── database/           # Model SQLAlchemy & repositori database
│       ├── domain/             # Domain entities & data models
│       ├── providers/          # Integrasi OpenStreetMap, AI, dan Website Analyzer
│       └── web/                # FastAPI backend & Static Frontend (HTML, CSS, JS)
│           ├── static/
│           │   ├── css/style.css
│           │   ├── js/app.js
│           │   └── index.html
│           ├── app.py
│           └── server.py
├── .env.example                # Template konfigurasi environment
├── .gitignore                  # Aturan ignore file git
├── pyproject.toml              # Konfigurasi package & dependencies
└── README.md                   # Dokumentasi proyek
```

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah lisensi [MIT License](LICENSE).
