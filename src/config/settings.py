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

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
