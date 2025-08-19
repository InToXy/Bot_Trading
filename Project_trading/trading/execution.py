
import logging
import os
from dotenv import load_dotenv
from alpaca_trade_api.rest import REST
from alertes.botdiscord import send_alert

load_dotenv()

API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_API_SECRET')
BASE_URL = 'https://paper-api.alpaca.markets'

api = REST(API_KEY, API_SECRET, BASE_URL)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def acheter(symbol: str, montant_eur: float):
    """Exécute un ordre d'achat pour le montant donné en euros."""
    try:
        order = api.submit_order(
            symbol=symbol,
            notional=montant_eur,
            side="buy",
            type="market",
            time_in_force="gtc"
        )
        logger.info(f"Achat exécuté : {montant_eur} € de {symbol}")
        try:
            send_alert(symbol, montant_eur, "buy")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte Discord : {e}")
        return order
    except Exception as e:
        logger.error(f"Erreur lors de l'achat : {e}")
        return None

def vendre(symbol: str, montant_eur: float):
    """Exécute un ordre de vente pour le montant donné en euros."""
    try:
        order = api.submit_order(
            symbol=symbol,
            notional=montant_eur,
            side="sell",
            type="market",
            time_in_force="gtc"
        )
        logger.info(f"Vente exécutée : {montant_eur} € de {symbol}")
        try:
            send_alert(symbol, montant_eur, "sell")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte Discord : {e}")
        return order
    except Exception as e:
        logger.error(f"Erreur lors de la vente : {e}")
        return None
