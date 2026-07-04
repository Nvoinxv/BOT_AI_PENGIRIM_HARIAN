"""
=============================================================================
BEATRICE - BIBLE VERSE & DAILY DEVOTIONAL SERVICE
=============================================================================
Service untuk mengambil ayat Alkitab menggunakan REST API ("Free Use Bible API")
dan menghasilkan renungan harian berformat rapi untuk Kevin.
=============================================================================
"""

import random
import logging
import requests
from src.config.settings import GEMINI_API_KEY
from src.services.discord_service import send_discord_dm_sync
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai

logger = logging.getLogger("BibleService")

# Daftar ayat inspiratif sebagai fallback & variasi referensi Harian
INSPIRATIONAL_VERSES = [
    "John 3:16",
    "Philippians 4:13",
    "Psalms 23:1",
    "Jeremiah 29:11",
    "Romans 8:28",
    "Proverbs 3:5",
    "Isaiah 41:10",
    "Matthew 6:33",
    "Joshua 1:9",
    "2 Corinthians 5:17"
]


def fetch_bible_verse_api(reference: str | None = None) -> dict:
    """
    Mengambil data ayat Alkitab secara resmi melalui REST API (Free Use Bible API / bible-api.com)
    dalam format JSON murni (Bukan scraping HTML online).
    """
    url = f"https://bible-api.com/{reference}" if reference else "https://bible-api.com/?random=verse"
    
    try:
        logger.info(f"🌐 Mengambil data Alkitab dari API: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        ref = data.get("reference", "John 3:16")
        text = data.get("text", "For God so loved the world, that he gave his one and only Son...").strip()
        translation = data.get("translation_name", "World English Bible")
        
        logger.info(f"📖 Berhasil mendapatkan ayat: {ref} ({translation})")
        return {
            "reference": ref,
            "text": text,
            "translation": translation
        }
    except Exception as e:
        logger.warning(f"⚠️ Gagal mengambil dari Free Use Bible API ({e}), menggunakan API fallback lokal...")
        # Fallback lokal jika jaringan/API gangguan agar bot tetap stabil
        return {
            "reference": "Philippians 4:13",
            "text": "I can do all things through Christ, who strengthens me.",
            "translation": "World English Bible"
        }


def generate_devotional_reflection(verse_data: dict) -> str:
    """
    Menerjemahkan ayat ke dalam Bahasa Indonesia yang indah serta menambahkan renungan pagi singkat
    (1-2 paragraf) khusus untuk Kevin menggunakan Gemini AI.
    """
    ref = verse_data["reference"]
    text = verse_data["text"]
    
    if not GEMINI_API_KEY:
        return (
            f"📖 **{ref}**\n\n"
            f"*\"{text}\"*\n\n"
            f"💡 **Renungan Pagi Beatrice**:\n"
            f"Kevin, biarlah ayat hari ini menjadi kekuatan dan penuntun langkahmu sepanjang hari ini. "
            f"Tuhan memberkati setiap pekerjaan dan rencanamu! 🙏❤️"
        )
        
    prompt = f"""
Kamu adalah Beatrice, asisten pribadi rohani yang ramah dan penuh kasih untuk Kevin.
Hari ini kita mendapatkan ayat Alkitab berikut dari API:
Referensi: {ref}
Teks Bahasa Inggris: "{text}"

TUGAS ANDA:
1. Tuliskan kembali referensi ayat dan terjemahan Bahasa Indonesia yang baku dan indah (sesuai Alkitab Terjemahan Baru).
2. Tuliskan renungan pagi singkat (1 paragraf hangat, menyentuh hati, dan aplikatif) untuk menyemangati Kevin sebelum memulai harinya.

Gunakan format STRICT berikut:
📖 RENUNGAN ALKITAB HARIAN
━━━━━━━━━━━━━━━━━━━━━
📜 Ayat Hari Ini: {ref}
"{text}" (Terjemahan Bahasa Indonesia yang sesuai)

💡 Renungan & Doa Pagi untuk Kevin:
[Tuliskan pesan refleksi hangat dan doa singkat di sini]
━━━━━━━━━━━━━━━━━━━━━
🌸 *Blessed morning from Beatrice*
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error Gemini saat membuat renungan: {e}")
        return (
            f"📖 **{ref}**\n\n"
            f"*\"{text}\"*\n\n"
            f"💡 **Renungan Pagi Beatrice**:\n"
            f"Selamat pagi Kevin! Semangat menjalani hari ini, Tuhan senantiasa menyertai dan memberkati setiap langkahmu. 🙏❤️"
        )


def run_daily_bible_job():
    """
    Eksekutor utama untuk tugas harian (Job) renungan Alkitab.
    Mengambil dari API -> Membuat Renungan -> Mengirim eksklusif via Discord DM ke Kevin.
    """
    logger.info("🙏 Memulai tugas harian: Pengiriman Ayat & Renungan Alkitab (Eksklusif via Discord DM)...")
    try:
        # 1. Pilih referensi acak atau ambil random dari API
        use_random_endpoint = random.choice([True, False])
        ref = None if use_random_endpoint else random.choice(INSPIRATIONAL_VERSES)
        
        verse_data = fetch_bible_verse_api(ref)
        
        # 2. Buat renungan pagi
        devotional_content = generate_devotional_reflection(verse_data)
        logger.info("✨ Konten renungan pagi berhasil disusun.")
        
        # 3. Kirim via Discord DM (Khusus Discord DM, tidak dikirim ke email agar inbox tidak bercampur)
        success_dm = send_discord_dm_sync(devotional_content)
        if success_dm:
            logger.info(f"💬 Renungan Alkitab ({verse_data['reference']}) berhasil dikirim eksklusif via Discord DM.")
        else:
            logger.warning("⚠️ Gagal mengirim Renungan via Discord DM (bot mungkin belum siap atau DM nonaktif).")

        return devotional_content
    except Exception as e:
        logger.error(f"💥 Error pada run_daily_bible_job: {e}", exc_info=True)
        return None
