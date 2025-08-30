import json
import os
import time

def load_cryptos_watchlist(path=None):
    """Charge la liste des cryptos à surveiller depuis un fichier JSON."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), '..', 'cryptos_watchlist.json')
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return data.get('cryptos', [])
    except Exception as e:
        print(f"Erreur lors du chargement de la watchlist : {e}")
        return []
