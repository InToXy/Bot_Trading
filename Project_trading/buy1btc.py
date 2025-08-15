import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi

# ==== CONFIGURATION ====
load_dotenv()
API_KEY = os.getenv('ALPACA_API_KEY')
API_SECRET = os.getenv('ALPACA_API_SECRET')
BASE_URL = "https://paper-api.alpaca.markets"  # Pour mode paper trading
SYMBOL = "BTC/USD"
USD_AMOUNT = 10  # Montant en USD

# Connexion à l'API Alpaca
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# Vérification du compte
account = api.get_account()
print(f"Compte connecté : {account.id}, Solde : {account.cash} USD")

# Passage d'un ordre pour 1 $ de BTC
print(f"Passage d'un ordre MARKET BUY de {USD_AMOUNT} USD sur {SYMBOL}...")
order = api.submit_order(
    symbol=SYMBOL,
    notional=USD_AMOUNT,  # Montant en USD
    side="buy",
    type="market",
    time_in_force="gtc"
)

print("Ordre passé :", order)

# Fin du script
print("Script terminé.")
