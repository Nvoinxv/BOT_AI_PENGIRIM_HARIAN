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

def generate_macro_summary(date_wib_str: str, news_data: dict, econ_events: str = "") -> str:
    """
    Menghasilkan ringkasan berita Finnhub (Kripto, Forex, Ekonomi) dengan analisa sentimen BULL/BEAR/SIDEWAYS.
    """
    system_instruction = (
        "You are Beatrice, Kevin's smart personal AI assistant. "
        "Your task is to analyze financial news from Finnhub (crypto, forex, general economy) and explain them in very simple, easy-to-understand Indonesian."
    )
    
    prompt = f"""
Tanggal: {date_wib_str}

Berikut adalah data berita terbaru dari Finnhub API:
1. BERITA KRIPTO:
{news_data.get('crypto', 'Tidak ada berita.')}

2. BERITA FOREX:
{news_data.get('forex', 'Tidak ada berita.')}

3. BERITA EKONOMI UMUM:
{news_data.get('general', 'Tidak ada berita.')}

Data Tambahan Kalender Ekonomi:
{econ_events if econ_events else 'Tidak ada event kalender khusus hari ini.'}

TUGAS ANDA:
Ringkaslah berita-berita di atas dengan bahasa Indonesia yang SANGAT MUDAH DIPAHAMI oleh pemula sekalipun (hindari jargon rumit tanpa penjelasan).
Tentukan sentimen pasar secara keseluruhan dan per kategori: apakah BULLISH (🟢 Bull), BEARISH (🔴 Bear), atau SIDEWAYS (🟡 Sideways).

Gunakan format STRICT berikut ini:

📊 BRIEFING PASAR & EKONOMI (FINNHUB)
Tanggal: {date_wib_str}
━━━━━━━━━━━━━━━━━━━━━
🔥 SENTIMENT PASAR SAAT INI: [🟢 BULLISH / 🔴 BEARISH / 🟡 SIDEWAYS]
[Alasan singkat 1-2 kalimat dengan bahasa gampang dipahami]
━━━━━━━━━━━━━━━━━━━━━
🪙 BERITA KRIPTO (Sentimen: [Bull/Bear/Sideways])
* [poin 1 diringkas mudah]
* [poin 2 diringkas mudah]
━━━━━━━━━━━━━━━━━━━━━
💵 BERITA FOREX & EKONOMI (Sentimen: [Bull/Bear/Sideways])
* [poin 1 diringkas mudah]
* [poin 2 diringkas mudah]
━━━━━━━━━━━━━━━━━━━━━
💡 INSIGHT BEATRICE
[Kesimpulan & saran pantauan santai dari Beatrice untuk Kevin]
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
        return "📊 BRIEFING PASAR & EKONOMI\n━━━━━━━━━━━━━━━━━━━━━\n🔥 SENTIMENT PASAR SAAT INI: 🟡 SIDEWAYS\nPasar sedang konsolidasi menanti data baru.\n\n💡 INSIGHT BEATRICE\nMaaf Kevin, Beatrice mengalami sedikit kendala saat memproses data AI saat ini. Tetap kelola risiko dengan baik ya! ❤️"


# Tambahan untuk fitur Chatbot DM
chat_session = None

def get_chat_response(user_message: str) -> str:
    """
    Memproses pesan masuk dari user dan membalas menggunakan Gemini Chat Session.
    """
    global chat_session
    
    if chat_session is None:
        system_instruction = (
            "You are Beatrice, Kevin's personal AI assistant. "
            "You are helpful, friendly, speak in Indonesian, and assist Kevin with his daily tasks."
        )
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system_instruction
            )
            chat_session = model.start_chat(history=[])
        except Exception as e:
            logger.error(f"Gagal inisialisasi Gemini Chat Session: {e}")
            return "Maaf Kevin, Beatrice sedang mengalami masalah saat menyiapkan chatbot. 😔"
        
    try:
        response = chat_session.send_message(user_message)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error dari Gemini API (Chatbot): {e}")
        return "Maaf Kevin, Beatrice sedang mengalami sedikit gangguan sistem saat membalas pesan. 😔"
