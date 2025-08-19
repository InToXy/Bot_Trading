import backtrader as bt
import pandas as pd

class ImprovedRsiMaStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('fast_ma', 12),
        ('slow_ma', 26),
        ('risk_per_trade', 0.01),  # 1% de risque par trade
        ('stoploss_pct', 0.03),   # 3% de stop-loss
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_ma)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_ma)
        self.order = None
        self.trade_count = 0

    def next(self):
        if self.order:
            return
            
        if not self.position:
            if (self.rsi[0] < self.p.rsi_oversold) and (self.fast_ma[0] > self.slow_ma[0]):
                risk_amount = self.broker.getvalue() * self.p.risk_per_trade
                size = risk_amount / self.data.close[0]
                self.buy(size=size)
        else:
            if (self.rsi[0] > self.p.rsi_overbought) or (self.data.close[0] < (self.position.price * (1 - self.p.stoploss_pct))):
                self.close()

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1

def run_backtest():
    cerebro = bt.Cerebro(stdstats=False)
    
    # Chargement des données
    data = bt.feeds.PandasData(dataname=pd.read_csv('data/BTC-USD.csv', parse_dates=True, index_col=0))
    cerebro.adddata(data)
    
    # Ajout de la stratégie
    cerebro.addstrategy(ImprovedRsiMaStrategy)
    
    # Configuration du broker
    cerebro.broker.setcash(500.0)
    cerebro.broker.setcommission(commission=0.001)
    
    # Analyseurs
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Exécution
    print('--- Début du Backtest ---')
    results = cerebro.run()
    strat = results[0]
    
    # Résultats
    print('\n--- Résultats Finaux ---')
    print(f'Capital initial: 500.00$')
    print(f'Capital final: {cerebro.broker.getvalue():.2f}$')
    
    sharpe = strat.analyzers.sharpe.get_analysis()
    print(f"Sharpe Ratio: {sharpe['sharperatio']:.2f}")
    
    drawdown = strat.analyzers.drawdown.get_analysis()
    print(f"Max Drawdown: {drawdown['max']['drawdown']:.2f}%")
    
    # Gestion des cas sans trades
    trades = strat.analyzers.trades.get_analysis()
    if hasattr(trades, 'total') and hasattr(trades.total, 'closed'):
        print(f"\n--- Statistiques des Trades ---")
        print(f"Nombre total: {trades.total.closed}")
        print(f"Gagnants: {getattr(trades.won, 'total', 0)}")
        print(f"Perdants: {getattr(trades.lost, 'total', 0)}")
        if trades.total.closed > 0:
            print(f"Win Rate: {trades.won.total/trades.total.closed*100:.1f}%")
    else:
        print("\nAucun trade effectué pendant la période")
    
    # Visualisation simplifiée
    try:
        cerebro.plot(style='candlestick', volume=False)
    except:
        print("\nAffichage graphique non disponible")

if __name__ == '__main__':
    run_backtest()