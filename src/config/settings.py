import os
from dotenv import load_dotenv
import logging

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_USER_ID = os.getenv('DISCORD_USER_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
RESEND_API_KEY = os.getenv('RESEND_API_KEY') or os.getenv('RESEND_EMAIL_KEVIN_HARLY')
RESEND_SENDER_EMAIL = os.getenv('RESEND_SENDER_EMAIL', 'onboarding@resend.dev')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY') or os.getenv('FINHUB_API_KEY')




def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
