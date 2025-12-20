"""
Market Regime Detection Module
Detects market regimes using ADX (Trend Strength) and ATR (Volatility)
"""
import logging
from typing import List, Dict, Any
from enum import Enum
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    """Market regime types"""
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    RANGE_VOLATILE = "RANGE_VOLATILE"
    RANGE_QUIET = "RANGE_QUIET"


def calculate_atr(ohlcv_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR) - Volatility indicator
    
    Args:
        ohlcv_df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        period: ATR period (default: 14)
        
    Returns:
        Series with ATR values
    """
    high = ohlcv_df['high']
    low = ohlcv_df['low']
    close = ohlcv_df['close']
    
    # True Range calculation
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Average True Range (exponential moving average of TR)
    atr = true_range.ewm(span=period, adjust=False).mean()
    
    return atr


def calculate_adx(ohlcv_df: pd.DataFrame, period: int = 14) -> tuple:
    """
    Calculate Average Directional Index (ADX) - Trend strength indicator
    
    Args:
        ohlcv_df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        period: ADX period (default: 14)
        
    Returns:
        Tuple of (ADX, +DI, -DI) Series
    
    Note: Using tuple instead of tuple[...] for Python 3.8+ compatibility
    """
    high = ohlcv_df['high']
    low = ohlcv_df['low']
    close = ohlcv_df['close']
    
    # Calculate +DM and -DM
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    plus_dm = pd.Series(0.0, index=ohlcv_df.index)
    minus_dm = pd.Series(0.0, index=ohlcv_df.index)
    
    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Smooth the values
    atr = true_range.ewm(span=period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)
    
    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    dx = dx.replace([float('inf'), float('-inf')], 0)
    adx = dx.ewm(span=period, adjust=False).mean()
    
    return adx, plus_di, minus_di


def calculate_rsi(ohlcv_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        ohlcv_df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        period: RSI period (default: 14)
        
    Returns:
        Series with RSI values
    """
    close = ohlcv_df['close']
    delta = close.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def detect_regime(ohlcv_df: pd.DataFrame, adx_threshold: float = 25.0, atr_percentile: float = 50.0) -> str:
    """
    Detect market regime using ADX (trend strength) and ATR (volatility)
    
    Regime Logic:
    - ADX > threshold: Trending market
      - +DI > -DI: TRENDING_UP
      - +DI < -DI: TRENDING_DOWN
    - ADX <= threshold: Ranging market
      - ATR above median: RANGE_VOLATILE
      - ATR below median: RANGE_QUIET
    
    Args:
        ohlcv_df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        adx_threshold: ADX threshold to distinguish trending vs ranging (default: 25)
        atr_percentile: ATR percentile to distinguish volatile vs quiet (default: 50)
        
    Returns:
        Market regime string: TRENDING_UP, TRENDING_DOWN, RANGE_VOLATILE, or RANGE_QUIET
    """
    if len(ohlcv_df) < 30:
        logger.warning("Insufficient data for regime detection (need at least 30 candles)")
        return MarketRegime.RANGE_QUIET
    
    try:
        # Calculate indicators
        adx, plus_di, minus_di = calculate_adx(ohlcv_df)
        atr = calculate_atr(ohlcv_df)
        
        # Get latest values
        current_adx = adx.iloc[-1]
        current_plus_di = plus_di.iloc[-1]
        current_minus_di = minus_di.iloc[-1]
        current_atr = atr.iloc[-1]
        
        # Calculate ATR percentile for volatility assessment
        atr_threshold = atr.quantile(atr_percentile / 100.0)
        
        # Detect regime
        if current_adx > adx_threshold:
            # Trending market
            if current_plus_di > current_minus_di:
                regime = MarketRegime.TRENDING_UP
            else:
                regime = MarketRegime.TRENDING_DOWN
        else:
            # Ranging market
            if current_atr > atr_threshold:
                regime = MarketRegime.RANGE_VOLATILE
            else:
                regime = MarketRegime.RANGE_QUIET
        
        logger.info(
            f"Regime detected: {regime} "
            f"(ADX: {current_adx:.2f}, +DI: {current_plus_di:.2f}, "
            f"-DI: {current_minus_di:.2f}, ATR: {current_atr:.4f})"
        )
        
        return regime
        
    except Exception as e:
        logger.error(f"Error detecting regime: {str(e)}")
        return MarketRegime.RANGE_QUIET


def get_regime_metrics(ohlcv_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get all regime-related metrics for analysis
    
    Args:
        ohlcv_df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
        
    Returns:
        Dictionary with regime metrics
    """
    if len(ohlcv_df) < 30:
        return {
            'regime': MarketRegime.RANGE_QUIET,
            'adx': 0.0,
            'plus_di': 0.0,
            'minus_di': 0.0,
            'atr': 0.0,
            'rsi': 50.0,
            'error': 'Insufficient data'
        }
    
    try:
        # Calculate all indicators
        adx, plus_di, minus_di = calculate_adx(ohlcv_df)
        atr = calculate_atr(ohlcv_df)
        rsi = calculate_rsi(ohlcv_df)
        regime = detect_regime(ohlcv_df)
        
        # Get latest values
        metrics = {
            'regime': regime,
            'adx': float(adx.iloc[-1]) if not adx.empty else 0.0,
            'plus_di': float(plus_di.iloc[-1]) if not plus_di.empty else 0.0,
            'minus_di': float(minus_di.iloc[-1]) if not minus_di.empty else 0.0,
            'atr': float(atr.iloc[-1]) if not atr.empty else 0.0,
            'rsi': float(rsi.iloc[-1]) if not rsi.empty else 50.0,
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating regime metrics: {str(e)}")
        return {
            'regime': MarketRegime.RANGE_QUIET,
            'adx': 0.0,
            'plus_di': 0.0,
            'minus_di': 0.0,
            'atr': 0.0,
            'rsi': 50.0,
            'error': str(e)
        }


def ohlcv_list_to_dataframe(ohlcv_data: List[List]) -> pd.DataFrame:
    """
    Convert OHLCV list format to pandas DataFrame
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
        
    Returns:
        DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    """
    df = pd.DataFrame(
        ohlcv_data,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df
