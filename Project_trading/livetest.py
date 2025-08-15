import os
import time
import pandas as pd
import os 
import numpy as np
from dotenv import load_dotenv
from alpaca_trade_api.rest import REST
from datetime import datetime, timezone, timedelta
import logging

# Configuration AGRESSIVE pour 100€ - Objectif: Multiplier par 5-10x
load_dotenv()

# Cryptos étendus pour plus d'opportunités (compte papier)
SYMBOLS = ['BTC/USD', 'PEPE/USD', 'DOGE/USD', 'FLOKI/USD', 'BONK/USD', 'ADA/USD', 'MATIC/USD', 'DOT/USD', 'AVAX/USD', 'SOL/USD']  
TIMEFRAME = '1Min'  # Scalping ultra-rapide
BUDGET = 1000  # Budget de test papier
RISK_PER_TRADE = 0.15  # 15% par trade (plus conservateur avec plus de capital)
LEVERAGE = 2  # Levier réduit avec plus de capital
MIN_PROFIT_TARGET = 0.04  # 4% minimum pour prendre profits
STOP_LOSS = 0.06  # 6% stop loss (plus serré)
DAILY_TARGET = 0.15  # Objectif: +15% par jour (150$ par jour)

# Setup logging agressif
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

api = REST(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_API_SECRET'),
    base_url='https://paper-api.alpaca.markets'
)

class AggressiveScalper:
    def __init__(self):
        # Récupération du capital réel via API
        try:
            account = api.get_account()
            self.initial_budget = float(account.portfolio_value)
            self.buying_power = float(account.buying_power)
            logger.info(f"💰 Capital initial détecté: {self.initial_budget:.2f}$")
            logger.info(f"💳 Pouvoir d'achat: {self.buying_power:.2f}$")
        except Exception as e:
            logger.error(f"❌ Erreur récupération compte: {e}")
            self.initial_budget = 1000  # Fallback
            self.buying_power = 1000
        
        self.daily_profit = 0
        self.trades_today = 0
        self.max_trades_per_day = 25
        self.active_positions = {}
        self.trade_history = []
        self.test_mode = False  # Désactive le mode test
        self.current_balance = self.buying_power  # Pour simulation, mais pas utilisé pour l'ordre réel
        
        # Objectifs basés sur le capital réel
        self.targets = [
            self.initial_budget * 1.15,  # +15%
            self.initial_budget * 1.30,  # +30%
            self.initial_budget * 1.50,  # +50%
            self.initial_budget * 1.75,  # +75%
            self.initial_budget * 2.00,  # +100%
            self.initial_budget * 2.50,  # +150%
            self.initial_budget * 3.00   # +200%
        ]
        self.current_target_index = 0
        
    def get_current_account_status(self):
        """Récupère le statut actuel du compte via API"""
        try:
            account = api.get_account()
            portfolio_value = float(account.portfolio_value)
            buying_power = float(account.buying_power)
            # day_trade_buying_power n'existe pas pour les comptes crypto
            # Calcul du P&L depuis le début
            total_pnl = portfolio_value - self.initial_budget
            total_pnl_pct = (total_pnl / self.initial_budget) * 100
            return {
                'portfolio_value': portfolio_value,
                'buying_power': buying_power,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'positions_count': len(api.list_positions())
            }
        except Exception as e:
            logger.error(f"❌ Erreur récupération statut compte: {e}")
            return None

    def get_ultra_volatile_cryptos(self):
        """Identifie les cryptos avec le plus de volatilité (= profit potentiel)"""
        try:
            volatility_scores = {}
            for symbol in SYMBOLS:
                # Données courtes pour rapidité
                bars = api.get_crypto_bars(symbol, '1Min', limit=30).df
                if len(bars) < 10:
                    continue
                # Calcul volatilité + momentum
                price_changes = bars['close'].pct_change().abs()
                volatility = price_changes.mean()
                # Momentum récent (dernières 5 minutes)
                recent_momentum = (bars['close'].iloc[-1] - bars['close'].iloc[-5]) / bars['close'].iloc[-5]
                # Volume explosion (protection contre division par zéro)
                avg_volume = bars['volume'].mean()
                if avg_volume > 0:
                    volume_spike = bars['volume'].iloc[-1] / avg_volume
                else:
                    volume_spike = 1.0
                # Score composite pour opportunité (amélioration du calcul)
                if volatility > 0 and abs(recent_momentum) > 0.001:  # Minimum de mouvement
                    momentum_factor = min(abs(recent_momentum) * 100, 5)  # Max 5x
                    volume_factor = min(volume_spike, 10)  # Max 10x pour éviter les outliers
                    opportunity_score = volatility * momentum_factor * volume_factor
                else:
                    opportunity_score = 0
                volatility_scores[symbol] = {
                    'score': opportunity_score,
                    'volatility': volatility,
                    'momentum': recent_momentum,
                    'volume_spike': volume_spike,
                    'price': bars['close'].iloc[-1]
                }
            # Tri par opportunité
            sorted_opportunities = sorted(
                volatility_scores.items(), 
                key=lambda x: x[1]['score'], 
                reverse=True
            )
            if sorted_opportunities:
                best_symbol, data = sorted_opportunities[0]
                logger.info(f"🔥 CRYPTO LA PLUS CHAUDE: {best_symbol}")
                logger.info(f"📊 Score opportunité: {data['score']:.4f}")
                logger.info(f"⚡ Volatilité: {data['volatility']:.3%}")
                logger.info(f"🚀 Momentum: {data['momentum']:.2%}")
                logger.info(f"🔊 Volume: {data['volume_spike']:.1f}x")
            return sorted_opportunities[:3]  # Top 3 pour diversification
        except Exception as e:
            logger.error(f"❌ Erreur sélection cryptos: {e}")
            return []
    
    def detect_breakout_signal(self, symbol):
        """Détection de signaux de breakout pour gains rapides"""
        try:
            # Données 1 minute pour réactivité maximale
            bars = api.get_crypto_bars(symbol, '1Min', limit=50).df
            
            if len(bars) < 20:
                return None
                
            # Indicateurs ultra-rapides
            close = bars['close']
            volume = bars['volume']
            
            # Support/Résistance rapide
            high_resistance = close.rolling(10).max().iloc[-1]
            low_support = close.rolling(10).min().iloc[-1]
            current_price = close.iloc[-1]
            
            # Momentum explosif
            momentum_1m = close.pct_change(1).iloc[-1]
            momentum_3m = close.pct_change(3).iloc[-1]
            momentum_5m = close.pct_change(5).iloc[-1]
            
            # Volume confirmation (protection division par zéro)
            avg_volume = volume.rolling(20).mean().iloc[-1]
            current_volume = volume.iloc[-1]
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
            else:
                volume_ratio = 1.0
            
            # RSI ultra-rapide (7 périodes) avec protection
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(7).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(7).mean()
            
            # Protection contre division par zéro pour RSI
            loss_val = loss.iloc[-1]
            if loss_val > 0:
                rs = gain.iloc[-1] / loss_val
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50  # Valeur neutre si pas de perte
            
            # Conditions de breakout BULLISH (ultra faciles pour forcer un ordre)
            bullish_breakout = (
                momentum_1m > 0.00001 and
                momentum_3m > 0.00001 and
                current_price > high_resistance * 0.99 and
                volume_ratio > 0.5 and
                rsi < 99 and
                momentum_5m > -1
            )

            # Conditions de breakout BEARISH (ultra faciles pour forcer un SELL)
            bearish_breakout = (
                momentum_1m < -0.00001 and
                momentum_3m < -0.00001 and
                current_price < low_support * 1.01 and
                volume_ratio > 0.5 and
                rsi > 1 and
                momentum_5m < 1
            )
            
            # Score de confiance (ajusté pour compte papier)
            confidence = 0
            if bullish_breakout:
                confidence = min(abs(momentum_3m) * 20 + volume_ratio / 3 + 0.3, 1.0)  # Boost de base
            elif bearish_breakout:
                confidence = min(abs(momentum_3m) * 20 + volume_ratio / 3 + 0.3, 1.0)
            
            return {
                'symbol': symbol,
                'signal': 'BUY' if bullish_breakout else ('SELL' if bearish_breakout else 'HOLD'),
                'confidence': confidence,
                'price': current_price,
                'momentum_1m': momentum_1m,
                'momentum_3m': momentum_3m,
                'volume_ratio': volume_ratio,
                'rsi': rsi,
                'resistance': high_resistance,
                'support': low_support
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur signal {symbol}: {e}")
            return None
    
    def calculate_aggressive_position(self, signal):
        """Calcul de position agressive basé sur le capital réel du compte"""
        try:
            # Récupération du capital réel via API
            account_status = self.get_current_account_status()
            if not account_status:
                return None
            
            available_capital = account_status['buying_power']
            
            logger.info(f"💰 Capital disponible: {available_capital:.2f}$")
            
            # Taille de base basée sur le capital réel
            base_amount = available_capital * RISK_PER_TRADE
            
            # Multiplicateur selon confiance
            confidence_multiplier = 1 + signal['confidence']
            
            # Multiplicateur selon momentum
            momentum_multiplier = 1 + min(abs(signal['momentum_3m']) * 5, 1)
            
            # Taille finale (avec limites adaptées au capital disponible)
            max_position_size = min(available_capital * 0.25, 500)  # Max 25% ou 500$ par position
            
            position_value = min(
                base_amount * confidence_multiplier * momentum_multiplier,
                max_position_size
            )
            
            quantity = position_value / signal['price']
            
            return {
                'quantity': quantity,
                'value': position_value,
                'stop_loss': signal['price'] * (0.94 if signal['signal'] == 'BUY' else 1.06),  # 6% stop
                'take_profit_1': signal['price'] * (1.04 if signal['signal'] == 'BUY' else 0.96),  # 4% TP1
                'take_profit_2': signal['price'] * (1.08 if signal['signal'] == 'BUY' else 0.92),  # 8% TP2
                'confidence': signal['confidence']
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul position: {e}")
            return None
    
    def execute_aggressive_trade(self, signal, position):
        """Exécution de trade ultra-agressive"""
        try:
            symbol = signal['symbol']
            
            # Vérifications finales
            if self.trades_today >= self.max_trades_per_day:
                logger.info("⏰ Limite de trades quotidiens atteinte")
                return False
                
            if position['value'] < 5:  # Minimum 5€ par trade
                logger.info(f"💰 Position trop petite: {position['value']:.2f}€")
                return False
            
            # Affichage du trade
            logger.info(f"\n🚨 TRADE ULTRA-AGGRESSIF 🚨")
            logger.info(f"🎯 Symbole: {symbol}")
            logger.info(f"📊 Signal: {signal['signal']}")
            logger.info(f"💪 Confiance: {signal['confidence']:.1%}")
            logger.info(f"💰 Investissement: {position['value']:.2f}€")
            logger.info(f"📈 Quantité: {position['quantity']:.4f}")
            logger.info(f"🔥 Momentum 3min: {signal['momentum_3m']:.2%}")
            logger.info(f"🔊 Volume: {signal['volume_ratio']:.1f}x")
            logger.info(f"🛡️ Stop Loss: {position['stop_loss']:.6f}")
            logger.info(f"🎯 TP1 (+4%): {position['take_profit_1']:.6f}")
            logger.info(f"🎯 TP2 (+8%): {position['take_profit_2']:.6f}")
            
            # Sauvegarde pour tracking
            self.active_positions[symbol] = {
                'entry_price': signal['price'],
                'quantity': position['quantity'],
                'side': signal['signal'],
                'stop_loss': position['stop_loss'],
                'tp1': position['take_profit_1'],
                'tp2': position['take_profit_2'],
                'entry_time': datetime.now(),
                'invested': position['value'],
                'confidence': signal['confidence']
            }
            
            # Achat ou vente réel sur Alpaca (toujours exécuté)
            if signal['signal'] == 'BUY':
                try:
                    logger.info(f"🟢 Envoi d'un ordre d'achat réel sur Alpaca pour {symbol}...")
                    order = api.submit_order(
                        symbol=symbol,
                        qty=round(position['quantity'], 6),
                        side='buy',
                        type='market',
                        time_in_force='ioc'
                    )
                    logger.info(f"✅ Ordre d'achat exécuté: {order.id}")
                except Exception as e:
                    logger.error(f"❌ Erreur ordre d'achat: {e}")
                    pass
            elif signal['signal'] == 'SELL':
                try:
                    logger.info(f"🔴 Envoi d'un ordre de vente réel sur Alpaca pour {symbol}...")
                    order = api.submit_order(
                        symbol=symbol,
                        qty=round(position['quantity'], 6),
                        side='sell',
                        type='market',
                        time_in_force='ioc'
                    )
                    logger.info(f"✅ Ordre de vente exécuté: {order.id}")
                except Exception as e:
                    logger.error(f"❌ Erreur ordre de vente: {e}")
                    pass
            self.trades_today += 1
            # self.current_balance -= position['value']  # Simulation, inutile pour l'ordre réel
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution: {e}")
            return False
    
    def manage_positions_aggressively(self):
        """Gestion ultra-rapide des positions avec positions réelles du compte"""
        try:
            # Récupération des positions réelles via API
            api_positions = api.list_positions()
            
            for api_pos in api_positions:
                symbol = api_pos.symbol
                current_price = float(api_pos.current_price)
                entry_price = float(api_pos.avg_entry_price)
                qty = float(api_pos.qty)
                market_value = float(api_pos.market_value)
                
                # Calcul P&L réel
                if api_pos.side == 'long':
                    pnl_pct = (current_price - entry_price) / entry_price
                    side = 'BUY'
                    stop_loss = entry_price * 0.94
                    tp1 = entry_price * 1.04
                    tp2 = entry_price * 1.08
                else:
                    pnl_pct = (entry_price - current_price) / entry_price
                    side = 'SELL'
                    stop_loss = entry_price * 1.06
                    tp1 = entry_price * 0.96
                    tp2 = entry_price * 0.92
                pnl_dollar = market_value - (qty * entry_price)

                # Mise à jour ou création du tracking interne
                if symbol not in self.active_positions:
                    self.active_positions[symbol] = {
                        'entry_price': entry_price,
                        'quantity': qty,
                        'side': side,
                        'stop_loss': stop_loss,
                        'tp1': tp1,
                        'tp2': tp2,
                        'entry_time': datetime.now(),
                        'invested': abs(market_value),
                        'confidence': 0.7  # Valeur par défaut
                    }
                
                trade = self.active_positions[symbol]
                
                # Affichage du statut de la position
                logger.info(f"📊 {symbol}: {pnl_pct:+.2%} ({pnl_dollar:+.2f}$) | Prix: {current_price:.6f}")
                
                # Conditions de sortie basées sur les prix réels
                
                # Stop Loss
                if ((trade['side'] == 'BUY' and current_price <= trade['stop_loss']) or
                    (trade['side'] == 'SELL' and current_price >= trade['stop_loss'])):
                    
                    logger.info(f"🛑 STOP LOSS DÉCLENCHÉ: {symbol} | P&L: {pnl_pct:.2%} ({pnl_dollar:.2f}$)")
                    self.close_position_via_api(symbol)
                    
                # Take Profit 1 (sortie partielle)
                elif ((trade['side'] == 'BUY' and current_price >= trade['tp1']) or
                      (trade['side'] == 'SELL' and current_price <= trade['tp1'])) and 'tp1_hit' not in trade:
                    
                    logger.info(f"🎯 TP1 ATTEINT: {symbol} | P&L: {pnl_pct:.2%} ({pnl_dollar:.2f}$)")
                    # Vente de 50% de la position
                    partial_qty = qty * 0.5
                    try:
                        logger.info(f"🟠 Envoi d'un ordre de vente partielle (50%) sur Alpaca pour {symbol}...")
                        api.submit_order(
                            symbol=symbol,
                            qty=round(partial_qty, 6),
                            side='sell' if trade['side'] == 'BUY' else 'buy',
                            type='market',
                            time_in_force='ioc'
                        )
                        trade['tp1_hit'] = True
                        logger.info(f"✅ Vente partielle (50%) exécutée pour {symbol}")
                    except Exception as e:
                        logger.error(f"❌ Erreur vente partielle {symbol}: {e}")
                        
                # Take Profit 2 (sortie complète)
                elif ((trade['side'] == 'BUY' and current_price >= trade['tp2']) or
                      (trade['side'] == 'SELL' and current_price <= trade['tp2'])):
                    
                    logger.info(f"🎯🎯 TP2 ATTEINT: {symbol} | P&L: {pnl_pct:.2%} ({pnl_dollar:.2f}$)")
                    self.close_position_via_api(symbol)
                    
                # Trailing stop pour profits exceptionnels
                elif pnl_pct > 0.12:  # Si +12% de profit
                    new_stop = current_price * (0.95 if trade['side'] == 'BUY' else 1.05)
                    if ((trade['side'] == 'BUY' and new_stop > trade['stop_loss']) or
                        (trade['side'] == 'SELL' and new_stop < trade['stop_loss'])):
                        trade['stop_loss'] = new_stop
                        logger.info(f"📈 Trailing Stop ajusté pour {symbol}: {new_stop:.6f}")
                
        except Exception as e:
            logger.error(f"❌ Erreur gestion positions: {e}")
    
    def close_position_via_api(self, symbol):
        """Fermeture de position via API avec tracking"""
        try:
            # Fermeture via API
            api.close_position(symbol)
            logger.info(f"✅ Position fermée via API: {symbol}")
            
            # Nettoyage du tracking interne
            if symbol in self.active_positions:
                trade = self.active_positions[symbol]
                
                # Ajout à l'historique
                self.trade_history.append({
                    'symbol': symbol,
                    'entry_time': trade['entry_time'],
                    'exit_time': datetime.now(),
                    'confidence': trade.get('confidence', 0.5)
                })
                
                del self.active_positions[symbol]
                
        except Exception as e:
            logger.error(f"❌ Erreur fermeture position {symbol}: {e}")
    
    def check_daily_target(self):
        """Vérification de l'objectif quotidien basé sur le portfolio réel"""
        try:
            account_status = self.get_current_account_status()
            if not account_status:
                return False
                
            current_value = account_status['portfolio_value']
            daily_return_pct = account_status['total_pnl_pct'] / 100
            
            if daily_return_pct >= DAILY_TARGET:
                logger.info(f"🎉 OBJECTIF QUOTIDIEN ATTEINT! +{daily_return_pct:.1%} ({account_status['total_pnl']:+.2f}$)")
                logger.info("💤 Arrêt du trading pour aujourd'hui - Profits sécurisés!")
                return True
                
            # Vérification des étapes de croissance
            if current_value >= self.targets[self.current_target_index]:
                logger.info(f"🚀 ÉTAPE FRANCHIE: {self.targets[self.current_target_index]:.0f}$!")
                self.current_target_index = min(self.current_target_index + 1, len(self.targets) - 1)
                
            return False
        except Exception as e:
            logger.error(f"❌ Erreur vérification objectif: {e}")
            return False
    
    def print_status(self):
        """Affichage du status complet basé sur le compte réel"""
        try:
            account_status = self.get_current_account_status()
            if not account_status:
                return
                
            logger.info(f"\n💰 PORTFOLIO: {account_status['portfolio_value']:.2f}$ (Initial: {self.initial_budget:.2f}$)")
            logger.info(f"💳 Pouvoir d'achat: {account_status['buying_power']:.2f}$")
            logger.info(f"📈 P&L Total: {account_status['total_pnl']:+.2f}$ ({account_status['total_pnl_pct']:+.1f}%)")
            logger.info(f"🎯 Prochain objectif: {self.targets[self.current_target_index]:.0f}$")
            logger.info(f"📊 Trades aujourd'hui: {self.trades_today}/{self.max_trades_per_day}")
            logger.info(f"⚡ Positions actives: {account_status['positions_count']}")
            
            if self.trade_history:
                logger.info(f"📊 Total trades exécutés: {len(self.trade_history)}")
                
        except Exception as e:
            logger.error(f"❌ Erreur affichage status: {e}")
    
    def run_aggressive_scalping(self):
        """Boucle principale de scalping agressif"""
        logger.info(f"\n🔥 DÉMARRAGE SCALPING ULTRA-AGRESSIF - Capital Papier: {self.initial_budget:.2f}$")
        logger.info(f"🎯 Objectif quotidien: +{DAILY_TARGET:.0%} ({DAILY_TARGET * self.initial_budget:.0f}$)")
        logger.info(f"💰 Risque par trade: {RISK_PER_TRADE:.0%} (~{RISK_PER_TRADE * self.initial_budget:.0f}$ par position)")
        logger.info(f"💳 Pouvoir d'achat initial: {self.buying_power:.2f}$")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                
                # Vérification objectif quotidien
                if self.check_daily_target():
                    break
                
                # Status périodique
                if cycle_count % 10 == 0:
                    self.print_status()
                
                # 1. Trouver les cryptos les plus chaudes
                opportunities = self.get_ultra_volatile_cryptos()
                
                if not opportunities:
                    time.sleep(30)
                    continue
                
                # 2. Analyser les 5 meilleures opportunités (focus qualité)
                for symbol, data in opportunities[:5]:
                    # Récupération des positions actuelles via API
                    current_positions = len(api.list_positions())
                    if current_positions >= 4:  # Max 4 positions
                        break
                        
                    # Vérifier si on a déjà une position sur ce symbole
                    existing_position = False
                    for pos in api.list_positions():
                        if pos.symbol == symbol:
                            existing_position = True
                            break
                    
                    if existing_position:
                        continue
                    
                    signal = self.detect_breakout_signal(symbol)
                    
                    if signal and signal['signal'] in ['BUY', 'SELL'] and signal['confidence'] > 0.4:  # Seuil plus bas
                        position = self.calculate_aggressive_position(signal)
                        
                        if position and position['value'] >= 20:  # Minimum 20$ pour tests réalistes
                            logger.info(f"🎯 Signal détecté: {symbol} - Confiance: {signal['confidence']:.1%}")
                            self.execute_aggressive_trade(signal, position)
                            time.sleep(3)  # Pause entre trades
                
                # 3. Gestion ultra-rapide des positions
                self.manage_positions_aggressively()
                
                # Protection du capital basée sur le portfolio réel
                account_status = self.get_current_account_status()
                if account_status:
                    total_return_pct = account_status['total_pnl_pct'] / 100
                    if total_return_pct < -0.3:  # -30% = arrêt
                        logger.info(f"🛑 PROTECTION CAPITALE: Arrêt après {total_return_pct:.1%}")
                        break
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Arrêt manuel du bot")
                break
            except Exception as e:
                logger.error(f"⚠️ Erreur cycle: {e}")
            
                # Cycle plus intelligent - ajustement selon activité
                if len(self.active_positions) > 0:
                    time.sleep(10)  # Plus rapide si positions actives
                else:
                    time.sleep(20)  # Plus lent si recherche d'opportunités
        
        # Rapport final
        self.print_final_report()
    
    def print_final_report(self):
        """Rapport final de performance basé sur le compte réel"""
        try:
            account_status = self.get_current_account_status()
            if not account_status:
                return
                
            final_value = account_status['portfolio_value']
            total_pnl = account_status['total_pnl']
            total_return_pct = account_status['total_pnl_pct']
            
            logger.info(f"\n{'='*50}")
            logger.info(f"📊 RAPPORT FINAL - SCALPING AGRESSIF")
            logger.info(f"{'='*50}")
            logger.info(f"💰 Portfolio initial: {self.initial_budget:.2f}$")
            logger.info(f"💰 Portfolio final: {final_value:.2f}$")
            logger.info(f"📈 P&L Total: {total_pnl:+.2f}$ ({total_return_pct:+.1f}%)")
            logger.info(f"📊 Nombre total de trades: {len(self.trade_history)}")
            
            if total_return_pct > 0:
                logger.info(f"🎉 MISSION ACCOMPLIE! Objectif de croissance atteint!")
            else:
                logger.info(f"📚 Expérience d'apprentissage - Ajustements nécessaires")
                
            # Positions encore ouvertes
            open_positions = api.list_positions()
            if open_positions:
                logger.info(f"⚠️ Positions encore ouvertes: {len(open_positions)}")
                for pos in open_positions:
                    pnl = float(pos.unrealized_pl)
                    logger.info(f"   📊 {pos.symbol}: {pnl:+.2f}$ ({float(pos.unrealized_plpc)*100:+.1f}%)")
                    
        except Exception as e:
            logger.error(f"❌ Erreur rapport final: {e}")

# Lancement du scalper agressif
if __name__ == '__main__':
    scalper = AggressiveScalper()
    scalper.run_aggressive_scalping()