import discord
import logging
import asyncio
import threading
from src.config.settings import DISCORD_TOKEN, DISCORD_USER_ID
from src.services.gemini_service import get_chat_response

logger = logging.getLogger(__name__)

# Membungkam warning voice (PyNaCl / davey) karena Beatrice fokus 100% pada DM & Text Chatbot
class VoiceWarningFilter(logging.Filter):
    def filter(self, record):
        return "voice will NOT be supported" not in record.getMessage()

logging.getLogger('discord.client').addFilter(VoiceWarningFilter())

class BeatriceDiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('Beatrice is ready to receive DMs!')

    async def on_message(self, message):
        # Jangan membalas pesan dari diri sendiri (bot)
        if message.author == self.user:
            return

        # Hanya merespons jika pesan dikirim melalui DM (guild is None)
        if message.guild is None:
            # Opsional: Hanya merespons jika user sesuai dengan DISCORD_USER_ID di .env
            if DISCORD_USER_ID and str(message.author.id) != DISCORD_USER_ID:
                await message.channel.send("Maaf, saya hanya asisten pribadi Kevin. 😌")
                return

            logger.info(f"Menerima DM dari {message.author}: {message.content}")
            
            # Tampilkan status typing di Discord
            async with message.channel.typing():
                # Dapatkan balasan dari Gemini (dijalankan di thread terpisah agar tidak memblokir event loop Discord)
                response = await asyncio.to_thread(get_chat_response, message.content)
                
            # Mengirimkan balasan ke Discord
            # Jika balasan terlalu panjang (>2000 karakter), bagi menjadi beberapa pesan
            for i in range(0, len(response), 2000):
                await message.channel.send(response[i:i+2000])

bot_client = None

def run_discord_bot():
    global bot_client
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN tidak ditemukan, bot Discord tidak dapat dijalankan.")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    
    bot_client = BeatriceDiscordBot(intents=intents)
    
    try:
        # Jalankan bot
        bot_client.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Gagal menjalankan bot Discord: {e}")

def start_discord_bot_in_background():
    """
    Menjalankan Discord Bot dalam thread terpisah agar tidak memblokir scheduler di main.py.
    """
    thread = threading.Thread(target=run_discord_bot, daemon=True)
    thread.start()
    return thread
