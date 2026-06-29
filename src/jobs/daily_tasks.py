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

logger = logging.getLogger(__name__)

def job_morning_email():
    logger.info("Memulai job_morning_email (Briefing Harian via Resend API)...")
    try:
        now_wib = get_current_wib_time()
        date_str = now_wib.strftime("%d %B %Y")
        
        # 1. Ambil data email
        emails_data = fetch_recent_emails()
        
        # 2. Buat ringkasan dengan Gemini AI
        summary = generate_morning_summary(date_str, emails_data)
        logger.info("Ringkasan pagi berhasil dibuat oleh Gemini.")
        
        # 3. Format ke HTML estetis
        html_content = format_summary_to_html(summary, title=f"Briefing Pagi - {date_str}")
        
        # 4. Kirim via Resend API
        recipient = EMAIL_USER if EMAIL_USER and EMAIL_USER != "your_email@gmail.com" else "kevin@example.com"
        success = send_email_resend(
            to_email=recipient,
            subject=f"✨ Beatrice Daily Briefing - {date_str}",
            html_content=html_content,
            text_content=summary
        )
        if success:
            logger.info("job_morning_email selesai dengan sukses.")
        else:
            logger.error("job_morning_email gagal saat pengiriman email via Resend API.")
    except Exception as e:
        logger.error(f"Error pada job_morning_email: {e}")


def job_bible_verse():
    logger.info("Menjalankan tugas harian: Renungan Pagi Alkitab...")
    run_daily_bible_job()

def run_macro_briefing(session_name: str):
    logger.info(f"Memulai briefing makro ekonomi & kripto ({session_name}) via Finnhub & Kalender...")
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
        
        # 3. Format ke HTML & Kirim via Resend API
        html_content = format_summary_to_html(summary, title=f"Analisa Pasar {session_name} - {date_str}")
        recipient = EMAIL_USER if EMAIL_USER and EMAIL_USER != "your_email@gmail.com" else "kevin@example.com"
        
        success = send_email_resend(
            to_email=recipient,
            subject=f"📊 Beatrice Market Sentiment ({session_name}) - {date_str}",
            html_content=html_content,
            text_content=summary
        )
        if success:
            logger.info(f"Briefing makro {session_name} terkirim via Resend API.")
        else:
            logger.error(f"Gagal mengirim briefing makro {session_name} via Resend API.")
    except Exception as e:
        logger.error(f"Error pada run_macro_briefing ({session_name}): {e}")

def job_morning_macro():
    run_macro_briefing("Pagi")

def job_evening_macro():
    run_macro_briefing("Malam")

def start_scheduler():
    schedule.every().day.at("05:00").do(job_morning_email)
    schedule.every().day.at("05:30").do(job_bible_verse)
    schedule.every().day.at("06:00").do(job_morning_macro)
    schedule.every().day.at("20:00").do(job_evening_macro)
    
    logging.info("Scheduler started. Waiting for jobs...")
    while True:
        schedule.run_pending()
        time.sleep(60)
