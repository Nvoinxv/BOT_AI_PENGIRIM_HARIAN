import logging
from src.config.settings import setup_logging
from src.jobs.daily_tasks import start_scheduler
from src.services.discord_service import start_discord_bot_in_background

def main():
    setup_logging()
    logging.info("Starting Personal Assistant Bot (Beatrice)...")
    
    # Jalankan bot discord di background thread agar jalan bersamaan
    start_discord_bot_in_background()
    
    # Jalankan scheduler (blocking operation)
    start_scheduler()

if __name__ == "__main__":
    main()
