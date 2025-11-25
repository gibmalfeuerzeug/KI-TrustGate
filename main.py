import os
import disnake
from disnake.ext import commands
from openai import OpenAI
from flask import Flask, request, jsonify
from threading import Thread
import time

# Tokens aus Railway Variablen
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---- KEEP ALIVE WEB SERVER (für Railway 24/7) ----
app = Flask('')

@app.route('/')
def home():
    return "Trust Bot läuft 24/7 auf Railway!"

# OPTIONAL: HTML Chat Support (falls du es nutzt)
@app.post("/api/chat")
def api_chat():
    try:
        data = request.json
        prompt = data.get("prompt", "")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Du bist Trust, ein hilfreicher Assistent."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = Thread(target=run_server)
    thread.start()
# ---------------------------------------------------

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---- 10-Minuten Session System ----
sessions = {}  # user_id: timestamp_of_last_message
SESSION_DURATION = 10 * 60  # 10 Minuten in Sekunden


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

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Ein Fehler ist aufgetreten: {e}"


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id
    now = time.time()

    # --- Check if user is in an active 10 min session ---
    in_session = False
    if user_id in sessions:
        if now - sessions[user_id] < SESSION_DURATION:
            in_session = True
        else:
            del sessions[user_id]  # Session expired

    content = message.content.lower()

    # --- Start a new session with "Hey Trust" ---
    if content.startswith("hey trust"):
        user_input = message.content[9:].strip()

        sessions[user_id] = now  # start session

        await message.channel.send("⏳ Einen Moment...")

        ai_reply = await generate_ai_answer(user_input)

        # ---- Embedded Antwort ----
        embed = disnake.Embed(
            title="🤖 Trust antwortet",
            description=ai_reply,
            color=0x00008b
        )
        embed.set_footer(text="Trust KI – 10 Minuten Session aktiv")

        await message.channel.send(embed=embed)
        return

    # --- Continue session without "Hey Trust" ---
    if in_session:
        sessions[user_id] = now  # extend session timer

        await message.channel.send("Einen Moment...")

        ai_reply = await generate_ai_answer(message.content.strip())

        # ---- Embedded Antwort ----
        embed = disnake.Embed(
            title="Trust antwortet dir",
            description=ai_reply,
            color=0x00008b
        )
        embed.set_footer(text="Trust KI – Session erneuert")

        await message.channel.send(embed=embed)
        return

    # --- User outside session must say "Hey Trust" ---
    if not in_session:
        await message.channel.send("👋 Bitte starte eine Unterhaltung mit **„Hey Trust“**.")
        return

    await bot.process_commands(message)


# ---- KEEP BOT + SERVER RUNNING 24/7 ----
keep_alive()
bot.run(DISCORD_TOKEN)
