# 🤖 Bot de Trading Crypto Hybride

Bot de trading automatisé combinant plusieurs stratégies pour maximiser les opportunités sur le marché crypto avec un capital de 500€.

## 📋 Fonctionnalités

### ✅ Implémentées (v1.0)
- **DCA Strategy (Dollar Cost Averaging Intelligent)**
  - Achats automatiques basés sur le RSI
  - RSI < 30: Achat agressif (40€)
  - RSI < 40: Achat moyen (25€)
  - RSI < 50: Petit achat (15€)
  - Vérification toutes les 4h
  - Maximum 1 achat par jour
  - Support BTC (70%) et ETH (30%)

- **Système de Notifications Discord**
  - Alertes en temps réel via Webhooks
  - Rapports quotidiens automatiques
  - Niveaux: INFO, OPPORTUNITY, TRADE, WARNING, ERROR

- **Modes de Trading**
  - `dry_run`: Simulation sans trading réel
  - `testnet`: Paper trading sur Binance Testnet
  - `live`: Trading réel sur Binance

### 🚧 À venir (v2.0)
- **Sniper Strategy**: Détection et achat de nouvelles listings
- **Scanner**: Détection d'opportunités (volume anormal, arbitrage, etc.)
- **Arbitrage**: Entre différents exchanges

## 🏗️ Architecture

```
crypto_hybrid_bot/
├── .env                    # Variables d'environnement (à créer)
├── .env.example           # Template pour .env
├── config.py              # Configuration globale
├── main.py                # Point d'entrée
├── requirements.txt       # Dépendances Python
├── strategies/
│   ├── __init__.py
│   └── dca_strategy.py    # Stratégie DCA
├── utils/
│   ├── __init__.py
│   ├── binance_client.py  # Client Binance
│   ├── indicators.py      # Indicateurs techniques (RSI, SMA, etc.)
│   └── notifications.py   # Notifications Telegram
├── data/
│   └── trades.json        # Historique des trades
└── logs/
    └── bot.log           # Logs détaillés
```

## 🚀 Installation

### 1. Prérequis
- Python 3.7 ou supérieur
- Compte Binance (ou Binance Testnet pour tester)
- Discord Webhook (optionnel mais recommandé)

### 2. Cloner et installer

```bash
cd Bot_crypto

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

#### A. Créer le fichier .env

```bash
cp .env.example .env
```

#### B. Éditer .env avec vos credentials

```bash
# Mode de trading (dry_run, testnet, ou live)
TRADING_MODE=dry_run

# Binance API (pour mode live)
BINANCE_API_KEY=votre_api_key
BINANCE_API_SECRET=votre_secret_key

# Binance Testnet API (pour mode testnet)
BINANCE_TESTNET_API_KEY=votre_testnet_key
BINANCE_TESTNET_API_SECRET=votre_testnet_secret

# Discord Webhook
DISCORD_WEBHOOK_URL=votre_discord_webhook_url
```

#### C. Obtenir les credentials

**Binance API (mode live):**
1. Se connecter sur [Binance](https://www.binance.com)
2. Compte → API Management
3. Créer une nouvelle API Key
4. ⚠️ **IMPORTANT**: Activer uniquement "Enable Spot & Margin Trading"
5. Ajouter votre IP en whitelist (recommandé)

**Binance Testnet (mode testnet):**
1. Aller sur [Testnet Binance](https://testnet.binance.vision)
2. Créer un compte testnet
3. Générer des API keys

**Discord Webhook:**
1. Ouvrir Discord et aller sur le serveur de votre choix
2. Paramètres du serveur → Intégrations → Webhooks
3. Créer un nouveau webhook
4. Copier l'URL du webhook
5. Coller l'URL dans votre fichier `.env`

### 4. Ajuster la configuration

Éditer `config.py` pour personnaliser:
- Allocation du capital
- Niveaux RSI et montants
- Intervalles de vérification
- Activation/désactivation des stratégies

```python
# Exemple: Modifier les niveaux RSI
DCA_SETTINGS = {
    'rsi_levels': {
        25: 50,  # RSI < 25 → acheter 50€
        35: 30,  # RSI < 35 → acheter 30€
        45: 20   # RSI < 45 → acheter 20€
    }
}
```

## 🎮 Utilisation

### Démarrer le bot

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le bot
python main.py

# Pour arrêter le bot proprement: Ctrl+C
```

### Tester la configuration

```bash
# Vérifier la config
python config.py

# Devrait afficher:
# ✅ Configuration valide!
# 🤖 CONFIGURATION DU BOT DE TRADING CRYPTO
# ...
```

### Modes d'exécution

**1. Mode DRY RUN (recommandé pour débuter)**
```bash
# Dans .env
TRADING_MODE=dry_run
```
- Simule tous les trades
- N'utilise pas d'argent réel
- Parfait pour tester la logique

**2. Mode TESTNET (paper trading)**
```bash
# Dans .env
TRADING_MODE=testnet
```
- Utilise Binance Testnet
- Argent virtuel
- Simule des conditions réelles

**3. Mode LIVE (trading réel)**
```bash
# Dans .env
TRADING_MODE=live
```
- ⚠️ **ATTENTION**: Utilise de l'argent réel!
- Commencer avec un petit capital
- Vérifier tous les paramètres

## 📊 Monitoring

### Logs

Les logs sont dans `logs/bot.log` et dans la console:

```bash
# Suivre les logs en temps réel
tail -f logs/bot.log
```

### Notifications Discord

Si configuré, vous recevrez sur Discord:
- Alertes d'opportunités DCA
- Confirmations de trades
- Rapport quotidien à 20h
- Erreurs et avertissements

### Données

Les trades sont sauvegardés dans `data/trades.json`:

```json
{
  "dca_trades": [
    {
      "timestamp": "2025-01-15T10:30:00",
      "coin": "BTC",
      "amount": 25,
      "price": 95000,
      "rsi": 38.5
    }
  ]
}
```

## ⚙️ Configuration avancée

### Modifier les coins DCA

```python
# config.py
DCA_SETTINGS = {
    'coins': {
        'BTC': 0.5,   # 50%
        'ETH': 0.3,   # 30%
        'BNB': 0.2    # 20%
    }
}
```

### Changer l'intervalle de vérification

```python
# config.py
DCA_SETTINGS = {
    'check_interval': 7200,  # 2 heures (en secondes)
}
```

### Activer/désactiver les stratégies

```python
# config.py
DCA_SETTINGS = {
    'enabled': True  # ou False pour désactiver
}
```

## 🔒 Sécurité

### Best Practices

1. **Ne jamais commit le .env**
   - Déjà dans .gitignore
   - Ne partagez JAMAIS vos API keys

2. **Binance API restrictions**
   - Activer uniquement "Spot Trading"
   - Désactiver "Withdrawals"
   - Utiliser IP whitelist

3. **Commencer petit**
   - Tester en dry_run
   - Puis testnet
   - Puis live avec petit capital

4. **Monitoring**
   - Vérifier régulièrement les logs
   - Surveiller les notifications Discord
   - Vérifier votre compte Binance

## 🐛 Dépannage

### Le bot ne démarre pas

```bash
# Vérifier la configuration
python config.py

# Vérifier les dépendances
pip install -r requirements.txt --upgrade
```

### Pas de notifications Discord

1. Vérifier que `DISCORD_WEBHOOK_URL` est correct
2. Vérifier que le webhook n'a pas été supprimé sur Discord
3. Regarder les logs pour les erreurs

### Erreur API Binance

1. Vérifier que les API keys sont correctes
2. Vérifier que l'IP est whitelistée (si configuré)
3. Vérifier les permissions de l'API key

### Mode dry_run n'achète rien

- Normal! Le mode dry_run simule les achats
- Regardez les logs pour voir les opportunités détectées
- Les trades simulés apparaissent avec `[DRY RUN]`

## 📈 Stratégie DCA Expliquée

### Principe

Le bot vérifie le RSI (Relative Strength Index) toutes les 4h:
- RSI bas = actif survendu = opportunité d'achat
- Plus le RSI est bas, plus on achète

### Exemple de session

```
[08:00] 📊 Vérification DCA
[08:01] 📊 BTC: Prix=$95,000, RSI=45.2, Signal=WEAK
[08:01] ✅ Aucune opportunité DCA détectée

[12:00] 📊 Vérification DCA
[12:01] 📊 BTC: Prix=$93,500, RSI=38.1, Signal=MODERATE
[12:02] 🎯 Opportunité DCA: BTC - RSI=38.1, Montant=25€
[12:03] ✅ DCA exécuté: 0.000267 BTC @ $93,500

[16:00] 📊 Vérification DCA
[16:01] ⏸️ 1 achat par jour effectué, arrêt pour aujourd'hui
```

## 🚧 Roadmap

### Version 1.0 ✅
- [x] DCA Strategy
- [x] Notifications Discord
- [x] Multi-modes (dry_run, testnet, live)
- [x] Logging complet
- [x] Arrêt propre avec Ctrl+C

### Version 2.0 (À venir)
- [ ] Sniper Strategy (nouvelles listings)
- [ ] Scanner d'opportunités
- [ ] Dashboard console amélioré
- [ ] Backtesting sur données historiques

### Version 3.0 (Futur)
- [ ] Arbitrage multi-exchange
- [ ] Machine Learning pour prédictions
- [ ] Interface Web (React)
- [ ] API REST pour contrôle à distance

## 📝 Réponses aux questions

### 1. Détection des annonces Binance

**Réponse**: Binance ne fournit pas d'API officielle pour les annonces de listing. Options:
- Scraping de la page d'annonces (risque de ban)
- Utiliser des services tiers (CoinMarketCal, etc.)
- Monitoring Twitter/Telegram officiel Binance
- **Recommandation**: Implémenter le sniper plus tard avec un service fiable

### 2. Gestion sécurisée des API keys

**Implémenté**:
- Fichier `.env` pour les secrets (dans .gitignore)
- Variables d'environnement chargées avec python-dotenv
- Validation au démarrage
- Logs ne contiennent JAMAIS les keys
- **Bonus**: Possibilité d'utiliser des gestionnaires de secrets (AWS Secrets Manager, etc.)

### 3. Système de recovery si crash

**Implémenté**:
- Sauvegarde de l'historique dans `data/trades.json`
- Logs détaillés avec rotation
- Gestionnaires de signaux (SIGINT, SIGTERM) pour arrêt propre
- Les tâches asyncio se terminent gracieusement
- **À améliorer**: Ajouter un watchdog externe (systemd, supervisor, PM2)

### 4. Système de backtesting

**À implémenter** dans v2.0, mais la structure est prête:
- Les indicateurs (RSI, etc.) acceptent des données historiques
- Le client Binance peut récupérer des klines historiques
- Il suffit de créer un mode `backtest` qui:
  1. Charge des données historiques
  2. Simule les trades
  3. Calcule les performances

**Exemple de structure**:
```python
# strategies/backtester.py (à créer)
async def backtest(strategy, start_date, end_date):
    # Charger données historiques
    # Rejouer la stratégie
    # Calculer P&L
    # Générer rapport
```

## 📄 License

MIT License - Libre d'utilisation

## ⚠️ Disclaimer

**Ce bot est fourni à des fins éducatives uniquement.**

- Le trading comporte des risques
- Vous pouvez perdre votre capital
- Testez toujours en dry_run d'abord
- L'auteur n'est pas responsable de vos pertes
- Faites vos propres recherches (DYOR)

**Utilisez à vos propres risques!**

## 💬 Support

Pour toute question ou problème:
1. Vérifier les logs dans `logs/bot.log`
2. Consulter cette documentation
3. Tester en mode dry_run

---

**Bon trading! 🚀💰**
