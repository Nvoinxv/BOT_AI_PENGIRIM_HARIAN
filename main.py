import logging
from src.config.settings import setup_logging
from src.jobs.daily_tasks import start_scheduler

def main():
    setup_logging()
    logging.info("Starting Personal Assistant Bot...")
    start_scheduler()

if __name__ == "__main__":
    main()
