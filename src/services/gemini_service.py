import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from src.config.settings import GEMINI_API_KEY
import logging

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY tidak ditemukan di .env!")

_cached_model_name = None

def get_best_gemini_model_name() -> str:
    """
    Menentukan model Gemini yang tersedia di akun melalui panggilan API list_models().
    Hal ini mencegah error 404 ketika model default tidak tersedia atau berbeda penamaan di v1beta.
    """
    global _cached_model_name
    if _cached_model_name:
        return _cached_model_name

    preferred_models = [
        "gemini-2.5-flash",
    ]

    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in getattr(m, 'supported_generation_methods', []):
                available_models.append(m.name)
        
        if available_models:
            logger.info(f"Model Gemini yang mendukung generateContent di API ini: {available_models}")
            for pref in preferred_models:
                for avail in available_models:
                    if pref in avail:
                        logger.info(f"Memilih model Gemini optimal: {avail}")
                        _cached_model_name = avail
                        return avail
            
            _cached_model_name = available_models[0]
            logger.info(f"Memilih model Gemini alternatif: {_cached_model_name}")
            return _cached_model_name
    except Exception as e:
        logger.warning(f"Gagal memeriksa genai.list_models(): {e}. Menggunakan fallback.")

    return "gemini-2.5-flash"

def generate_content_safe(prompt: str, system_instruction: str) -> str:
    """
    Memanggil Gemini API dengan mekanisme fallback otomatis jika terjadi error 404 (model not found).
    """
    global _cached_model_name
    model_name = get_best_gemini_model_name()
    
    candidate_models = [
        model_name,
        "gemini-2.5-flash"
    ]
    
    seen = set()
    last_error = None
    
    for candidate in candidate_models:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        
        try:
            try:
                model = genai.GenerativeModel(
                    model_name=candidate,
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)
            except TypeError:
                model = genai.GenerativeModel(model_name=candidate)
                response = model.generate_content(f"{system_instruction}\n\n{prompt}")
                
            _cached_model_name = candidate
            return response.text.strip()
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "404" in err_str or "not found" in err_str.lower() or "not supported" in err_str.lower():
                logger.warning(f"Model {candidate} gagal (404/Not Supported). Mencoba model fallback berikutnya...")
                _cached_model_name = None
                continue
            else:
                logger.error(f"Error saat generate content dengan {candidate}: {e}")
                raise e
                
    raise last_error if last_error else Exception("Semua model Gemini gagal dijalankan.")

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
        return generate_content_safe(prompt, system_instruction)
    except Exception as e:
        logger.error(f"Error dari Gemini API (Morning Summary): {e}")
        return "Maaf Kevin, Beatrice mengalami masalah saat membaca email hari ini. 😔"

def generate_macro_summary(date_wib_str: str, news_data: dict, econ_events: str = "") -> str:
    """
    Menghasilkan ringkasan berita Finnhub & Kalender Ekonomi dengan analisa sentimen BULL/BEAR/SIDEWAYS.
    """
    system_instruction = (
        "You are Beatrice, Kevin's smart personal AI assistant. "
        "Your task is to analyze financial news from Finnhub and economic calendar events, and explain them in very simple, easy-to-understand Indonesian."
    )
    
    prompt = f"""
Tanggal: {date_wib_str}

Data Berita Terbaru dari Finnhub API:
1. BERITA KRIPTO:
{news_data.get('crypto', 'Tidak ada berita.')}

2. BERITA FOREX:
{news_data.get('forex', 'Tidak ada berita.')}

3. BERITA EKONOMI UMUM:
{news_data.get('general', 'Tidak ada berita.')}

Data Kalender Ekonomi (Economic Calendar):
{econ_events if econ_events else 'Tidak ada event kalender khusus hari ini.'}

TUGAS ANDA:
1. Ringkaslah berita dan event kalender di atas dengan bahasa Indonesia yang SANGAT MUDAH DIPAHAMI oleh pemula sekalipun (hindari jargon rumit tanpa penjelasan).
2. Tentukan sentimen pasar secara keseluruhan dan per kategori: apakah BULLISH (🟢 Bull), BEARISH (🔴 Bear), atau SIDEWAYS (🟡 Sideways).
3. KHUSUS UNTUK KALENDER EKONOMI: Berikan konfirmasi sentimen dampaknya (🟢 BULLISH / 🔴 BEARISH / 🟡 SIDEWAYS) untuk setiap event penting serta penjelasan mudah 1 kalimat mengapa angka/estimasi tersebut berdampak demikian terhadap pasar aset berisiko/kripto.

Gunakan format STRICT berikut ini:

📊 BRIEFING PASAR & EKONOMI (FINNHUB & KALENDER)
Tanggal: {date_wib_str}
━━━━━━━━━━━━━━━━━━━━━
🔥 SENTIMENT PASAR SAAT INI: [🟢 BULLISH / 🔴 BEARISH / 🟡 SIDEWAYS]
[Alasan singkat 1-2 kalimat dengan bahasa gampang dipahami]
━━━━━━━━━━━━━━━━━━━━━
📆 KALENDER EKONOMI AS (Konfirmasi Sentimen)
* [Jam WIB] - [Nama Event] | Est: [X] vs Act: [Y]
  👉 Sentimen: [🟢 BULLISH / 🔴 BEARISH / 🟡 SIDEWAYS] ([Alasan singkat dampak event ini])
* [Jam WIB] - [Nama Event] ...
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
        return generate_content_safe(prompt, system_instruction)
    except Exception as e:
        logger.error(f"Error dari Gemini API (Macro Summary): {e}")
        return "📊 BRIEFING PASAR & EKONOMI\n━━━━━━━━━━━━━━━━━━━━━\n🔥 SENTIMENT PASAR SAAT INI: 🟡 SIDEWAYS\nPasar sedang konsolidasi menanti data baru.\n\n💡 INSIGHT BEATRICE\nMaaf Kevin, Beatrice mengalami sedikit kendala saat memproses data AI saat ini. Tetap kelola risiko dengan baik ya! ❤️"


# Tambahan untuk fitur Chatbot DM
chat_session = None

def get_chat_response(user_message: str) -> str:
    """
    Memproses pesan masuk dari user dan membalas menggunakan Gemini Chat Session.
    """
    global chat_session, _cached_model_name
    
    if chat_session is None:
        system_instruction = (
            "You are Beatrice, Kevin's personal AI assistant. "
            "You are helpful, friendly, speak in Indonesian, and assist Kevin with his daily tasks."
        )
        model_name = get_best_gemini_model_name()
        candidate_models = [
            model_name,
            "gemini-2.5-flash"
        ]
        seen = set()
        for candidate in candidate_models:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            try:
                model = genai.GenerativeModel(
                    model_name=candidate,
                    system_instruction=system_instruction
                )
                chat_session = model.start_chat(history=[])
                _cached_model_name = candidate
                break
            except Exception as e:
                logger.warning(f"Gagal mulai chat session dengan model {candidate}: {e}")
                _cached_model_name = None
                chat_session = None
        
        if chat_session is None:
            return "Maaf Kevin, Beatrice sedang mengalami masalah saat menyiapkan chatbot. 😔"
        
    try:
        response = chat_session.send_message(user_message)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error dari Gemini API (Chatbot): {e}")
        chat_session = None
        return "Maaf Kevin, Beatrice sedang mengalami sedikit gangguan sistem saat membalas pesan. 😔"
