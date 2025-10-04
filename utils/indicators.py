"""
Indicateurs techniques pour l'analyse de marché
"""
import numpy as np
import pandas as pd
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calcule le RSI (Relative Strength Index)

    Args:
        prices: Liste des prix de clôture
        period: Période pour le calcul (défaut: 14)

    Returns:
        Valeur du RSI (0-100)
    """
    if len(prices) < period + 1:
        logger.warning(f"⚠️ Pas assez de données pour calculer RSI (besoin {period + 1}, reçu {len(prices)})")
        return 50.0  # Valeur neutre par défaut

    try:
        # Convertir en array numpy
        prices_array = np.array(prices, dtype=float)

        # Calculer les variations
        deltas = np.diff(prices_array)

        # Séparer gains et pertes
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # Calculer les moyennes mobiles exponentielles
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])

        # Calculer les moyennes mobiles pour les valeurs restantes
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        # Éviter la division par zéro
        if avg_loss == 0:
            return 100.0

        # Calculer RS et RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        logger.debug(f"📊 RSI calculé: {rsi:.2f}")
        return round(rsi, 2)

    except Exception as e:
        logger.error(f"❌ Erreur calcul RSI: {e}")
        return 50.0


def calculate_sma(prices: List[float], period: int) -> float:
    """
    Calcule la SMA (Simple Moving Average)

    Args:
        prices: Liste des prix
        period: Période pour la moyenne

    Returns:
        Valeur de la SMA
    """
    if len(prices) < period:
        return 0.0

    try:
        return round(np.mean(prices[-period:]), 2)
    except Exception as e:
        logger.error(f"❌ Erreur calcul SMA: {e}")
        return 0.0


def calculate_ema(prices: List[float], period: int) -> float:
    """
    Calcule l'EMA (Exponential Moving Average)

    Args:
        prices: Liste des prix
        period: Période pour la moyenne

    Returns:
        Valeur de l'EMA
    """
    if len(prices) < period:
        return 0.0

    try:
        prices_array = np.array(prices, dtype=float)
        ema = pd.Series(prices_array).ewm(span=period, adjust=False).mean().iloc[-1]
        return round(ema, 2)
    except Exception as e:
        logger.error(f"❌ Erreur calcul EMA: {e}")
        return 0.0


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: int = 2
) -> Tuple[float, float, float]:
    """
    Calcule les bandes de Bollinger

    Args:
        prices: Liste des prix
        period: Période pour la SMA
        std_dev: Nombre d'écarts-types

    Returns:
        Tuple (bande_sup, sma, bande_inf)
    """
    if len(prices) < period:
        return (0.0, 0.0, 0.0)

    try:
        prices_array = np.array(prices[-period:], dtype=float)
        sma = np.mean(prices_array)
        std = np.std(prices_array)

        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        return (
            round(upper_band, 2),
            round(sma, 2),
            round(lower_band, 2)
        )
    except Exception as e:
        logger.error(f"❌ Erreur calcul Bollinger Bands: {e}")
        return (0.0, 0.0, 0.0)


def calculate_volume_ratio(volumes: List[float], period: int = 7) -> float:
    """
    Calcule le ratio de volume actuel vs moyenne

    Args:
        volumes: Liste des volumes
        period: Période pour la moyenne

    Returns:
        Ratio volume_actuel / volume_moyen
    """
    if len(volumes) < period + 1:
        return 1.0

    try:
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[-period - 1:-1])

        if avg_volume == 0:
            return 1.0

        ratio = current_volume / avg_volume
        return round(ratio, 2)
    except Exception as e:
        logger.error(f"❌ Erreur calcul volume ratio: {e}")
        return 1.0


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[float, float, float]:
    """
    Calcule le MACD (Moving Average Convergence Divergence)

    Args:
        prices: Liste des prix
        fast_period: Période EMA rapide
        slow_period: Période EMA lente
        signal_period: Période de la ligne de signal

    Returns:
        Tuple (macd, signal, histogramme)
    """
    if len(prices) < slow_period + signal_period:
        return (0.0, 0.0, 0.0)

    try:
        prices_series = pd.Series(prices, dtype=float)

        # Calculer les EMAs
        ema_fast = prices_series.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices_series.ewm(span=slow_period, adjust=False).mean()

        # Calculer MACD
        macd_line = ema_fast - ema_slow

        # Ligne de signal
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Histogramme
        histogram = macd_line - signal_line

        return (
            round(macd_line.iloc[-1], 2),
            round(signal_line.iloc[-1], 2),
            round(histogram.iloc[-1], 2)
        )
    except Exception as e:
        logger.error(f"❌ Erreur calcul MACD: {e}")
        return (0.0, 0.0, 0.0)


def calculate_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14
) -> float:
    """
    Calcule l'ATR (Average True Range) - mesure de volatilité

    Args:
        highs: Liste des prix hauts
        lows: Liste des prix bas
        closes: Liste des prix de clôture
        period: Période pour le calcul

    Returns:
        Valeur de l'ATR
    """
    if len(highs) < period + 1:
        return 0.0

    try:
        # Convertir en arrays
        highs = np.array(highs, dtype=float)
        lows = np.array(lows, dtype=float)
        closes = np.array(closes, dtype=float)

        # Calculer les True Ranges
        tr1 = highs[1:] - lows[1:]
        tr2 = np.abs(highs[1:] - closes[:-1])
        tr3 = np.abs(lows[1:] - closes[:-1])

        true_range = np.maximum(tr1, np.maximum(tr2, tr3))

        # Calculer ATR (moyenne mobile exponentielle des TR)
        atr = np.mean(true_range[-period:])

        return round(atr, 2)
    except Exception as e:
        logger.error(f"❌ Erreur calcul ATR: {e}")
        return 0.0


def is_oversold(rsi: float, threshold: float = 30) -> bool:
    """
    Vérifie si un actif est en survente (oversold)

    Args:
        rsi: Valeur du RSI
        threshold: Seuil d'oversold (défaut: 30)

    Returns:
        True si oversold, False sinon
    """
    return rsi < threshold


def is_overbought(rsi: float, threshold: float = 70) -> bool:
    """
    Vérifie si un actif est en surachat (overbought)

    Args:
        rsi: Valeur du RSI
        threshold: Seuil d'overbought (défaut: 70)

    Returns:
        True si overbought, False sinon
    """
    return rsi > threshold


def get_buy_signal_strength(rsi: float) -> str:
    """
    Évalue la force d'un signal d'achat basé sur le RSI

    Args:
        rsi: Valeur du RSI

    Returns:
        'STRONG', 'MODERATE', 'WEAK', ou 'NONE'
    """
    if rsi < 25:
        return 'STRONG'
    elif rsi < 35:
        return 'MODERATE'
    elif rsi < 50:
        return 'WEAK'
    else:
        return 'NONE'


def analyze_market_condition(
    rsi: float,
    volume_ratio: float,
    price: float,
    sma_50: float
) -> dict:
    """
    Analyse globale de la condition du marché

    Args:
        rsi: Valeur du RSI
        volume_ratio: Ratio de volume
        price: Prix actuel
        sma_50: SMA 50 périodes

    Returns:
        Dictionnaire avec l'analyse
    """
    analysis = {
        'rsi': rsi,
        'volume_ratio': volume_ratio,
        'price': price,
        'sma_50': sma_50,
        'trend': 'unknown',
        'buy_signal': 'NONE',
        'sell_signal': 'NONE',
        'signals': []
    }

    # Tendance basée sur prix vs SMA
    if sma_50 > 0:
        if price > sma_50 * 1.02:
            analysis['trend'] = 'bullish'
        elif price < sma_50 * 0.98:
            analysis['trend'] = 'bearish'
        else:
            analysis['trend'] = 'neutral'

    # Signaux d'achat
    if is_oversold(rsi, 30):
        analysis['buy_signal'] = get_buy_signal_strength(rsi)
        analysis['signals'].append('RSI oversold')

    if volume_ratio > 3.0 and rsi < 40:
        analysis['signals'].append('High volume + low RSI')

    # Signaux de vente
    if is_overbought(rsi, 70):
        analysis['sell_signal'] = 'STRONG' if rsi > 80 else 'MODERATE'
        analysis['signals'].append('RSI overbought')

    return analysis


# Fonction helper pour obtenir les prix depuis les klines
def extract_prices_from_klines(klines: List[List]) -> dict:
    """
    Extrait les prix des données klines de Binance

    Args:
        klines: Données klines de Binance

    Returns:
        Dict avec 'open', 'high', 'low', 'close', 'volume'
    """
    try:
        return {
            'open': [float(k[1]) for k in klines],
            'high': [float(k[2]) for k in klines],
            'low': [float(k[3]) for k in klines],
            'close': [float(k[4]) for k in klines],
            'volume': [float(k[5]) for k in klines],
        }
    except Exception as e:
        logger.error(f"❌ Erreur extraction prix depuis klines: {e}")
        return {
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': []
        }
