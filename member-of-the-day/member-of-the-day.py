import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random
import os
import http.server
import socketserver
import threading

# Bot automatycznie pobiera zmienne z Rendera
TOKEN = os.getenv('token')
GUILD_ID = int(os.getenv('guild'))
ROLE_ID = int(os.getenv('role'))
CHANNEL_ID = int(os.getenv('channel'))
TIME_STR = os.getenv('time', '15:00')

try:
    HOUR, MINUTE = map(int, TIME_STR.split(':'))
except:
    HOUR, MINUTE = 15, 0

intents = discord.Intents.default()
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)
scheduler = AsyncIOScheduler()

async def losowanie_uzytkownika():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"Nie znaleziono serwera o ID {GUILD_ID}")
        return
        
    role = guild.get_role(ROLE_ID)
    channel = bot.get_channel(CHANNEL_ID)
    
    if not role:
        print(f"Nie znaleziono roli o ID {ROLE_ID}")
        return

    # --- ZABEZPIECZENIE PRZED POTRÓJNYM LOSOWANIEM ---
    # Sprawdzamy, czy ktoś aktualnie posiada już tę rolę. 
    # Jeśli rola ma już przypisanego członka, oznacza to, że inna kopia bota właśnie wykonała losowanie.
    if len(role.members) > 0:
        print("Losowanie na dziś zostało już wykonane przez inną instancję bota. Przerywam.")
        return
    # ------------------------------------------------

    # 1. Reset poprzedniej roli (na wypadek, gdyby bot startował po całkowitym czyszczeniu ręcznym)
    for member in role.members:
        try:
            await member.remove_roles(role)
        except Exception as e:
            print(f"Nie udało się odebrać roli użytkownikowi {member.name}: {e}")

    # 2. Losowanie nowego użytkownika
    czlonkowie = [m for m in guild.members if not m.bot]
    
    if czlonkowie:
        zwyciezca = random.choice(czlonkowie)
        try:
            await zwyciezca.add_roles(role)
            if channel:
                await channel.send(f"Gratulacje {zwyciezca.mention} zostajesz cwelem dnia!")
            print(f"Wylosowano użytkownika: {zwyciezca.name}")
        except Exception as e:
            print(f"Błąd podczas nadawania roli/wysyłania wiadomości: {e}")
    else:
        print("Brak użytkowników do wylosowania.")

@bot.event
async def on_ready():
    print(f'Zalogowano pomyślnie jako: {bot.user.name}')
    scheduler.add_job(losowanie_uzytkownika, 'cron', hour=HOUR, minute=MINUTE)
    scheduler.start()
    print(f"Harmonogram uruchomiony! Losowanie codziennie o godzinie {HOUR}:{MINUTE} UTC.")

# Specjalny serwer portu dla platformy Render
def run_dummy_server():
    PORT = int(os.getenv("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

bot.run(TOKEN)
