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

# API für HTML-Frontend
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
    await bot.change_presence(
        activity=disnake.Game(name="Stelle mir eine Frage mit Hey Trust")
    )


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

    # --- Nachrichten starten mit "Hey Trust" ---
    if content.startswith("hey trust") or in_session:
        user_input = content[9:].strip() if content.startswith("hey trust") else content

        sessions[user_id] = now  # start/extend session

        # Versuch DM zu öffnen
        try:
            await message.author.send("⏳ Einen Moment...")
        except disnake.Forbidden:
            await message.channel.send(
                f"{message.author.mention}, ich kann dir leider keine DM senden. Bitte öffne DMs mit mir."
            )
            return

        ai_reply = await generate_ai_answer(user_input)

        # ---- Embed-Antwort in DM ----
        embed = disnake.Embed(
            title="🤖 Trust antwortet",
            description=ai_reply,
            color=0x3498DB  # Blau
        )
        footer_text = "Trust KI – 10 Minuten Session aktiv" if content.startswith("hey trust") else "Trust KI – Session erneuert"
        embed.set_footer(text=footer_text)

        await message.author.send(embed=embed)

        # --- Info im Server-Channel ---
        if not isinstance(message.channel, disnake.DMChannel):
            await message.channel.send(
                f"{message.author.mention}, ich habe dir meine Antwort per DM geschickt 📩"
            )
        return

    # --- User outside session must say "Hey Trust" ---
    if not in_session:
        try:
            await message.author.send("👋 Bitte starte eine Unterhaltung mit **„Hey Trust“**.")
        except disnake.Forbidden:
            await message.channel.send(
                f"{message.author.mention}, ich kann dir leider keine DM senden. Bitte öffne DMs mit mir."
            )
        return

    await bot.process_commands(message)


# ---- KEEP BOT + SERVER RUNNING 24/7 ----
keep_alive()
bot.run(DISCORD_TOKEN)
