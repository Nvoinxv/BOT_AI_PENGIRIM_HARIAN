import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Memuat variabel lingkungan dengan memprioritaskan environment OS (seperti parameter -e / --env-file dari docker run di VPS)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=False)
else:
    load_dotenv(override=False)

def clean_env(val: str):
    if not val:
        return None
    # Bersihkan carriage returns (\r dari CRLF Windows di Linux Docker), newline (\n), tab, BOM (\ufeff), zero-width space (\u200b), dan tanda kutip
    cleaned = str(val).replace('\r', '').replace('\n', '').replace('\t', '').replace('\ufeff', '').replace('\u200b', '').strip().strip('\'"').strip()
    return cleaned if cleaned else None

DISCORD_TOKEN = clean_env(os.getenv('DISCORD_TOKEN'))
DISCORD_USER_ID = clean_env(os.getenv('DISCORD_USER_ID'))
GEMINI_API_KEY_AKUN_EDWARD_FARREL = clean_env(os.getenv('GEMINI_API_KEY_AKUN_EDWARD_FARREL'))
GEMINI_API_KEY_KEVIN_PETRA = clean_env(os.getenv('GEMINI_API_KEY_KEVIN_PETRA'))
GEMINI_API_KEY = GEMINI_API_KEY_KEVIN_PETRA or clean_env(os.getenv('GEMINI_API_KEY')) or GEMINI_API_KEY_AKUN_EDWARD_FARREL
EMAIL_USER = clean_env(os.getenv('EMAIL_USER'))
EMAIL_PASS = clean_env(os.getenv('EMAIL_PASS'))
IMAP_SERVER = clean_env(os.getenv('IMAP_SERVER')) or 'imap.gmail.com'
SMTP_SERVER = clean_env(os.getenv('SMTP_SERVER')) or 'smtp.gmail.com'
RESEND_API_KEY = clean_env(os.getenv('RESEND_API_KEY')) or clean_env(os.getenv('RESEND_EMAIL_KEVIN_HARLY'))
RESEND_SENDER_EMAIL = clean_env(os.getenv('RESEND_SENDER_EMAIL')) or 'onboarding@resend.dev'
FINNHUB_API_KEY = clean_env(os.getenv('FINNHUB_API_KEY')) or clean_env(os.getenv('FINHUB_API_KEY'))
MONGO_URL = clean_env(os.getenv('MONGO_URL')) or 'mongodb://mongodb:27017'
MONGO_DB_NAME = clean_env(os.getenv('MONGO_DB_NAME')) or 'beatrice_daily_db'




def setup_logging():
    from src.utils.logger import setup_logging as prof_setup_logging
    prof_setup_logging()

