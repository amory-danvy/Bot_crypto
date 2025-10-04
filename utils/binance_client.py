"""
Client Binance avec gestion d'erreurs, retry et websocket
"""
import asyncio
import logging
import time
from typing import Dict, Optional, List, Union
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from binance.websockets import BinanceSocketManager
import config

logger = logging.getLogger(__name__)


class BinanceClient:
    """Wrapper pour l'API Binance avec gestion avancée"""

    def __init__(self):
        self.mode = config.TRADING_MODE
        self.client = None
        self.socket_manager = None
        self._price_cache = {}
        self._last_request_time = 0
        self._request_count = 0

        # Initialiser le client selon le mode
        self._initialize_client()

    def _initialize_client(self):
        """Initialise le client Binance selon le mode de trading"""
        try:
            if self.mode == 'dry_run':
                logger.info("🔧 Mode DRY RUN - Aucune connexion réelle à Binance")
                # En dry run, on utilise quand même le client pour les prix
                self.client = Client("", "", testnet=False)

            elif self.mode == 'testnet':
                logger.info("🧪 Mode TESTNET - Connexion au Binance Testnet")
                self.client = Client(
                    config.BINANCE_TESTNET_API_KEY,
                    config.BINANCE_TESTNET_API_SECRET,
                    testnet=True
                )

            elif self.mode == 'live':
                logger.info("🚀 Mode LIVE - Connexion à Binance en production")
                self.client = Client(
                    config.BINANCE_API_KEY,
                    config.BINANCE_API_SECRET
                )

            # Initialiser le websocket si activé
            if config.BINANCE_CONFIG['use_websocket'] and self.client:
                self.socket_manager = BinanceSocketManager(self.client)

            logger.info("✅ Client Binance initialisé avec succès")

        except Exception as e:
            logger.error(f"❌ Erreur initialisation client Binance: {e}")
            raise

    def _rate_limit_check(self):
        """Vérifie et applique le rate limiting"""
        current_time = time.time()

        # Reset le compteur chaque minute
        if current_time - self._last_request_time > 60:
            self._request_count = 0
            self._last_request_time = current_time

        # Vérifier la limite
        if self._request_count >= config.BINANCE_CONFIG['rate_limit']:
            sleep_time = 60 - (current_time - self._last_request_time)
            logger.warning(f"⚠️ Rate limit atteint, pause de {sleep_time:.1f}s")
            time.sleep(sleep_time)
            self._request_count = 0
            self._last_request_time = time.time()

        self._request_count += 1

    def _retry_request(self, func, *args, **kwargs):
        """Exécute une requête avec retry automatique"""
        max_retries = config.BINANCE_CONFIG['max_retries']
        retry_delay = config.BINANCE_CONFIG['retry_delay']

        for attempt in range(max_retries):
            try:
                self._rate_limit_check()
                return func(*args, **kwargs)

            except BinanceAPIException as e:
                logger.error(f"❌ Binance API Error (tentative {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise

            except BinanceRequestException as e:
                logger.error(f"❌ Binance Request Error (tentative {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise

            except Exception as e:
                logger.error(f"❌ Erreur inattendue: {e}")
                raise

    def get_balance(self, asset: str = None) -> Union[Dict, float]:
        """
        Récupère le solde
        Args:
            asset: Symbole de la crypto (ex: 'USDT', 'BTC'). Si None, retourne tout
        Returns:
            Dict avec tous les soldes ou float pour un asset spécifique
        """
        if self.mode == 'dry_run':
            # En dry run, simuler les balances depuis le capital alloué
            balances = {
                'USDT': float(config.CAPITAL_ALLOCATION['total']),
                'BTC': 0.0,
                'ETH': 0.0
            }
            if asset:
                return balances.get(asset, 0.0)
            return balances

        try:
            account = self._retry_request(self.client.get_account)
            balances = {
                b['asset']: float(b['free'])
                for b in account['balances']
                if float(b['free']) > 0
            }

            if asset:
                return balances.get(asset, 0.0)
            return balances

        except Exception as e:
            logger.error(f"❌ Erreur récupération balance: {e}")
            return 0.0 if asset else {}

    def get_price(self, symbol: str) -> float:
        """
        Récupère le prix actuel d'un symbole
        Args:
            symbol: Paire de trading (ex: 'BTCUSDT')
        Returns:
            Prix actuel en float
        """
        try:
            # Utiliser le cache si disponible et récent (< 5 secondes)
            if symbol in self._price_cache:
                cached_price, cached_time = self._price_cache[symbol]
                if time.time() - cached_time < 5:
                    return cached_price

            # Récupérer le prix
            ticker = self._retry_request(self.client.get_symbol_ticker, symbol=symbol)
            price = float(ticker['price'])

            # Mettre en cache
            self._price_cache[symbol] = (price, time.time())

            return price

        except Exception as e:
            logger.error(f"❌ Erreur récupération prix {symbol}: {e}")
            return 0.0

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100
    ) -> List[List]:
        """
        Récupère les données historiques (klines/candlesticks)
        Args:
            symbol: Paire de trading (ex: 'BTCUSDT')
            interval: Timeframe (ex: '1h', '4h', '1d')
            limit: Nombre de bougies à récupérer
        Returns:
            Liste de klines
        """
        try:
            klines = self._retry_request(
                self.client.get_klines,
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return klines

        except Exception as e:
            logger.error(f"❌ Erreur récupération klines {symbol}: {e}")
            return []

    def place_buy_order(
        self,
        symbol: str,
        amount_usd: float,
        order_type: str = 'MARKET'
    ) -> Optional[Dict]:
        """
        Place un ordre d'achat
        Args:
            symbol: Paire de trading (ex: 'BTCUSDT')
            amount_usd: Montant en USD/USDT
            order_type: Type d'ordre ('MARKET' ou 'LIMIT')
        Returns:
            Dictionnaire avec les détails de l'ordre
        """
        if self.mode == 'dry_run':
            logger.info(f"🧪 [DRY RUN] Achat simulé: {amount_usd}€ de {symbol}")
            price = self.get_price(symbol)
            quantity = amount_usd / price
            return {
                'symbol': symbol,
                'orderId': f'DRY_{int(time.time())}',
                'price': price,
                'origQty': quantity,
                'executedQty': quantity,
                'status': 'FILLED',
                'type': order_type,
                'side': 'BUY',
                'dry_run': True
            }

        try:
            # Calculer la quantité à acheter
            price = self.get_price(symbol)
            quantity = amount_usd / price

            # Arrondir selon la précision
            quantity = round(quantity, config.BINANCE_CONFIG['quantity_precision'])

            logger.info(f"📈 Placement ordre ACHAT: {quantity} {symbol} (~{amount_usd}€)")

            # Placer l'ordre
            if order_type == 'MARKET':
                order = self._retry_request(
                    self.client.order_market_buy,
                    symbol=symbol,
                    quantity=quantity
                )
            else:
                order = self._retry_request(
                    self.client.create_order,
                    symbol=symbol,
                    side='BUY',
                    type=order_type,
                    quantity=quantity
                )

            logger.info(f"✅ Ordre placé: {order['orderId']}")
            return order

        except Exception as e:
            logger.error(f"❌ Erreur placement ordre achat {symbol}: {e}")
            return None

    def place_sell_order(
        self,
        symbol: str,
        quantity: float = None,
        order_type: str = 'MARKET'
    ) -> Optional[Dict]:
        """
        Place un ordre de vente
        Args:
            symbol: Paire de trading (ex: 'BTCUSDT')
            quantity: Quantité à vendre (si None, vend tout)
            order_type: Type d'ordre ('MARKET' ou 'LIMIT')
        Returns:
            Dictionnaire avec les détails de l'ordre
        """
        if self.mode == 'dry_run':
            logger.info(f"🧪 [DRY RUN] Vente simulée: {quantity} {symbol}")
            price = self.get_price(symbol)
            return {
                'symbol': symbol,
                'orderId': f'DRY_{int(time.time())}',
                'price': price,
                'origQty': quantity,
                'executedQty': quantity,
                'status': 'FILLED',
                'type': order_type,
                'side': 'SELL',
                'dry_run': True
            }

        try:
            # Si quantity est None, récupérer le solde
            if quantity is None:
                asset = symbol.replace(config.BINANCE_CONFIG['quote_currency'], '')
                quantity = self.get_balance(asset)

            # Arrondir selon la précision
            quantity = round(quantity, config.BINANCE_CONFIG['quantity_precision'])

            logger.info(f"📉 Placement ordre VENTE: {quantity} {symbol}")

            # Placer l'ordre
            if order_type == 'MARKET':
                order = self._retry_request(
                    self.client.order_market_sell,
                    symbol=symbol,
                    quantity=quantity
                )
            else:
                order = self._retry_request(
                    self.client.create_order,
                    symbol=symbol,
                    side='SELL',
                    type=order_type,
                    quantity=quantity
                )

            logger.info(f"✅ Ordre placé: {order['orderId']}")
            return order

        except Exception as e:
            logger.error(f"❌ Erreur placement ordre vente {symbol}: {e}")
            return None

    def get_order_status(self, symbol: str, order_id: str) -> Optional[Dict]:
        """
        Récupère le statut d'un ordre
        Args:
            symbol: Paire de trading
            order_id: ID de l'ordre
        Returns:
            Dictionnaire avec le statut de l'ordre
        """
        if self.mode == 'dry_run':
            return {
                'orderId': order_id,
                'status': 'FILLED',
                'dry_run': True
            }

        try:
            order = self._retry_request(
                self.client.get_order,
                symbol=symbol,
                orderId=order_id
            )
            return order

        except Exception as e:
            logger.error(f"❌ Erreur récupération statut ordre {order_id}: {e}")
            return None

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Annule un ordre
        Args:
            symbol: Paire de trading
            order_id: ID de l'ordre
        Returns:
            True si succès, False sinon
        """
        if self.mode == 'dry_run':
            logger.info(f"🧪 [DRY RUN] Annulation simulée de l'ordre {order_id}")
            return True

        try:
            self._retry_request(
                self.client.cancel_order,
                symbol=symbol,
                orderId=order_id
            )
            logger.info(f"✅ Ordre {order_id} annulé")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur annulation ordre {order_id}: {e}")
            return False

    async def start_price_stream(self, symbols: List[str], callback):
        """
        Démarre un flux websocket pour les prix en temps réel
        Args:
            symbols: Liste des symboles à surveiller
            callback: Fonction à appeler quand un prix est mis à jour
        """
        if not self.socket_manager:
            logger.warning("⚠️ Websocket non activé")
            return

        try:
            # Créer une connexion multiplex pour tous les symboles
            conn_key = self.socket_manager.start_multiplex_socket(
                [s.lower() + '@ticker' for s in symbols],
                callback
            )

            # Démarrer le socket manager
            self.socket_manager.start()
            logger.info(f"✅ Websocket démarré pour {len(symbols)} symboles")

        except Exception as e:
            logger.error(f"❌ Erreur démarrage websocket: {e}")

    def close(self):
        """Ferme les connexions"""
        if self.socket_manager:
            self.socket_manager.close()
        logger.info("🔌 Connexions Binance fermées")


# Instance globale (singleton)
_binance_client = None


def get_binance_client() -> BinanceClient:
    """Récupère l'instance unique du client Binance"""
    global _binance_client
    if _binance_client is None:
        _binance_client = BinanceClient()
    return _binance_client
