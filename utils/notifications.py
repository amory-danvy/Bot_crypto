"""
Système de notifications via Discord webhook
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
import aiohttp
import config

logger = logging.getLogger(__name__)


class NotificationManager:
    """Gestionnaire de notifications Discord"""

    def __init__(self):
        self.enabled = config.ALERTS['discord_enabled']
        self.webhook_url = config.DISCORD_WEBHOOK_URL

        # Vérifier la configuration
        if self.enabled:
            self._validate_config()

    def _validate_config(self):
        """Valide la configuration Discord"""
        if not self.webhook_url or self.webhook_url == 'your_discord_webhook_url_here':
            logger.warning("⚠️ DISCORD_WEBHOOK_URL manquant, notifications désactivées")
            self.enabled = False
            return

        logger.info("✅ Discord webhook configuré")

    def _format_message(self, level: str, message: str) -> dict:
        """
        Formate un message pour Discord

        Args:
            level: Niveau du message (INFO, OPPORTUNITY, TRADE, etc.)
            message: Contenu du message

        Returns:
            Payload Discord formaté
        """
        emoji = config.ALERTS['levels'].get(level, '📌')
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Couleurs selon le niveau
        colors = {
            'INFO': 0x3498db,      # Bleu
            'OPPORTUNITY': 0x9b59b6,  # Violet
            'TRADE': 0x2ecc71,     # Vert
            'WARNING': 0xf39c12,   # Orange
            'ERROR': 0xe74c3c,     # Rouge
            'PROFIT': 0x27ae60,    # Vert foncé
            'LOSS': 0xc0392b       # Rouge foncé
        }

        color = colors.get(level, 0x95a5a6)

        # Créer l'embed Discord
        embed = {
            "title": f"{emoji} {level}",
            "description": message,
            "color": color,
            "footer": {
                "text": f"Bot Trading • {timestamp}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return {"embeds": [embed]}

    async def send_message(self, level: str, message: str):
        """
        Envoie un message Discord

        Args:
            level: Niveau du message
            message: Contenu du message
        """
        # Vérifier si on doit envoyer en dry_run
        if config.TRADING_MODE == 'dry_run' and not config.ALERTS['alert_in_dry_run']:
            logger.info(f"[DRY RUN] Message supprimé: {level} - {message}")
            return

        # Si désactivé, juste logger
        if not self.enabled:
            emoji = config.ALERTS['levels'].get(level, '📌')
            logger.info(f"[NO DISCORD] {emoji} {level}: {message}")
            return

        try:
            payload = self._format_message(level, message)

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.debug(f"✅ Message Discord envoyé: {level}")
                    else:
                        logger.error(f"❌ Erreur Discord: Status {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"❌ Erreur connexion Discord: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur inattendue envoi Discord: {e}")

    async def send_info(self, message: str):
        """Envoie un message d'information"""
        await self.send_message('INFO', message)

    async def send_opportunity(self, message: str):
        """Envoie une alerte d'opportunité"""
        await self.send_message('OPPORTUNITY', message)

    async def send_trade(self, message: str):
        """Envoie une notification de trade"""
        await self.send_message('TRADE', message)

    async def send_warning(self, message: str):
        """Envoie un avertissement"""
        await self.send_message('WARNING', message)

    async def send_error(self, message: str):
        """Envoie une notification d'erreur"""
        await self.send_message('ERROR', message)

    async def send_profit(self, message: str):
        """Envoie une notification de profit"""
        await self.send_message('PROFIT', message)

    async def send_loss(self, message: str):
        """Envoie une notification de perte"""
        await self.send_message('LOSS', message)

    async def send_dca_alert(
        self,
        coin: str,
        rsi: float,
        amount: float,
        price: float,
        executed: bool = False
    ):
        """
        Envoie une alerte DCA formatée

        Args:
            coin: Symbole de la crypto
            rsi: Valeur du RSI
            amount: Montant de l'achat en €
            price: Prix d'achat
            executed: Si l'ordre a été exécuté
        """
        if executed:
            message = (
                f"**DCA EXECUTED**\n"
                f"Coin: {coin}\n"
                f"Amount: {amount}€\n"
                f"Price: ${price:,.2f}\n"
                f"RSI: {rsi:.1f}"
            )
            await self.send_trade(message)
        else:
            message = (
                f"**DCA OPPORTUNITY**\n"
                f"Coin: {coin}\n"
                f"RSI: {rsi:.1f} (oversold)\n"
                f"Suggested amount: {amount}€\n"
                f"Current price: ${price:,.2f}"
            )
            await self.send_opportunity(message)

    async def send_snipe_alert(
        self,
        token: str,
        listing_time: str,
        amount: float,
        status: str = 'detected'
    ):
        """
        Envoie une alerte de snipe

        Args:
            token: Token à sniper
            listing_time: Heure du listing
            amount: Montant alloué
            status: 'detected', 'preparing', 'executed', 'failed'
        """
        if status == 'detected':
            message = (
                f"**NEW LISTING DETECTED**\n"
                f"Token: {token}\n"
                f"Listing time: {listing_time}\n"
                f"Allocated: {amount}€"
            )
            await self.send_opportunity(message)

        elif status == 'preparing':
            message = f"**PREPARING SNIPE**\nToken: {token}\nReady to execute..."
            await self.send_info(message)

        elif status == 'executed':
            message = f"**SNIPED!**\nToken: {token}\nAmount: {amount}€"
            await self.send_trade(message)

        elif status == 'failed':
            message = f"**SNIPE FAILED**\nToken: {token}\nReason: Order not filled"
            await self.send_error(message)

    async def send_scanner_alert(
        self,
        alert_type: str,
        coin: str,
        details: dict
    ):
        """
        Envoie une alerte du scanner

        Args:
            alert_type: Type d'alerte ('volume', 'rsi', 'arbitrage', etc.)
            coin: Symbole de la crypto
            details: Détails supplémentaires
        """
        if alert_type == 'volume':
            message = (
                f"**VOLUME ANOMALY**\n"
                f"Coin: {coin}\n"
                f"Volume: {details.get('volume_ratio', 0):.1f}x average\n"
                f"Price: ${details.get('price', 0):,.2f}"
            )
            await self.send_opportunity(message)

        elif alert_type == 'rsi':
            message = (
                f"**EXTREME RSI**\n"
                f"Coin: {coin}\n"
                f"RSI: {details.get('rsi', 0):.1f}\n"
                f"Price: ${details.get('price', 0):,.2f}"
            )
            await self.send_opportunity(message)

        elif alert_type == 'arbitrage':
            message = (
                f"**ARBITRAGE OPPORTUNITY**\n"
                f"Coin: {coin}\n"
                f"Price difference: {details.get('diff_pct', 0):.2f}%\n"
                f"Exchange A: ${details.get('price_a', 0):,.2f}\n"
                f"Exchange B: ${details.get('price_b', 0):,.2f}"
            )
            await self.send_opportunity(message)

    async def send_daily_report(self, stats: dict):
        """
        Envoie le rapport quotidien

        Args:
            stats: Statistiques de la journée
        """
        pnl = stats.get('pnl', 0)
        pnl_emoji = '💰' if pnl >= 0 else '📉'

        message = (
            f"**📊 DAILY REPORT**\n"
            f"{'='*30}\n"
            f"Capital: {stats.get('capital', 0):.2f}€\n"
            f"P&L: {pnl_emoji} {pnl:+.2f}€ ({stats.get('pnl_pct', 0):+.1f}%)\n"
            f"Trades today: {stats.get('trades_count', 0)}\n"
            f"Win rate: {stats.get('win_rate', 0):.1f}%\n"
            f"\n"
            f"**Strategies:**\n"
            f"DCA: {stats.get('dca_trades', 0)} trades\n"
            f"Sniper: {stats.get('sniper_trades', 0)} trades\n"
            f"\n"
            f"**Top performers:**\n"
        )

        # Ajouter top 3 performers
        top_performers = stats.get('top_performers', [])
        for i, perf in enumerate(top_performers[:3], 1):
            message += f"{i}. {perf['coin']}: {perf['pnl']:+.2f}€\n"

        await self.send_info(message)

    async def send_startup_message(self):
        """Envoie un message au démarrage du bot"""
        mode_emoji = {
            'dry_run': '🧪',
            'testnet': '🧪',
            'live': '🚀'
        }

        emoji = mode_emoji.get(config.TRADING_MODE, '🤖')

        message = (
            f"**{emoji} BOT STARTED**\n"
            f"Mode: {config.TRADING_MODE.upper()}\n"
            f"Capital: {config.CAPITAL_ALLOCATION['total']}€\n"
            f"\n"
            f"**Active strategies:**\n"
            f"DCA: {'✅' if config.DCA_SETTINGS['enabled'] else '❌'}\n"
            f"Sniper: {'✅' if config.SNIPER_SETTINGS['enabled'] else '❌'}\n"
            f"Scanner: {'✅' if config.SCANNER_SETTINGS['enabled'] else '❌'}\n"
            f"\n"
            f"🟢 All systems operational"
        )

        await self.send_info(message)

    async def send_shutdown_message(self):
        """Envoie un message à l'arrêt du bot"""
        message = "**🔴 BOT STOPPED**\nAll systems shutting down gracefully..."
        await self.send_warning(message)

    async def test_connection(self) -> bool:
        """
        Teste la connexion Discord

        Returns:
            True si connexion OK, False sinon
        """
        if not self.enabled:
            logger.warning("⚠️ Discord non activé")
            return False

        try:
            await self.send_info("✅ Test de connexion Discord réussi!")
            logger.info("✅ Test Discord réussi")
            return True

        except Exception as e:
            logger.error(f"❌ Test Discord échoué: {e}")
            return False


# Instance globale (singleton)
_notification_manager = None


def get_notification_manager() -> NotificationManager:
    """Récupère l'instance unique du gestionnaire de notifications"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager


# Fonctions helper pour appels synchrones (si nécessaire)
def notify_sync(level: str, message: str):
    """Envoie une notification de manière synchrone"""
    notif = get_notification_manager()
    asyncio.create_task(notif.send_message(level, message))
