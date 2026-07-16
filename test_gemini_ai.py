import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load variabel dari file .env
load_dotenv()

# 2. Pastikan API Key aman dan kebaca (memprioritaskan GEMINI_API_KEY_KEVIN_PETRA untuk tes chatbot)
api_key = os.getenv("GEMINI_API_KEY_KEVIN_PETRA") or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_AKUN_EDWARD_FARREL")
if not api_key:
    raise ValueError("Error: GEMINI_API_KEY_KEVIN_PETRA / GEMINI_API_KEY gak ketemu di file .env, coba cek lagi bro.")

# 3. Inisialisasi client Gemini SDK terbaru
client = genai.Client(api_key=api_key)

def jalankan_chatbot():
    print("=== Chatbot Gemini 2.5 Flash Siap! (Ketik 'keluar' buat selesai) ===\n")
    
    # 4. Set instruksi buat karakter si bot (opsional)
    konfigurasi = types.GenerateContentConfig(
        system_instruction="Kamu adalah asisten AI yang santai, responsif, dan suka bantu pakai bahasa gaul."
    )
    
    # 5. Mulai sesi chat biar bot inget konteks obrolan sebelumnya
    sesi_chat = client.chats.create(
        model="gemini-3.5-flash",
        config=konfigurasi
    )
    
    # 6. Loop buat ngobrol terus-terusan
    while True:
        try:
            user_input = input("Lu: ")
            
            # Cek kalau user mau keluar
            if user_input.lower() == 'keluar':
                print("Bot: Siap bro, cabut dulu ya!")
                break
                
            # Lewatin kalau user cuma enter kosong
            if not user_input.strip():
                continue
                
            # Kirim pesan ke model dan ambil responnya
            respons = sesi_chat.send_message(user_input)
            
            print(f"Bot: {respons.text}\n")
            
        except Exception as e:
            print(f"Waduh ada error nih: {e}\n")

if __name__ == "__main__":
    jalankan_chatbot()