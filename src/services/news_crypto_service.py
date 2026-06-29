import logging
import requests
from src.config.settings import FINNHUB_API_KEY

logger = logging.getLogger(__name__)

def fetch_finnhub_news(category: str = "general", limit: int = 4) -> str:
    """
    Mengambil berita terbaru dari Finnhub API berdasarkan kategori (general, forex, crypto).
    Mengembalikan string ringkasan berita mentah untuk diproses oleh Gemini AI.
    """
    if not FINNHUB_API_KEY or FINNHUB_API_KEY == "your_finnhub_api_key":
        logger.warning(f"FINNHUB_API_KEY belum valid. Menggunakan data berita simulasi untuk kategori: {category}")
        return _get_mock_news(category)

    url = f"https://finnhub.io/api/v1/news?category={category}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            news_items = response.json()
            if not isinstance(news_items, list) or not news_items:
                return f"Tidak ada berita terbaru untuk kategori {category} saat ini."

            formatted_news = []
            for item in news_items[:limit]:
                headline = item.get("headline", "").strip()
                summary = item.get("summary", "").strip()
                source = item.get("source", "Finnhub")
                if headline:
                    # Gabungkan headline dan summary singkat
                    content = f"- [{source}] {headline}: {summary[:150]}..." if summary else f"- [{source}] {headline}"
                    formatted_news.append(content)
            
            return "\n".join(formatted_news) if formatted_news else f"Tidak ada berita signifikan di kategori {category}."
        else:
            logger.error(f"Gagal mengambil berita Finnhub ({category}). Status: {response.status_code}")
            return _get_mock_news(category)
    except Exception as e:
        logger.error(f"Error koneksi ke Finnhub API ({category}): {e}")
        return _get_mock_news(category)

def _get_mock_news(category: str) -> str:
    if category == "crypto":
        return (
            "- [Bloomberg] Bitcoin Menembus $64,000: Arus masuk ke ETF Bitcoin Spot kembali melonjak drastis didorong optimisme pemotongan suku bunga bunga domestik.\n"
            "- [CoinDesk] Ethereum Volume Lonjak: Aktivitas staking DeFi meningkat pesat seiring peningkatan skalabilitas jaringan lapis kedua (L2)."
        )
    elif category == "forex":
        return (
            "- [Reuters] USD/JPY Melemah: Dolar AS melemah menyusul ekspektasi bahwa Federal Reserve akan segera memangkas suku bunga acuan pada rapat mendatang.\n"
            "- [FXStreet] EUR/USD Stabil: Euro tertahan di level resistance kunci menanti rilis data inflasi zona Euro siang ini."
        )
    else: # general / ekonomi
        return (
            "- [Wall Street Journal] Inflasi CPI AS Melambat: Indeks harga konsumen menunjukkan penurunan tekanan harga, memberi ruang santai bagi kebijakan moneter The Fed.\n"
            "- [CNBC] Pasar Saham AS Menguat: Indeks S&P 500 dan Nasdaq ditutup hijau dipimpin reli saham teknologi dan semikonduktor."
        )

def get_combined_market_news() -> dict:
    """
    Mengambil kumpulan berita Crypto, Forex, dan Ekonomi General sekaligus.
    """
    logger.info("Mengambil berita Crypto, Forex, dan Ekonomi dari Finnhub...")
    return {
        "crypto": fetch_finnhub_news("crypto", limit=4),
        "forex": fetch_finnhub_news("forex", limit=4),
        "general": fetch_finnhub_news("general", limit=4)
    }
