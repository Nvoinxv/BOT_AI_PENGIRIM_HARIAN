# 🌸 BEATRICE - PERSONAL AI ASSISTANT & DAILY AUTOMATION BOT

![Version](https://img.shields.io/badge/version-2.0.0-pink.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Modular%20Service%20Oriented-success.svg)
![Docker](https://img.shields.io/badge/Docker-Production%20Ready-2496ED.svg)

**Beatrice** adalah sistem asisten pribadi berbasis kecerdasan buatan (AI) yang dirancang untuk mengotomasi rutinitas harian, mulai dari analisis makroekonomi pasar keuangan, pengiriman ringkasan email harian, renungan pagi rohani, hingga asisten interaktif via Discord Direct Message.

---

## ✨ Fitur Utama (*Core Capabilities*)

*   📧 **College Email Reader & Briefing (Resend API):** Membaca pesan email masuk dari Gmail via IMAP (khususnya email kuliah UK Petra/Petraku, BAKP, Dosen, BEM, dan deadline penting), lalu mengirimkan buletin ringkasan HTML elegan ke inbox email Anda via Resend API serta duplikat ke Discord DM.
*   📈 **Finnhub & Macro Intelligence (Eksklusif Discord DM):** Memantau berita pasar finansial terkini (Kripto, Forex, Saham) dan **Kalender Ekonomi AS** secara real-time, dikirimkan **eksklusif hanya ke Discord DM** agar tidak bercampur di inbox email Anda.
*   🤖 **AI Sentiment & Academic Analysis (Google Gemini AI):** Menganalisis jadwal kuliah/deadline secara cerdas serta menyimpulkan sentimen pasar ke dalam indikator jelas: `BULLISH` 🟢, `BEARISH` 🔴, atau `SIDEWAYS` 🟡.
*   📖 **Daily Bible Devotional (Eksklusif Discord DM):** Mengambil ayat Alkitab resmi dan merangkai renungan pagi penyemangat yang dikirimkan **eksklusif ke Discord DM**.
*   💬 **Interactive Discord DM Chatbot:** Asisten personal yang siap merespons pertanyaan dan mengobrol secara privat 24/7 via Direct Message Discord.
*   🛡️ **Professional Rotating Logger:** Sistem pencatatan log terstruktur dengan zona waktu WIB asli (*WIB Timestamp*) dan pembatasan ukuran file otomatis (*Log Rotation*).

---

## 🏗️ Gambaran Besar Arsitektur (*High-Level Architecture*)

Beatrice dibangun dengan arsitektur **Modular Service-Oriented**, di mana setiap layanan eksternal terisolasi dengan rapi di dalam layernya masing-masing:

```text
                        ┌──────────────────────────────┐
                        │       main.py (Core)         │
                        │  Banner, Env Check & Loggers │
                        └──────────────┬───────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
    ┌───────────────────────┐                     ┌───────────────────────┐
    │  Daily Tasks Scheduler │                     │  Discord Background   │
    │   (schedule & jobs)   │                     │    Thread (AsyncIO)   │
    └───────────┬───────────┘                     └───────────┬───────────┘
                │                                             │
        ┌───────┴────────────────────────┐                    │
        ▼                                ▼                    ▼
┌───────────────────────┐    ┌───────────────────────┐    ┌───────────────────────┐
│ Market & Macro Engine │    │  Spiritual Devotional │    │  Direct Message AI    │
│  • Finnhub Market API │    │  • Free Use Bible API │    │  • Discord Gateway    │
│  • US Economic Cal    │    │  • Gemini Reflection  │    │  • Gemini Chat Res    │
│  • Gemini Sentiment   │    │  • Resend Email API   │    └───────────────────────┘
│  • Resend Email API   │    └───────────────────────┘
└───────────────────────┘
```

### 📂 Struktur Direktori Project
```text
Sender_Bot_Daily/
├── main.py                    # Core entry point (Startup banner & verification)
├── Dockerfile                 # Production Docker multi-stage & non-root architecture
├── docker-compose.yml         # Container orchestration configuration
├── requirements.txt           # Daftar dependensi Python
├── .env.example               # Template konfigurasi variabel lingkungan
└── src/
    ├── config/settings.py     # Loader variabel lingkungan (.env)
    ├── jobs/daily_tasks.py    # Scheduler rutinitas harian (05:00, 05:30, 06:00, 20:00 WIB)
    ├── services/              # Modul integrasi pihak ketiga (Resend, Finnhub, Gemini, Discord, Bible)
    └── utils/                 # Helper fungsionalitas (Logger profesional & konversi waktu WIB)
```

---

## ⚙️ Persiapan & Konfigurasi (*Prerequisites*)

1. Pastikan Anda telah menginstal **Python 3.11+** atau **Docker**.
2. Salin file contoh konfigurasi lingkungan:
   ```bash
   cp .env.example .env
   ```
3. Buka file `.env` dan lengkapi API Key yang dibutuhkan:
   *   `RESEND_API_KEY`: Kunci API untuk pengiriman email harian.
   *   `FINHUB_API_KEY`: Kunci API untuk intelijen berita keuangan.
   *   `GEMINI_API_KEY`: Kunci API Google Gemini untuk analisis AI.
   *   `DISCORD_TOKEN`: Token bot Discord Anda.

---

## 🚀 Cara Menjalankan (*Deployment Guide*)

### Opsi 1: Menjalankan Secara Lokal (Python)
Cocok untuk pengembangan (*development*) atau eksekusi langsung di komputer pribadi:

```bash
# 1. Buat dan aktifkan virtual environment (opsional)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Instal seluruh dependensi
pip install -r requirements.txt

# 3. Jalankan bot Beatrice
python main.py
```

---

### Opsi 2: Menjalankan Menggunakan Docker Compose (Direkomendasikan)
Cara termudah, terisolasi, dan teraman untuk menjalankan bot secara *background daemon*:

```bash
# 1. Bangun image dan jalankan kontainer di latar belakang
docker compose up -d --build

# 2. Pantau log operasional bot secara real-time
docker logs -f beatrice_assistant_bot
```

Untuk menghentikan kontainer yang sedang berjalan:
```bash
docker compose down
```

---

## 📅 Jadwal Rutinitas Otomatis (Waktu WIB)

| Waktu Eksekusi | Tugas Harian | Jalur Pengiriman | Deskripsi Layanan |
| :--- | :--- | :--- | :--- |
| **05:00 WIB** | Briefing Email Kuliah & Penting | **Resend API & Discord DM** | Rangkuman pesan email kuliah (Petraku/BAKP/Dosen) & agenda |
| **05:30 WIB** | Renungan Alkitab | **Eksklusif Discord DM** | Pengiriman ayat harian & doa refleksi pagi |
| **06:00 WIB** | Analisa Pasar Pagi | **Eksklusif Discord DM** | Rangkuman makroekonomi, kripto, forex & kalender AS |
| **20:00 WIB** | Analisa Pasar Malam | **Eksklusif Discord DM** | Evaluasi penutupan pasar & kalender ekonomi malam |

---
*Developed with ❤️ for seamless personal automation.*
