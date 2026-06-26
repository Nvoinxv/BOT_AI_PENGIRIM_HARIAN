import schedule
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
