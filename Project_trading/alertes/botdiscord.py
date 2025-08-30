def send_status_alert(status: str):
    """
    Envoie une alerte Discord pour le statut du bot (start/stop).
    status doit être 'start' ou 'stop'.
    """
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    if status == 'start':
        message = "🚀 Le bot de trading vient de démarrer !"
    elif status == 'stop':
        message = "🛑 Le bot de trading vient de s'arrêter !"
    else:
        raise ValueError("status doit être 'start' ou 'stop'")

    @client.event
    async def on_ready():
        try:
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                try:
                    await channel.send(message)
                except Exception as e:
                    print(f"❌ Erreur lors de l'envoi du message : {e}")
            else:
                print("❌ Channel introuvable.")
        except Exception as e:
            print(f"❌ Erreur Discord : {e}")
        finally:
            await client.close()

    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"❌ Erreur de connexion Discord : {e}")


# Version synchrone de l'envoi d'alerte Discord
import discord
import os
import dotenv

dotenv.load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

def send_alert(crypto: str, montant: float, action: str):
    """
    Envoie une alerte Discord pour un achat ou une vente (synchrone).
    action doit être 'buy' ou 'sell'.
    Gestion des erreurs d'envoi et de connexion.
    """
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    if action == 'buy':
        message = f"🟢 Achat de {montant} € de {crypto} !"
    elif action == 'sell':
        message = f"🔴 Vente de {montant} € de {crypto} !"
    else:
        raise ValueError("action doit être 'buy' ou 'sell'")

    @client.event
    async def on_ready():
        try:
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                try:
                    await channel.send(message)
                except Exception as e:
                    print(f"❌ Erreur lors de l'envoi du message : {e}")
            else:
                print("❌ Channel introuvable.")
        except Exception as e:
            print(f"❌ Erreur Discord : {e}")
        finally:
            await client.close()

    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"❌ Erreur de connexion Discord : {e}")
