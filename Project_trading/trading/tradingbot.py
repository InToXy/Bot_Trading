# importations nécessaires

import threading
import time
import pandas as pd
import numpy as np
import logging
import requests
import signal
import sys
from trading.execution import acheter, vendre, api
from trading.watchlist import load_cryptos_watchlist
from alertes.botdiscord import send_status_alert

def get_klines(symbol, timeframe='1Min', limit=100):
	# Utilise Alpaca pour récupérer les prix de clôture
	try:
		bars = api.get_crypto_bars(symbol, timeframe).df
		if bars.empty:
			logging.warning(f"Aucune donnée de prix trouvée pour {symbol}.")
			return []
		closes = bars['close'][-limit:].tolist()
		logging.debug(f"{symbol} closes: {closes}")
		return closes
	except Exception as e:
		logging.error(f"Erreur récupération prix Alpaca pour {symbol}: {e}")
		return []

def compute_rsi(prices, period=14):
	prices = pd.Series(prices)
	delta = prices.diff()
	gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
	loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
	rs = gain / loss
	rsi = 100 - (100 / (1 + rs))
	return rsi.iloc[-1]

def trader_thread(symbol, montant_eur):
	logging.info(f"Thread lancé pour {symbol}")
	montant_eur = 100  # Achat de 100€
	last_buy_time = 0
	while True:
		try:
			prices = get_klines(symbol)
			if not prices or len(prices) < 15:
				logging.warning(f"Pas assez de données pour {symbol} (n={len(prices)}), attente...")
				time.sleep(10)
				continue
			try:
				rsi = compute_rsi(prices)
			except Exception as e:
				logging.error(f"Erreur calcul RSI pour {symbol}: {e}")
				time.sleep(30)
				continue
			logging.info(f"{symbol} RSI: {rsi:.2f}")
			now = time.time()
			# Achat toutes les 24h si RSI <= 30
			if rsi <= 30:
				if (last_buy_time == 0 or now - last_buy_time >= 86400):
					logging.info(f"Signal ACHAT détecté pour {symbol} (RSI={rsi:.2f})")
					try:
						acheter(symbol, montant_eur)
						last_buy_time = now
					except Exception as e:
						logging.error(f"Erreur lors de l'achat de {symbol}: {e}")
				else:
					hours_left = (86400 - (now - last_buy_time)) / 3600
					logging.info(f"Achat déjà effectué pour {symbol} il y a moins de 24h. Prochain achat possible dans {hours_left:.1f}h.")
			elif rsi >= 70:
				logging.info(f"Signal VENTE détecté pour {symbol} (RSI={rsi:.2f})")
				try:
					vendre(symbol, montant_eur)
				except Exception as e:
					logging.error(f"Erreur lors de la vente de {symbol}: {e}")
		except Exception as e:
			logging.error(f"Erreur inattendue dans le thread {symbol}: {e}")
		time.sleep(60)  # Attendre 1 min avant la prochaine vérification

def main():
	threads = {}

	# Envoi alerte démarrage
	send_status_alert('start')

	def handle_exit(signum, frame):
		send_status_alert('stop')
		sys.exit(0)

	signal.signal(signal.SIGINT, handle_exit)
	signal.signal(signal.SIGTERM, handle_exit)

	try:
		while True:
			cryptos = load_cryptos_watchlist()
			for symbol in cryptos:
				if symbol not in threads or not threads[symbol].is_alive():
					t = threading.Thread(target=trader_thread, args=(symbol, 100), daemon=True)
					t.start()
					threads[symbol] = t
			time.sleep(30)
	except SystemExit:
		pass
	except Exception as e:
		logging.error(f"Erreur inattendue : {e}")
		send_status_alert('stop')

if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
	main()
