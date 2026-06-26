import os

base = r"C:\Users\Nvoinvx\Downloads\Sender_Bot_Daily"

files = {
    "main.py": """import logging
from src.config.settings import setup_logging
from src.jobs.daily_tasks import start_scheduler

def main():
    setup_logging()
    logging.info("Starting Personal Assistant Bot...")
    start_scheduler()

if __name__ == "__main__":
    main()
""",
    ".env.example": """DISCORD_TOKEN=your_discord_token
DISCORD_USER_ID=your_discord_id
GEMINI_API_KEY=your_gemini_api_key
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
IMAP_SERVER=imap.gmail.com
SMTP_SERVER=smtp.gmail.com
TZ=Asia/Jakarta
""",
    "requirements.txt": """discord.py
google-generativeai
requests
schedule
python-dotenv
tzdata
""",
    ".gitignore": """.env
__pycache__/
*.pyc
logs/
""",
    "README.md": """# Sender Bot Daily

Personal Assistant Bot for Daily Briefings.

## Setup
1. Copy `.env.example` to `.env` and fill the variables.
2. Run `pip install -r requirements.txt`.
3. Run `python main.py`.

## Docker
Run `docker-compose up --build -d`
""",
    "Dockerfile": """FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]
""",
    "docker-compose.yml": """version: '3.8'
services:
  bot:
    build: .
    container_name: sender_bot
    env_file:
      - .env
    restart: unless-stopped
""",
    "src/config/settings.py": """import os
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
""",
    "src/services/email_service.py": """# IMAP and SMTP logic goes here
""",
    "src/services/gemini_service.py": """# Gemini AI logic goes here
""",
    "src/services/discord_service.py": """# Discord DM logic goes here
""",
    "src/services/news_crypto_service.py": """# Crypto and Macro News logic goes here
""",
    "src/services/bible_service.py": """# Bible Verse API logic goes here
""",
    "src/jobs/daily_tasks.py": """import schedule
import time
import logging

def job_morning_email():
    logging.info("Running job_morning_email")

def job_bible_verse():
    logging.info("Running job_bible_verse")

def job_morning_macro():
    logging.info("Running job_morning_macro")

def job_evening_macro():
    logging.info("Running job_evening_macro")

def start_scheduler():
    schedule.every().day.at("05:00").do(job_morning_email)
    schedule.every().day.at("05:30").do(job_bible_verse)
    schedule.every().day.at("06:00").do(job_morning_macro)
    schedule.every().day.at("20:00").do(job_evening_macro)
    
    logging.info("Scheduler started. Waiting for jobs...")
    while True:
        schedule.run_pending()
        time.sleep(60)
""",
    "src/utils/logger.py": """# Custom logger setup if needed
""",
    "src/utils/time_helper.py": """from datetime import datetime
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")

def get_current_wib_time():
    return datetime.now(WIB)
"""
}

for filepath, content in files.items():
    with open(os.path.join(base, filepath), "w", encoding="utf-8") as f:
        f.write(content)
