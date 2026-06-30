import discord
from discord.ext import commands

# Aktifkan intent untuk membaca isi pesan
intents = discord.Intents.default()
intents.message_content = True

# Prefix command
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot berhasil login sebagai {bot.user}")


@bot.event
async def on_message(message):
    # Jangan balas pesan dari bot sendiri
    if message.author == bot.user:
        return

    # Jika isi pesan "Halo"
    if message.content.lower() == "halo":
        await message.channel.send("Halo")

    # Agar command tetap bisa dipakai
    await bot.process_commands(message)


# Ganti dengan token bot Discord milikmu
TOKEN = "DISCORD_TOKEN"

bot.run(TOKEN)