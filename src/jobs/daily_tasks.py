import schedule
import time
import logging
from src.utils.time_helper import get_current_wib_time
from src.services.email_service import fetch_recent_emails, format_summary_to_html, send_email_resend
from src.services.gemini_service import generate_morning_summary, generate_macro_summary
from src.services.news_crypto_service import get_combined_market_news
from src.config.settings import EMAIL_USER
from src.services.economic_calendar_api import EconomicCalendarAPI
from src.services.bible_service import run_daily_bible_job
from src.services.discord_service import send_discord_dm_sync

logger = logging.getLogger(__name__)

def job_morning_email():
    logger.info("Memulai job_morning_email (Rangkuman Inbox Gmail Petraku via Resend API)...")
    try:
        now_wib = get_current_wib_time()
        date_str = now_wib.strftime("%d %B %Y")
        
        # 1. Ambil data email masuk dari Gmail (Petraku)
        emails_data = fetch_recent_emails()
        
        # 2. Buat ringkasan dengan Gemini AI
        summary = generate_morning_summary(date_str, emails_data)
        logger.info("Ringkasan inbox Gmail Petraku berhasil dibuat oleh Gemini.")
        
        # 3. Format ke HTML estetis
        html_content = format_summary_to_html(summary, title=f"📧 Rangkuman Gmail Petraku - {date_str}")
        
        # 4. Kirim via Resend API
        recipient = EMAIL_USER if EMAIL_USER and EMAIL_USER not in ["your_email@gmail.com", "kevin@example.com"] else "d11250214@john.petra.ac.id"
        success = send_email_resend(
            to_email=recipient,
            subject=f"✨ Beatrice Email Briefing (Petraku Inbox) - {date_str}",
            html_content=html_content,
            text_content=summary
        )
        if success:
            logger.info("job_morning_email (Rangkuman Gmail Petraku) selesai dengan sukses.")
        else:
            logger.error("job_morning_email gagal saat pengiriman email via Resend API.")
    except Exception as e:
        logger.error(f"Error pada job_morning_email: {e}")


def job_bible_verse():
    logger.info("Menjalankan tugas harian: Renungan Pagi Alkitab (via Discord DM)...")
    run_daily_bible_job()

def run_macro_briefing(session_name: str):
    logger.info(f"Memulai briefing makro ekonomi & kripto ({session_name}) via Finnhub & Kalender (untuk Discord DM)...")
    try:
        now_wib = get_current_wib_time()
        date_str = now_wib.strftime("%d %B %Y (%H:%M WIB)")
        
        # 1. Ambil berita Finnhub & Kalender Ekonomi
        news_data = get_combined_market_news()
        econ_api = EconomicCalendarAPI()
        econ_events = econ_api.get_formatted_calendar_str()
        
        # 2. Buat analisa sentimen Bull/Bear/Sideways dengan Gemini
        summary = generate_macro_summary(date_str, news_data, econ_events)
        logger.info(f"Analisa sentimen pasar ({session_name}) berhasil dibuat.")
        
        # 3. Kirim langsung via Discord DM ke Kevin
        formatted_dm = f"📊 **ANALISA PASAR & MAKROEKONOMI ({session_name.upper()})**\n📅 *{date_str}*\n\n{summary}"
        success = send_discord_dm_sync(formatted_dm)
        if success:
            logger.info(f"💬 Briefing makro {session_name} terkirim via Discord DM.")
        else:
            logger.warning(f"⚠️ Gagal mengirim briefing makro {session_name} via Discord DM.")
    except Exception as e:
        logger.error(f"Error pada run_macro_briefing ({session_name}): {e}")

def job_morning_macro():
    run_macro_briefing("Pagi")

def job_evening_macro():
    run_macro_briefing("Malam")

def start_scheduler(run_immediately: bool = True):
    schedule.every().day.at("05:00").do(job_morning_email)
    schedule.every().day.at("05:30").do(job_bible_verse)
    schedule.every().day.at("06:00").do(job_morning_macro)
    schedule.every().day.at("20:00").do(job_evening_macro)
    
    if run_immediately:
        logger.info("🧪 [TESTING MODE] Menjalankan uji coba briefing makro (Malam) sekarang sebelum menunggu jadwal...")
        try:
            job_evening_macro()
            logger.info("✅ Uji coba selesai. Sekarang masuk ke mode penjadwalan harian (Scheduler Loop)...")
        except Exception as e:
            logger.error(f"Terjadi kesalahan saat uji coba awal: {e}")

    logging.info("Scheduler started. Waiting for jobs...")
    while True:
        schedule.run_pending()
        time.sleep(60)
