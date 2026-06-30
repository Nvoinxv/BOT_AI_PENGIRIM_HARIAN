import os
from datetime import datetime
from dotenv import load_dotenv
import finnhub

# 1. Load variabel dari file .env
load_dotenv()

# 2. Ambil API Key dari environment variable sesuai request lu
api_key = os.getenv("FINHUB_API_KEY")
if not api_key:
    raise ValueError("Error: FINHUB_API_KEY tidak ditemukan di file .env!")

# 3. Inisialisasi Finnhub Client
finnhub_client = finnhub.Client(api_key=api_key)

def ambil_berita_market(kategori="general", jumlah=5):
    """
    Kategori yang didukung Finnhub Free Tier:
    - 'general' (Ekonomi makro, pasar saham global, geopolitik)
    - 'crypto' (Berita dunia Cryptocurrency)
    - 'forex' (Berita pasar mata uang)
    """
    print(f"\n=== Mengambil {jumlah} Berita Terbaru Kategori: {kategori.upper()} ===")
    
    try:
        # Memanggil API Finnhub untuk market news
        berita_list = finnhub_client.general_news(kategori, min_id=0)
        
        # Ambil sejumlah berita yang di-request (default: 5)
        for i, berita in enumerate(berita_list[:jumlah], 1):
            # Konversi UNIX timestamp ke format waktu lokal yang gampang dibaca
            waktu = datetime.fromtimestamp(berita.get('datetime')).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{i}. [{waktu}] - {berita.get('source')}")
            print(f"   Judul: {berita.get('headline')}")
            print(f"   Summary: {berita.get('summary')}")
            print(f"   Link: {berita.get('url')}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Gagal mengambil berita: {e}")

if __name__ == "__main__":
    # Contoh 1: Mengambil berita Ekonomi Umum / Geopolitik
    ambil_berita_market(kategori="general", jumlah=3)
    
    # Contoh 2: Mengambil berita Kripto
    ambil_berita_market(kategori="crypto", jumlah=3)