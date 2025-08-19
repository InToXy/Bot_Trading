from alertes.botdiscord import send_alert

if __name__ == "__main__":
    print("Test alerte achat...")
    send_alert("BTC", 0.1, "buy")
    print("Test alerte vente...")
    send_alert("ETH", 0.2, "sell")
