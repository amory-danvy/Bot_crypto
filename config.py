"""
Configuration centrale pour le bot de trading crypto hybride
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

# === MODE DE TRADING ===
# Options: 'dry_run' (simulation), 'testnet' (paper trading), 'live' (réel)
TRADING_MODE = os.getenv('TRADING_MODE', 'dry_run')

# === API KEYS ===
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Testnet keys (pour paper trading)
BINANCE_TESTNET_API_KEY = os.getenv('BINANCE_TESTNET_API_KEY')
BINANCE_TESTNET_API_SECRET = os.getenv('BINANCE_TESTNET_API_SECRET')

# Discord
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# === ALLOCATION DU CAPITAL ===
CAPITAL_ALLOCATION = {
    'dca': 200,        # Budget pour DCA automatique
    'sniper': 100,     # Budget pour sniper les nouvelles listings
    'reserve': 200,    # Réserve pour opportunités manuelles
    'total': 500
}

# === CONFIGURATION DCA STRATEGY ===
DCA_SETTINGS = {
    # Répartition par coin (doit totaliser 1.0)
    'coins': {
        'BTC': 0.7,   # 70% du budget DCA sur Bitcoin
        'ETH': 0.3    # 30% du budget DCA sur Ethereum
    },

    # Intervalle de vérification en secondes (14400 = 4 heures)
    'check_interval': 14400,

    # Maximum à acheter par jour (en €)
    'max_daily_buy': 40,

    # Niveaux RSI et montants d'achat correspondants
    # RSI seuil : montant en €
    'rsi_levels': {
        30: 40,  # Panique/oversold extrême → achat agressif
        40: 25,  # Dip significatif → achat moyen
        50: 15   # Normal-bas → petit achat
    },

    # Période RSI (14 est standard)
    'rsi_period': 14,

    # Timeframe pour calcul RSI (1h, 4h, 1d, etc.)
    'timeframe': '4h',

    # Capital minimum pour effectuer un trade (€)
    'min_trade_amount': 10,

    # Activer/désactiver la stratégie
    'enabled': True
}

# === CONFIGURATION SNIPER STRATEGY ===
SNIPER_SETTINGS = {
    # Montant maximum par trade de snipe (€)
    'max_per_trade': 50,

    # Stop loss (-10%)
    'stop_loss': -0.10,

    # Take profit (+30%)
    'take_profit': 0.30,

    # Activation du trailing stop après ce gain (+20%)
    'trailing_stop_activation': 0.20,

    # Trailing stop distance (5%)
    'trailing_stop_distance': 0.05,

    # Temps d'attente avant le listing (secondes)
    'prepare_time': 30,

    # Intervalle de vérification des annonces (secondes)
    'check_interval': 60,

    # Activer/désactiver la stratégie
    'enabled': False  # Désactivé par défaut, à activer manuellement
}

# === CONFIGURATION SCANNER D'OPPORTUNITÉS ===
SCANNER_SETTINGS = {
    # Intervalle de scan (300 = 5 minutes)
    'check_interval': 300,

    # Seuil de volume anormal (500% = 5x la moyenne)
    'volume_threshold': 5.0,

    # Période pour la moyenne de volume (jours)
    'volume_period': 7,

    # RSI extrême pour alerte
    'rsi_extreme': 25,

    # Différence de prix minimum entre exchanges pour arbitrage (%)
    'arbitrage_threshold': 0.005,

    # Funding rate minimum pour alerte (%)
    'funding_rate_threshold': 0.001,

    # Top N coins à surveiller
    'top_coins': 100,

    # Activer/désactiver le scanner
    'enabled': True
}

# === CONFIGURATION DES ALERTES ===
ALERTS = {
    # Activer/désactiver Discord
    'discord_enabled': False,

    # Niveaux d'alertes
    'levels': {
        'INFO': '📊',
        'OPPORTUNITY': '🎯',
        'TRADE': '✅',
        'WARNING': '⚠️',
        'ERROR': '🔴',
        'PROFIT': '💰',
        'LOSS': '📉'
    },

    # Heure du rapport quotidien (format 24h)
    'daily_report_hour': 20,

    # Envoyer des alertes même en dry_run
    'alert_in_dry_run': True
}

# === CONFIGURATION BINANCE ===
BINANCE_CONFIG = {
    # Endpoints selon le mode
    'testnet_url': 'https://testnet.binance.vision/api',
    'live_url': 'https://api.binance.com/api',

    # Rate limiting (requêtes par minute)
    'rate_limit': 1200,

    # Retry settings
    'max_retries': 3,
    'retry_delay': 1,  # secondes

    # Websocket pour prix temps réel
    'use_websocket': True,

    # Paires de trading
    'quote_currency': 'USDT',  # Devise de cotation

    # Précision des ordres (décimales)
    'price_precision': 8,
    'quantity_precision': 8
}

# === CHEMINS DES FICHIERS ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# Créer les dossiers s'ils n'existent pas
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Fichiers de données
TRADES_FILE = DATA_DIR / 'trades.json'
BALANCE_FILE = DATA_DIR / 'balance.json'
STATS_FILE = DATA_DIR / 'stats.json'

# Fichier de logs
LOG_FILE = LOGS_DIR / 'bot.log'

# === CONFIGURATION DES LOGS ===
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOG_FILE),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

# === VALIDATION DE LA CONFIGURATION ===
def validate_config():
    """Valide la configuration avant de démarrer le bot"""
    errors = []

    # Vérifier le mode de trading
    if TRADING_MODE not in ['dry_run', 'testnet', 'live']:
        errors.append(f"TRADING_MODE invalide: {TRADING_MODE}")

    # Vérifier les API keys si pas en dry_run
    if TRADING_MODE == 'testnet':
        if not BINANCE_TESTNET_API_KEY or not BINANCE_TESTNET_API_SECRET:
            errors.append("BINANCE_TESTNET_API_KEY et BINANCE_TESTNET_API_SECRET requis en mode testnet")
    elif TRADING_MODE == 'live':
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            errors.append("BINANCE_API_KEY et BINANCE_API_SECRET requis en mode live")

    # Vérifier Discord si activé
    if ALERTS['discord_enabled']:
        if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == 'your_discord_webhook_url_here':
            errors.append("DISCORD_WEBHOOK_URL requis si discord_enabled=True")

    # Vérifier la répartition DCA
    total_allocation = sum(DCA_SETTINGS['coins'].values())
    if abs(total_allocation - 1.0) > 0.01:
        errors.append(f"La répartition DCA doit totaliser 1.0 (actuellement: {total_allocation})")

    # Vérifier les montants
    if DCA_SETTINGS['max_daily_buy'] > CAPITAL_ALLOCATION['dca']:
        errors.append("max_daily_buy ne peut pas dépasser le budget DCA total")

    if SNIPER_SETTINGS['max_per_trade'] > CAPITAL_ALLOCATION['sniper']:
        errors.append("max_per_trade ne peut pas dépasser le budget sniper total")

    return errors

# === AFFICHAGE DE LA CONFIGURATION ===
def display_config():
    """Affiche un résumé de la configuration"""
    print("\n" + "="*60)
    print("🤖 CONFIGURATION DU BOT DE TRADING CRYPTO")
    print("="*60)
    print(f"\n📊 Mode de trading: {TRADING_MODE.upper()}")
    print(f"💰 Capital total: {CAPITAL_ALLOCATION['total']}€")
    print(f"   - DCA: {CAPITAL_ALLOCATION['dca']}€")
    print(f"   - Sniper: {CAPITAL_ALLOCATION['sniper']}€")
    print(f"   - Réserve: {CAPITAL_ALLOCATION['reserve']}€")

    print(f"\n📈 Stratégies actives:")
    print(f"   - DCA: {'✅' if DCA_SETTINGS['enabled'] else '❌'}")
    print(f"   - Sniper: {'✅' if SNIPER_SETTINGS['enabled'] else '❌'}")
    print(f"   - Scanner: {'✅' if SCANNER_SETTINGS['enabled'] else '❌'}")

    print(f"\n📱 Alertes Discord: {'✅' if ALERTS['discord_enabled'] else '❌'}")
    print("="*60 + "\n")

if __name__ == '__main__':
    # Tester la configuration
    errors = validate_config()
    if errors:
        print("❌ ERREURS DE CONFIGURATION:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration valide!")
        display_config()
