import os
import disnake
from disnake.ext import commands
from openai import OpenAI
from flask import Flask
from threading import Thread

# Tokens aus Railway Variablen
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---- KEEP ALIVE WEB SERVER (für Railway 24/7) ----
app = Flask('')

@app.route('/')
def home():
    return "Trust Bot läuft 24/7 auf Railway!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = Thread(target=run_server)
    thread.start()
# ---------------------------------------------------

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"🤖 Bot gestartet als {bot.user}")


async def generate_ai_answer(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Du bist Trust, ein hilfreicher Discord-Assistent."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"⚠️ Ein Fehler ist aufgetreten: {e}"


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Reaktion auf "Hey Trust"
    if message.content.lower().startswith("hey trust"):
        user_input = message.content[9:].strip()

        await message.channel.send("⏳ Einen Moment...")

        ai_reply = await generate_ai_answer(user_input)
        await message.channel.send(ai_reply)

    await bot.process_commands(message)


# ---- KEEP BOT + SERVER RUNNING 24/7 ----
keep_alive()

bot.run(DISCORD_TOKEN)
