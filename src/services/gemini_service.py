import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from src.config.settings import (
    GEMINI_API_KEY,
    GEMINI_API_KEY_AKUN_EDWARD_FARREL,
    GEMINI_API_KEY_KEVIN_PETRA
)
from src.services.db_service import get_db
import logging

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY tidak ditemukan di .env!")

_cached_model_names = {}

def get_best_gemini_model_name(api_key: str = None) -> str:
    """
    Menentukan model Gemini yang tersedia di akun melalui panggilan API list_models().
    Hal ini mencegah error 404 ketika model default tidak tersedia atau berbeda penamaan di v1beta.
    """
    global _cached_model_names
    cache_key = api_key or "default"
    if cache_key in _cached_model_names:
        return _cached_model_names[cache_key]

    preferred_models = [
        "gemini-2.5-flash",
    ]

    try:
        if api_key:
            genai.configure(api_key=api_key)
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
                        _cached_model_names[cache_key] = avail
                        return avail
            
            _cached_model_names[cache_key] = available_models[0]
            logger.info(f"Memilih model Gemini alternatif: {_cached_model_names[cache_key]}")
            return _cached_model_names[cache_key]
    except Exception as e:
        logger.warning(f"Gagal memeriksa genai.list_models(): {e}. Menggunakan fallback.")

    return "gemini-2.5-flash"

def generate_content_safe(prompt: str, system_instruction: str, api_key: str = None) -> str:
    """
    Memanggil Gemini API dengan mekanisme fallback otomatis jika terjadi error 404 (model not found).
    """
    global _cached_model_names
    cache_key = api_key or "default"
    if api_key:
        genai.configure(api_key=api_key)
    client_opts = {'api_key': api_key} if api_key else None

    model_name = get_best_gemini_model_name(api_key=api_key)
    
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
                    system_instruction=system_instruction,
                    client_options=client_opts
                )
                response = model.generate_content(prompt)
            except TypeError:
                try:
                    model = genai.GenerativeModel(
                        model_name=candidate,
                        system_instruction=system_instruction
                    )
                    response = model.generate_content(prompt)
                except TypeError:
                    model = genai.GenerativeModel(model_name=candidate)
                    response = model.generate_content(f"{system_instruction}\n\n{prompt}")
                
            _cached_model_names[cache_key] = candidate
            return response.text.strip()
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "404" in err_str or "not found" in err_str.lower() or "not supported" in err_str.lower():
                logger.warning(f"Model {candidate} gagal (404/Not Supported). Mencoba model fallback berikutnya...")
                if cache_key in _cached_model_names:
                    del _cached_model_names[cache_key]
                continue
            else:
                logger.error(f"Error saat generate content dengan {candidate}: {e}")
                raise e
                
    raise last_error if last_error else Exception("Semua model Gemini gagal dijalankan.")

def generate_morning_summary(date_wib_str: str, emails_content: str) -> str:
    """
    Menghasilkan ringkasan email harian (Pagi) dengan personalitas Beatrice.
    Fokus memprioritaskan email kuliah/kampus (UK Petra/Petraku/BAKP/Dosen) dan hal penting lainnya.
    Dilengkapi pengecekan riwayat MongoDB agar tidak mengulang pola/kalimat yang sama.
    """
    db = get_db()
    api_key = GEMINI_API_KEY_AKUN_EDWARD_FARREL or GEMINI_API_KEY
    if GEMINI_API_KEY_AKUN_EDWARD_FARREL:
        logger.info("Menggunakan API Key terpisah (GEMINI_API_KEY_AKUN_EDWARD_FARREL) untuk membaca pesan email.")
    recent_context = db.get_recent_briefings_context("morning", limit=1)
    context_instruction = f"\nCatatan Briefing Pagi Sebelumnya (hindari pengulangan frasa/pengantar yang persis sama):\n{recent_context}\n" if recent_context else ""

    system_instruction = (
        "You are Beatrice, Kevin's smart personal AI assistant. "
        "Your primary task is to analyze Kevin's Gmail inbox, specifically focusing on reading and summarizing "
        "college/university emails (like Petra Christian University / Petraku, BAKP, lecturers, BEM, assignments, organization) "
        "and important academic/work schedules or deadlines. Ignore promotional spam or irrelevant newsletters. "
        "Generate a clear, professional summary in Indonesian without repetitive expressions."
    )

    prompt = f"""
Step 1: The current date in WIB is: {date_wib_str}
{context_instruction}
Step 2: Here is the recent Gmail data from the last 24 hours (including subject and body snippets):
{emails_content}

TUGAS ANDA:
1. Analisis seluruh email di atas. FOKUS UTAMA pada email-email kuliah/kampus (seperti dari Petra Christian University / Petraku / BAKP / dosen / BEM / tugas / organisasi / perpustakaan) serta pengumuman atau jadwal penting lainnya.
2. Abaikan pesan promosi, spam, atau newsletter umum yang tidak penting bagi kuliah/pekerjaan Kevin.
3. Ekstrak informasi krusial seperti: jam perkuliahan, deadline pengumpulan tugas, tenggat waktu KRS, atau link meeting/ruangan.

Step 3: Compose a summary in Indonesian (under 3800 chars) using EXACTLY this template:

📅 RANGKUMAN EMAIL KULIAH & PENTING
{date_wib_str}
━━━━━━━━━━━━━━━━━━━━━
📧 EMAIL KULIAH & PENTING
* [Pengirim/Topik]: [Ringkasan jelas 1-2 kalimat beserta detail waktu/ruangan/deadline jika ada]
(atau: "Inbox aman, tidak ada email kuliah/penting baru ✅" jika tidak ada)
━━━━━━━━━━━━━━━━━━━━━
📆 JADWAL & AGENDA HARI INI
* [Waktu]: [Detail event/perkuliahan/kegiatan]
(atau: "Hari ini bebas agenda perkuliahan/meeting 🎉" jika tidak ada)
━━━━━━━━━━━━━━━━━━━━━
⚡ DEADLINE / PERLU DIPERHATIKAN
[Sebutkan deadline tugas, KRS, atau hal penting yang membutuhkan tindakan Kevin dalam waktu dekat]
━━━━━━━━━━━━━━━━━━━━━
Have a productive day, Kevin! ❤️
"""

    try:
        res = generate_content_safe(prompt, system_instruction, api_key=api_key)
        if db.check_if_similar_exists(res, briefing_type="morning", similarity_threshold=0.75):
            logger.warning("Kemiripan tinggi dengan briefing pagi sebelumnya, mencoba regenerasi variasi...")
            res = generate_content_safe(prompt + "\n\nCatatan Tambahan: Gunakan variasi kosakata baru dan pastikan tidak mengulang frasa kemaren.", system_instruction, api_key=api_key)
        db.save_briefing(res, briefing_type="morning")
        return res
    except Exception as e:
        logger.error(f"Error dari Gemini API (Morning Summary): {e}")
        return "Maaf Kevin, Beatrice mengalami masalah saat membaca email kuliah/penting hari ini. 😔"

def generate_macro_summary(date_wib_str: str, news_data: dict, econ_events: str = "") -> str:
    """
    Menghasilkan ringkasan berita Finnhub & Kalender Ekonomi dengan analisa sentimen BULL/BEAR/SIDEWAYS.
    Melakukan verifikasi MongoDB agar tidak mengulangi berita atau analisis yang sama persis.
    """
    db = get_db()
    api_key = GEMINI_API_KEY_KEVIN_PETRA or GEMINI_API_KEY
    if GEMINI_API_KEY_KEVIN_PETRA:
        logger.info("Menggunakan API Key terpisah (GEMINI_API_KEY_KEVIN_PETRA) untuk analisa pasar & makro.")
    recent_context = db.get_recent_briefings_context("macro", limit=1)
    context_instruction = f"\nRiwayat Briefing Makro Sebelumnya (AGAR TIDAK MENGULANG POIN BERITA YANG PERSIS SAMA):\n{recent_context}\n" if recent_context else ""

    system_instruction = (
        "You are Beatrice, Kevin's smart personal AI assistant. "
        "Your task is to analyze financial news from Finnhub and economic calendar events, and explain them in very simple, easy-to-understand Indonesian without repetition."
    )
    
    prompt = f"""
Tanggal: {date_wib_str}
{context_instruction}
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
1. Ringkaslah berita dan event kalender di atas dengan bahasa Indonesia yang SANGAT MUDAH DIPAHAMI oleh pemula sekalipun (hindari jargon rumit tanpa penjelasan). Jika ada berita yang sama persis dengan riwayat sebelumnya, abaikan atau pilih berita lain.
2. Tentukan sentimen pasar secara keseluruhan dan per kategori: apakah BULLISH (🟢 Bull), BEARISH (🔴 Bear), atau SIDEWAYS (🟡 Sideways). PASTIKAN Anda menyebutkan secara spesifik sentimen tersebut BERLAKU UNTUK ASET APA (Misal: "Bearish for Crypto", "Bullish for USD", "Sideways for Stocks").
3. KHUSUS UNTUK KALENDER EKONOMI: Berikan konfirmasi sentimen dampaknya (🟢 BULLISH / 🔴 BEARISH / 🟡 SIDEWAYS) beserta aset spesifiknya (misal: "Bullish for USD") untuk setiap event penting serta penjelasan mudah 1 kalimat mengapa angka/estimasi tersebut berdampak demikian.

Gunakan format STRICT berikut ini:

📊 BRIEFING PASAR & EKONOMI (FINNHUB & KALENDER)
Tanggal: {date_wib_str}
━━━━━━━━━━━━━━━━━━━━━
🔥 SENTIMENT PASAR SAAT INI: [🟢 BULLISH / 🔴 BEARISH / 🟡 SIDEWAYS] for [Nama Aset/Market]
[Alasan singkat 1-2 kalimat dengan bahasa gampang dipahami]
━━━━━━━━━━━━━━━━━━━━━
📆 KALENDER EKONOMI AS (Konfirmasi Sentimen)
* [Jam WIB] - [Nama Event] | Est: [X] vs Act: [Y]
  👉 Sentimen: [🟢 BULLISH / 🔴 BEARISH / 🟡 SIDEWAYS] for [Nama Aset] ([Alasan singkat dampak event ini])
* [Jam WIB] - [Nama Event] ...
━━━━━━━━━━━━━━━━━━━━━
🪙 BERITA KRIPTO (Sentimen: [Bull/Bear/Sideways] for Crypto)
* [poin 1 diringkas mudah]
* [poin 2 diringkas mudah]
━━━━━━━━━━━━━━━━━━━━━
💵 BERITA FOREX & EKONOMI (Sentimen: [Bull/Bear/Sideways] for [USD/Forex])
* [poin 1 diringkas mudah]
* [poin 2 diringkas mudah]
━━━━━━━━━━━━━━━━━━━━━
💡 INSIGHT BEATRICE
[Kesimpulan & saran pantauan santai dari Beatrice untuk Kevin]
"""
    try:
        res = generate_content_safe(prompt, system_instruction, api_key=api_key)
        if db.check_if_similar_exists(res, briefing_type="macro", similarity_threshold=0.75):
            logger.warning("Kemiripan tinggi dengan briefing makro sebelumnya, mencoba regenerasi variasi...")
            res = generate_content_safe(prompt + "\n\nCatatan Tambahan: Berikan analisis sudut pandang yang lebih segar dan jangan mengulangi kalimat di riwayat sebelumnya.", system_instruction, api_key=api_key)
        db.save_briefing(res, briefing_type="macro")
        return res
    except Exception as e:
        logger.error(f"Error dari Gemini API (Macro Summary): {e}")
        return "📊 BRIEFING PASAR & EKONOMI\n━━━━━━━━━━━━━━━━━━━━━\n🔥 SENTIMENT PASAR SAAT INI: 🟡 SIDEWAYS\nPasar sedang konsolidasi menanti data baru.\n\n💡 INSIGHT BEATRICE\nMaaf Kevin, Beatrice mengalami sedikit kendala saat memproses data AI saat ini. Tetap kelola risiko dengan baik ya! ❤️"


# Tambahan untuk fitur Chatbot DM
chat_session = None

def get_chat_response(user_message: str) -> str:
    """
    Memproses pesan masuk dari user dan membalas menggunakan Gemini Chat Session.
    Menggunakan riwayat memori MongoDB agar percakapan terus bersambung dan tidak monoton/mengulang.
    """
    global chat_session, _cached_model_names
    db = get_db()
    api_key = GEMINI_API_KEY_KEVIN_PETRA or GEMINI_API_KEY
    if GEMINI_API_KEY_KEVIN_PETRA:
        logger.info("Menggunakan API Key terpisah (GEMINI_API_KEY_KEVIN_PETRA) untuk Chatbot DM.")
    
    if api_key:
        genai.configure(api_key=api_key)
    client_opts = {'api_key': api_key} if api_key else None
    
    if chat_session is None:
        system_instruction = (
            "You are Beatrice, Kevin's smart and empathetic personal AI assistant. "
            "You speak friendly Indonesian, remember previous chat history, avoid repetitive responses, and assist Kevin with daily tasks."
        )
        model_name = get_best_gemini_model_name(api_key=api_key)
        candidate_models = [
            model_name,
            "gemini-2.5-flash"
        ]
        seen = set()
        loaded_history = db.get_chat_history(limit=16)
        
        for candidate in candidate_models:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            try:
                try:
                    model = genai.GenerativeModel(
                        model_name=candidate,
                        system_instruction=system_instruction,
                        client_options=client_opts
                    )
                except TypeError:
                    model = genai.GenerativeModel(
                        model_name=candidate,
                        system_instruction=system_instruction
                    )
                chat_session = model.start_chat(history=loaded_history)
                break
            except Exception as e:
                logger.warning(f"Gagal mulai chat session dengan model {candidate}: {e}")
                chat_session = None
        
        if chat_session is None:
            return "Maaf Kevin, Beatrice sedang mengalami masalah saat menyiapkan chatbot. 😔"
        
    try:
        if api_key:
            genai.configure(api_key=api_key)
        db.save_chat_message("user", user_message)
        response = chat_session.send_message(user_message)
        reply = response.text.strip()
        db.save_chat_message("model", reply)
        return reply
    except Exception as e:
        logger.error(f"Error dari Gemini API (Chatbot): {e}")
        chat_session = None
        return "Maaf Kevin, Beatrice sedang mengalami sedikit gangguan sistem saat membalas pesan. 😔"
