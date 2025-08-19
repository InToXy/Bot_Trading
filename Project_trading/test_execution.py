from trading.execution import acheter, vendre
import time

# PRI fictif pour le test
PRI = 20
symbol = "BTC/USD"
montant = 10

print(f"PRI fictif = {PRI}")
if PRI < 30:
    print(f"Décision : achat de {montant} € de {symbol}")
    acheter(symbol, montant)
else:
    print("Aucune action")

# Simuler un changement de PRI
time.sleep(2)
PRI = 70
print(f"PRI fictif = {PRI}")
if PRI > 60:
    print(f"Décision : vente de {montant} € de {symbol}")
    vendre(symbol, montant)
else:
    print("Aucune action")
