import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Timezone WIB untuk log timestamp
WIB = ZoneInfo("Asia/Jakarta")

class WIBFormatter(logging.Formatter):
    """
    Formatter khusus untuk mengonversi waktu log menjadi zona waktu WIB (Asia/Jakarta).
    """
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=WIB)
        return dt.timetuple()

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=WIB)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S WIB")

class ColoredConsoleFormatter(WIBFormatter):
    """
    Formatter dengan warna ANSI untuk output Console (Terminal) agar profesional dan mudah dibaca.
    """
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[1;31m" # Bold Red
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        level_name = f"{color}{self.BOLD}{record.levelname:<8}{self.RESET}"
        time_str = f"\033[90m{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}\033[0m"
        logger_name = f"\033[35m{record.name}\033[0m"
        message = f"{color}{record.getMessage()}{self.RESET}"
        
        # Format: [Time] [Level] [Logger:Line] ➔ Message
        return f"[{time_str}] [{level_name}] [{logger_name}:{record.lineno}] ➔ {message}"

def setup_logging(log_level=logging.INFO, log_dir="logs", max_bytes=10*1024*1024, backup_count=5):
    """
    Inisialisasi konfigurasi logging enterprise-grade:
    1. Console Handler dengan warna kustom (Colored ANSI) & timestamp WIB.
    2. Rotating File Handler (penyimpanan otomatis di folder logs/ dengan rotasi file maksimal 10MB).
    3. Filter pembatas noise untuk pustaka pihak ketiga (requests, urllib3, discord).
    """
    # Buat direktori logs jika belum ada
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    log_file_path = os.path.join(log_dir, "sender_bot.log")

    # Dapatkan root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Hapus handler lama jika ada agar tidak duplikat log
    if root_logger.handlers:
        root_logger.handlers.clear()

    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ColoredConsoleFormatter())
    root_logger.addHandler(console_handler)

    # 2. File Handler (Rotating File Handler)
    file_formatter = WIBFormatter(
        fmt="[{asctime}] [{levelname:<8}] [{name}:{lineno}] [{processName}] - {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style='{'
    )
    file_handler = RotatingFileHandler(
        log_file_path, 
        maxBytes=max_bytes, 
        backupCount=backup_count, 
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # 3. Meredam kebisingan dari third-party libraries
    noisy_libraries = [
        "urllib3", 
        "requests", 
        "discord.client", 
        "discord.gateway", 
        "google.auth", 
        "schedule"
    ]
    for lib in noisy_libraries:
        logging.getLogger(lib).setLevel(logging.WARNING)

    logging.info("Sistem Logging Profesional (Beatrice Core) berhasil diinisialisasi.")
    logging.info(f"File Log disimpan di: {os.path.abspath(log_file_path)} (Max: {max_bytes//(1024*1024)}MB/file)")

def get_logger(name: str) -> logging.Logger:
    """
    Helper untuk mendapatkan logger instance berspesifikasi modul.
    """
    return logging.getLogger(name)
