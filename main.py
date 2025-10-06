#!/usr/bin/env python3
"""
Bot de Trading Crypto Hybride
Point d'entrée principal
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from logging.config import dictConfig

import config
from strategies.dca_strategy import DCAStrategy
from utils.binance_client import get_binance_client
from utils.notifications import get_notification_manager

# Configuration du logging
dictConfig(config.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class CryptoTradingBot:
    """Bot de trading principal"""

    def __init__(self):
        self.running = False
        self.tasks = []

        # Initialiser les composants
        self.client = None
        self.notif = None
        self.dca_strategy = None

    async def initialize(self):
        """Initialise tous les composants du bot"""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("🤖 INITIALISATION DU BOT DE TRADING CRYPTO")
            logger.info("=" * 60)

            # Valider la configuration
            errors = config.validate_config()
            if errors:
                logger.error("❌ ERREURS DE CONFIGURATION:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False

            # Afficher la configuration
            config.display_config()

            # Initialiser le client Binance
            logger.info("📡 Initialisation client Binance...")
            self.client = get_binance_client()

            # Initialiser les notifications
            logger.info("📱 Initialisation notifications Discord...")
            self.notif = get_notification_manager()

            # Tester Discord si activé
            if config.ALERTS['discord_enabled']:
                logger.info("🧪 Test connexion Discord...")
                # await self.notif.test_connection()

            # Initialiser les stratégies
            logger.info("📊 Initialisation des stratégies...")

            if config.DCA_SETTINGS['enabled']:
                self.dca_strategy = DCAStrategy()
                logger.info("  ✅ DCA Strategy initialisée")

            # Afficher les balances
            if config.TRADING_MODE != 'dry_run':
                logger.info("\n💰 Vérification des balances...")
                balances = self.client.get_balance()
                for asset, amount in balances.items():
                    if amount > 0:
                        logger.info(f"  {asset}: {amount:.8f}")

            logger.info("\n✅ Initialisation terminée avec succès!")
            logger.info("=" * 60 + "\n")

            return True

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}", exc_info=True)
            return False

    async def start(self):
        """Démarre le bot et toutes les stratégies"""
        try:
            self.running = True

            # Envoyer notification de démarrage
            await self.notif.send_startup_message()

            logger.info("🚀 DÉMARRAGE DES STRATÉGIES\n")

            # Démarrer la stratégie DCA
            if self.dca_strategy and config.DCA_SETTINGS['enabled']:
                task = asyncio.create_task(self.dca_strategy.start())
                self.tasks.append(task)
                logger.info("✅ Stratégie DCA démarrée")

            # TODO: Ajouter sniper et scanner ici plus tard
            # if self.sniper_strategy and config.SNIPER_SETTINGS['enabled']:
            #     task = asyncio.create_task(self.sniper_strategy.start())
            #     self.tasks.append(task)

            # if self.scanner and config.SCANNER_SETTINGS['enabled']:
            #     task = asyncio.create_task(self.scanner.start())
            #     self.tasks.append(task)

            # Démarrer la tâche de rapport quotidien
            task = asyncio.create_task(self._daily_report_task())
            self.tasks.append(task)

            logger.info(f"\n🟢 Bot opérationnel avec {len(self.tasks)} tâches actives\n")

            # Attendre que toutes les tâches soient terminées
            await asyncio.gather(*self.tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ Erreur dans le bot: {e}", exc_info=True)

    async def _daily_report_task(self):
        """Tâche pour envoyer le rapport quotidien"""
        while self.running:
            try:
                # Calculer le temps jusqu'au prochain rapport
                now = datetime.now()
                report_hour = config.ALERTS['daily_report_hour']

                # Prochaine heure de rapport
                next_report = now.replace(hour=report_hour, minute=0, second=0, microsecond=0)

                # Si l'heure est dépassée aujourd'hui, planifier pour demain
                if now.hour >= report_hour:
                    next_report += timedelta(days=1)

                # Attendre jusqu'à l'heure du rapport
                wait_seconds = (next_report - now).total_seconds()
                logger.info(f"📅 Prochain rapport quotidien: {next_report.strftime('%Y-%m-%d %H:%M')}")

                await asyncio.sleep(wait_seconds)

                # Envoyer le rapport
                await self._send_daily_report()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans daily_report_task: {e}")
                await asyncio.sleep(3600)  # Attendre 1h en cas d'erreur

    async def _send_daily_report(self):
        """Génère et envoie le rapport quotidien"""
        try:
            logger.info("📊 Génération du rapport quotidien...")

            stats = {
                'capital': config.CAPITAL_ALLOCATION['total'],
                'pnl': 0.0,
                'pnl_pct': 0.0,
                'trades_count': 0,
                'win_rate': 0.0,
                'dca_trades': 0,
                'sniper_trades': 0,
                'top_performers': []
            }

            # Récupérer les stats DCA
            if self.dca_strategy:
                dca_stats = self.dca_strategy.get_stats()
                stats['dca_trades'] = dca_stats['today_trades']
                stats['trades_count'] += dca_stats['today_trades']

            # TODO: Ajouter les stats des autres stratégies

            # Envoyer le rapport
            await self.notif.send_daily_report(stats)

        except Exception as e:
            logger.error(f"❌ Erreur génération rapport quotidien: {e}")

    async def stop(self):
        """Arrête proprement le bot"""
        try:
            logger.info("\n🛑 ARRÊT DU BOT...")
            self.running = False

            # Envoyer notification d'arrêt
            await self.notif.send_shutdown_message()

            # Annuler toutes les tâches
            for task in self.tasks:
                if not task.done():
                    task.cancel()

            # Attendre que toutes les tâches se terminent
            await asyncio.gather(*self.tasks, return_exceptions=True)

            # Fermer les connexions
            if self.client:
                self.client.close()

            logger.info("✅ Bot arrêté proprement")

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'arrêt: {e}")

    def signal_handler(self):
        """Gestionnaire de signaux pour arrêt propre"""
        logger.info(f"\n⚠️ Signal reçu")
        self.running = False


# Instance globale du bot
bot = None


async def main():
    """Fonction principale"""
    global bot

    try:
        # Créer et initialiser le bot
        bot = CryptoTradingBot()

        # Installer les gestionnaires de signaux
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, bot.signal_handler)

        # Initialiser
        if not await bot.initialize():
            logger.error("❌ Échec de l'initialisation")
            return 1

        # Démarrer le bot
        await bot.start()

        # Arrêt propre
        await bot.stop()

        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️ Interruption clavier détectée")
        if bot:
            await bot.stop()
        return 0

    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        return 1


def run():
    """Point d'entrée pour démarrer le bot"""
    try:
        # Vérifier Python 3.7+
        if sys.version_info < (3, 7):
            print("❌ Python 3.7+ requis")
            return 1

        # Lancer le bot
        exit_code = asyncio.run(main())
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"❌ Erreur au démarrage: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    run()
