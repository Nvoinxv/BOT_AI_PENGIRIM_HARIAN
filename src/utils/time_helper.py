from datetime import datetime
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")

def get_current_wib_time():
    return datetime.now(WIB)
