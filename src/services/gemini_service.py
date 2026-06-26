import google.generativeai as genai
from src.config.settings import GEMINI_API_KEY
import logging

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY tidak ditemukan di .env!")

def generate_morning_summary(date_wib_str: str, emails_content: str) -> str:
    """
    Menghasilkan ringkasan email harian (Pagi) dengan personalitas Beatrice.
    """
    system_instruction = (
        "You are Beatrice, Kevin's personal AI assistant. "
        "Your task is to analyze Kevin's Gmail data (schedule and important emails) "
        "and generate a summary push notification in Indonesian."
    )

    prompt = f"""
Step 1: The current date in WIB is: {date_wib_str}

Step 2: Here is the recent Gmail data from the last 24 hours:
{emails_content}
Please look for calendar invites, meeting notifications, deadlines, and important alerts.
Identify the top 3-5 most important emails.

Step 3: Compose a summary in Indonesian (under 3800 chars) using EXACTLY this template:

📅 JADWAL & EMAIL HARI INI
{date_wib_str}
━━━━━━━━━━━━━━━━━━━━━
📧 EMAIL PENTING
* [Pengirim]: [ringkasan 1 kalimat]
(atau: "Inbox aman ✅" jika tidak ada)
━━━━━━━━━━━━━━━━━━━━━
📆 JADWAL HARI INI
* [Waktu]: [event]
(atau: "Hari ini bebas 🎉" jika tidak ada)
━━━━━━━━━━━━━━━━━━━━━
⚡ PERLU DIPERHATIKAN
[deadline atau follow-up]
━━━━━━━━━━━━━━━━━━━━━
Have a great day! ❤️
"""

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error dari Gemini API (Morning Summary): {e}")
        return "Maaf Kevin, Beatrice mengalami masalah saat membaca email hari ini. 😔"

def generate_macro_summary(date_wib_str: str, macro_events: str, crypto_prices: str) -> str:
    """
    Menghasilkan ringkasan berita makro ekonomi dan kripto.
    """
    system_instruction = (
        "You are Beatrice, Kevin's personal AI assistant. "
        "Your task is to summarize macro-economic news, events, and crypto updates in a concise, friendly tone in Indonesian."
    )
    
    prompt = f"""
Tanggal: {date_wib_str}

Berikut adalah data kalender ekonomi makro (AS) hari ini:
{macro_events}

Berikut adalah data harga Kripto terbaru:
{crypto_prices}

Buatlah ringkasan singkat untuk Kevin mengenai apa saja event penting yang terjadi atau akan terjadi, 
serta update harga Bitcoin/Kripto, dan insight singkat sektor apa yang mungkin menarik.
Gunakan format bullet points dan gaya bahasa asisten personal (Beatrice) yang ceria. 
Jangan terlalu panjang.
"""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error dari Gemini API (Macro Summary): {e}")
        return "Maaf Kevin, Beatrice kesulitan mengambil data makro ekonomi saat ini. 😔"
