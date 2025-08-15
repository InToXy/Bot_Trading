import discord
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Intents Discord
intents = discord.Intents.default()

# Création du client Discord
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {client.user}")

    # Récupérer le channel
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Test envoie message")
    else:
        print("❌ Channel introuvable.")

    await client.close()  # Ferme le bot après envoi (on peut retirer cette ligne pour le laisser actif)

# Lancer le bot
client.run(TOKEN)
