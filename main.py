import os
import discord
from discord.ext import commands
from openai import OpenAI

Tokens aus Railway-Umgebungsvariablen
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"🤖
 Bot gestartet als {bot.user}")


async def generate_ai_answer(prompt: str) -> str:
    """
    Ruft die OpenAI API auf und generiert eine Antwort.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Du bist Trust, ein hilfreicher Discord-Assistent."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
        )

        return response.choices[0].message["content"]

    except Exception as e:
        return f"⚠️
 Ein Fehler ist aufgetreten: {e}"


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # auf "Hey Trust" reagieren
    if message.content.lower().startswith("hey trust"):
        user_input = message.content[9:].strip()

        await message.channel.send("⏳
 Einen Moment, ich denke nach...")

        ai_reply = await generate_ai_answer(user_input)

        await message.channel.send(ai_reply)

    await bot.process_commands(message)


bot.run(DISCORD_TOKEN)
