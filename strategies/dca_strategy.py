"""
Stratégie DCA (Dollar Cost Averaging) intelligente basée sur le RSI
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from pathlib import Path

import config
from utils.binance_client import get_binance_client
from utils.indicators import calculate_rsi, extract_prices_from_klines, get_buy_signal_strength
from utils.notifications import get_notification_manager

logger = logging.getLogger(__name__)


class DCAStrategy:
    """Stratégie DCA intelligente"""

    def __init__(self):
        self.enabled = config.DCA_SETTINGS['enabled']
        self.client = get_binance_client()
        self.notif = get_notification_manager()

        # État de la stratégie
        self.daily_spent = 0.0
        self.last_buy_date = None
        self.trades_history = []

        # Charger l'historique si existe
        self._load_history()

    def _load_history(self):
        """Charge l'historique des trades DCA"""
        try:
            if config.TRADES_FILE.exists():
                with open(config.TRADES_FILE, 'r') as f:
                    data = json.load(f)
                    self.trades_history = data.get('dca_trades', [])

                # Calculer le montant dépensé aujourd'hui
                today = datetime.now().date()
                self.daily_spent = sum(
                    trade['amount']
                    for trade in self.trades_history
                    if datetime.fromisoformat(trade['timestamp']).date() == today
                )

                if self.daily_spent > 0:
                    self.last_buy_date = today

                logger.info(f"📊 Historique DCA chargé: {len(self.trades_history)} trades, {self.daily_spent}€ dépensés aujourd'hui")

        except Exception as e:
            logger.error(f"❌ Erreur chargement historique DCA: {e}")
            self.trades_history = []

    def _save_history(self):
        """Sauvegarde l'historique des trades"""
        try:
            # Charger les données existantes
            data = {}
            if config.TRADES_FILE.exists():
                with open(config.TRADES_FILE, 'r') as f:
                    data = json.load(f)

            # Mettre à jour les trades DCA
            data['dca_trades'] = self.trades_history

            # Sauvegarder
            with open(config.TRADES_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("💾 Historique DCA sauvegardé")

        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde historique DCA: {e}")

    def _reset_daily_counter(self):
        """Reset le compteur quotidien si on est un nouveau jour"""
        today = datetime.now().date()

        if self.last_buy_date and self.last_buy_date != today:
            logger.info(f"📅 Nouveau jour - Reset du compteur DCA (était: {self.daily_spent}€)")
            self.daily_spent = 0.0
            self.last_buy_date = None

    def _get_buy_amount(self, rsi: float) -> float:
        """
        Détermine le montant à acheter basé sur le RSI

        Args:
            rsi: Valeur du RSI

        Returns:
            Montant en € à acheter (0 si pas d'achat)
        """
        # Parcourir les niveaux RSI du plus bas au plus haut
        for rsi_threshold in sorted(config.DCA_SETTINGS['rsi_levels'].keys()):
            if rsi < rsi_threshold:
                return config.DCA_SETTINGS['rsi_levels'][rsi_threshold]

        # Si RSI trop élevé, pas d'achat
        return 0.0

    async def _execute_buy(
        self,
        coin: str,
        amount: float,
        current_price: float,
        rsi: float
    ) -> bool:
        """
        Exécute un achat DCA

        Args:
            coin: Symbole de la crypto (BTC, ETH)
            amount: Montant en €
            current_price: Prix actuel
            rsi: Valeur du RSI

        Returns:
            True si succès, False sinon
        """
        try:
            symbol = f"{coin}{config.BINANCE_CONFIG['quote_currency']}"

            logger.info(f"💰 Exécution DCA: {amount}€ de {coin} @ ${current_price:,.2f} (RSI: {rsi:.1f})")

            # Placer l'ordre
            order = self.client.place_buy_order(symbol, amount)

            if not order:
                await self.notif.send_error(f"Échec ordre DCA pour {coin}")
                return False

            # Enregistrer le trade
            trade = {
                'timestamp': datetime.now().isoformat(),
                'coin': coin,
                'symbol': symbol,
                'amount': amount,
                'price': current_price,
                'quantity': order.get('executedQty', amount / current_price),
                'rsi': rsi,
                'order_id': order.get('orderId'),
                'dry_run': config.TRADING_MODE == 'dry_run'
            }

            self.trades_history.append(trade)
            self._save_history()

            # Mettre à jour les compteurs
            self.daily_spent += amount
            self.last_buy_date = datetime.now().date()

            # Notification
            await self.notif.send_dca_alert(
                coin=coin,
                rsi=rsi,
                amount=amount,
                price=current_price,
                executed=True
            )

            logger.info(f"✅ DCA exécuté avec succès: {trade['quantity']:.8f} {coin}")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur exécution DCA pour {coin}: {e}")
            await self.notif.send_error(f"Erreur DCA {coin}: {str(e)}")
            return False

    async def _check_coin(self, coin: str, allocation: float) -> Optional[Dict]:
        """
        Vérifie une crypto et détermine s'il faut acheter

        Args:
            coin: Symbole de la crypto (BTC, ETH)
            allocation: Pourcentage d'allocation (0.0 - 1.0)

        Returns:
            Dict avec les infos si achat recommandé, None sinon
        """
        try:
            symbol = f"{coin}{config.BINANCE_CONFIG['quote_currency']}"

            # Récupérer les données historiques
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=config.DCA_SETTINGS['timeframe'],
                limit=100
            )

            if not klines:
                logger.warning(f"⚠️ Pas de données pour {coin}")
                return None

            # Extraire les prix de clôture
            prices_data = extract_prices_from_klines(klines)
            close_prices = prices_data['close']

            if not close_prices:
                logger.warning(f"⚠️ Pas de prix de clôture pour {coin}")
                return None

            # Calculer le RSI
            rsi = calculate_rsi(
                close_prices,
                period=config.DCA_SETTINGS['rsi_period']
            )

            current_price = close_prices[-1]

            # Déterminer le montant d'achat basé sur le RSI
            buy_amount = self._get_buy_amount(rsi)

            # Ajuster selon l'allocation
            if buy_amount > 0:
                buy_amount = buy_amount * allocation

            logger.info(f"📊 {coin}: Prix=${current_price:,.2f}, RSI={rsi:.1f}, Signal={get_buy_signal_strength(rsi)}")

            # Retourner les infos si achat recommandé
            if buy_amount >= config.DCA_SETTINGS['min_trade_amount']:
                return {
                    'coin': coin,
                    'symbol': symbol,
                    'price': current_price,
                    'rsi': rsi,
                    'amount': buy_amount,
                    'signal_strength': get_buy_signal_strength(rsi)
                }

            return None

        except Exception as e:
            logger.error(f"❌ Erreur vérification {coin}: {e}")
            return None

    async def run_check(self):
        """Exécute une vérification DCA"""
        if not self.enabled:
            logger.debug("⏸️ Stratégie DCA désactivée")
            return

        try:
            logger.info("🔍 === Début vérification DCA ===")

            # Reset le compteur si nouveau jour
            self._reset_daily_counter()

            # Vérifier si on a déjà atteint la limite quotidienne
            if self.daily_spent >= config.DCA_SETTINGS['max_daily_buy']:
                logger.info(f"⏸️ Limite quotidienne atteinte ({self.daily_spent}€/{config.DCA_SETTINGS['max_daily_buy']}€)")
                return

            # Budget restant pour aujourd'hui
            remaining_budget = config.DCA_SETTINGS['max_daily_buy'] - self.daily_spent

            # Vérifier chaque coin
            opportunities = []

            for coin, allocation in config.DCA_SETTINGS['coins'].items():
                opportunity = await self._check_coin(coin, allocation)
                if opportunity:
                    opportunities.append(opportunity)

            # Trier par force du signal (RSI le plus bas en premier)
            opportunities.sort(key=lambda x: x['rsi'])

            if not opportunities:
                logger.info("✅ Aucune opportunité DCA détectée")
                return

            # Traiter les opportunités
            for opp in opportunities:
                # Vérifier le budget restant
                if remaining_budget < config.DCA_SETTINGS['min_trade_amount']:
                    logger.info(f"⏸️ Budget insuffisant pour continuer ({remaining_budget:.2f}€)")
                    break

                # Ajuster le montant si nécessaire
                buy_amount = min(opp['amount'], remaining_budget)

                logger.info(
                    f"🎯 Opportunité DCA: {opp['coin']} - "
                    f"RSI={opp['rsi']:.1f}, "
                    f"Prix=${opp['price']:,.2f}, "
                    f"Montant={buy_amount:.2f}€"
                )

                # Envoyer notification d'opportunité
                await self.notif.send_dca_alert(
                    coin=opp['coin'],
                    rsi=opp['rsi'],
                    amount=buy_amount,
                    price=opp['price'],
                    executed=False
                )

                # Exécuter l'achat
                success = await self._execute_buy(
                    coin=opp['coin'],
                    amount=buy_amount,
                    current_price=opp['price'],
                    rsi=opp['rsi']
                )

                if success:
                    remaining_budget -= buy_amount
                    logger.info(f"💰 Budget restant: {remaining_budget:.2f}€")

                    # Respecter la limite: 1 achat max par jour
                    logger.info("⏸️ 1 achat par jour effectué, arrêt de la stratégie DCA pour aujourd'hui")
                    break

                # Petite pause entre les ordres
                await asyncio.sleep(1)

            logger.info("🔍 === Fin vérification DCA ===\n")

        except Exception as e:
            logger.error(f"❌ Erreur dans run_check DCA: {e}")
            await self.notif.send_error(f"Erreur DCA: {str(e)}")

    async def start(self):
        """Démarre la stratégie DCA en boucle"""
        logger.info("🚀 Démarrage stratégie DCA")

        while self.enabled:
            try:
                await self.run_check()

                # Attendre l'intervalle configuré
                interval = config.DCA_SETTINGS['check_interval']
                logger.info(f"⏰ Prochaine vérification DCA dans {interval / 3600:.1f}h")
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("🛑 Stratégie DCA arrêtée")
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans boucle DCA: {e}")
                await asyncio.sleep(60)  # Attendre 1 minute avant de réessayer

    def get_stats(self) -> Dict:
        """
        Retourne les statistiques de la stratégie

        Returns:
            Dict avec les stats
        """
        today = datetime.now().date()
        today_trades = [
            t for t in self.trades_history
            if datetime.fromisoformat(t['timestamp']).date() == today
        ]

        total_invested = sum(t['amount'] for t in self.trades_history)
        today_invested = sum(t['amount'] for t in today_trades)

        return {
            'total_trades': len(self.trades_history),
            'today_trades': len(today_trades),
            'total_invested': total_invested,
            'today_invested': today_invested,
            'daily_budget': config.DCA_SETTINGS['max_daily_buy'],
            'remaining_today': config.DCA_SETTINGS['max_daily_buy'] - self.daily_spent,
            'enabled': self.enabled
        }
