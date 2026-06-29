"""
=============================================================================
BEATRICE - PERSONAL AI ASSISTANT & DAILY AUTOMATION BOT
=============================================================================
Core Entry Point (Main Module)
Pemilik : Kevin
Versi   : 2.0 (Resend API + Finnhub + Economic Calendar + Gemini AI)
=============================================================================
"""

import sys
import time
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import logging
from src.config.settings import (
    setup_logging,
    RESEND_API_KEY,
    FINNHUB_API_KEY,
    DISCORD_TOKEN,
    GEMINI_API_KEY,
    EMAIL_USER
)
from src.jobs.daily_tasks import start_scheduler
from src.services.discord_service import start_discord_bot_in_background

logger = logging.getLogger("BeatriceCore")


def display_banner():
    """Menampilkan banner sambutan profesional di terminal saat bot berjalan."""
    banner = """
    ╔═════════════════════════════════════════════════════════════════════╗
    ║                 🌸 BEATRICE PERSONAL ASSISTANT 🌸                   ║
    ║        Daily Email Briefing | Finnhub & Macro | Discord DM          ║
    ╚═════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def verify_environment():
    """
    Memeriksa ketersediaan konfigurasi & API Key penting agar Kevin mengetahui
    fitur mana saja yang sudah siap berjalan.
    """
    logger.info("🔍 Memeriksa konfigurasi sistem & API Key...")
    
    status_checks = [
        ("Resend Email API", RESEND_API_KEY, "Kirim email harian & briefing"),
        ("Finnhub Market API", FINNHUB_API_KEY, "Berita Kripto, Forex & Ekonomi"),
        ("Google Gemini AI", GEMINI_API_KEY, "Analisa sentimen Bull/Bear/Sideways"),
        ("Discord Bot Token", DISCORD_TOKEN, "Chatbot interaktif via Direct Message")
    ]
    
    ready_count = 0
    for name, key, desc in status_checks:
        is_ready = bool(key and key != "your_api_key_here" and "placeholder" not in str(key).lower())
        if is_ready:
            logger.info(f"  [✓] {name:<20} : SIAP ({desc})")
            ready_count += 1
        else:
            logger.warning(f"  [!] {name:<20} : BELUM ATUR / FALLBACK MODE ({desc})")
            
    logger.info(f"⚙️ Status Sistem: {ready_count}/{len(status_checks)} Layanan Utama Aktif. Email Penerima: {EMAIL_USER}")


def log_scheduled_jobs():
    """Menampilkan jadwal tugas harian otomatis yang terdaftar."""
    logger.info("📅 Daftar Jadwal Tugas Harian (Waktu WIB):")
    logger.info("  ⏰ 05:00 WIB ➔ Briefing Email Pagi (Rangkuman Email & Agenda)")
    logger.info("  ⏰ 05:30 WIB ➔ Ayat Alkitab Harian & Renungan Pagi")
    logger.info("  ⏰ 06:00 WIB ➔ Analisa Pasar Pagi (Finnhub + Kalender Ekonomi)")
    logger.info("  ⏰ 20:00 WIB ➔ Analisa Pasar Malam (Finnhub + Kalender Ekonomi)")


def main():
    """Fungsi utama penggerak seluruh ekosistem Beatrice."""
    # 1. Inisialisasi Sistem Logging Enterprise
    setup_logging()
    
    # 2. Tampilkan Banner & Cek Status
    display_banner()
    verify_environment()
    
    logger.info("🚀 Memulai proses background Beatrice Assistant Bot...")
    
    try:
        # 3. Jalankan Bot Discord di Background Thread
        logger.info("💬 Mengaktifkan layanan Discord Bot (DM Chatbot)...")
        start_discord_bot_in_background()
        
        # 4. Tampilkan Jadwal & Jalankan Scheduler Otomatis
        log_scheduled_jobs()
        logger.info("⏳ Beatrice stand-by mengawasi jadwal. Tekan [Ctrl + C] untuk berhenti.")
        
        # Blocking Scheduler Loop
        start_scheduler()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Menerima sinyal berhenti (Ctrl + C). Mematikan Beatrice...")
        logger.info("👋 Sampai jumpa lagi, Kevin! Semoga harimu menyenangkan. ❤️")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"💥 Terjadi kesalahan tak terduga pada sistem utama: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
