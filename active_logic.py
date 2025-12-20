"""
Active Logic - Self-evolving trading logic
This file is automatically rewritten by the Architect
"""
from typing import Dict, List, Any


def calculate_indicators(ohlcv_data: List[List]) -> Dict[str, Any]:
    """
    Calculate trading indicators from OHLCV data
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
        
    Returns:
        Dictionary of calculated indicators
    """
    if len(ohlcv_data) < 2:
        return {}
    
    closes = [candle[4] for candle in ohlcv_data]
    volumes = [candle[5] for candle in ohlcv_data]
    
    # Simple Moving Averages
    sma_5 = sum(closes[-5:]) / min(5, len(closes)) if closes else 0
    sma_20 = sum(closes[-20:]) / min(20, len(closes)) if len(closes) >= 20 else sum(closes) / len(closes)
    
    # Volume metrics
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    
    return {
        'sma_5': sma_5,
        'sma_20': sma_20,
        'current_price': closes[-1],
        'avg_volume': avg_volume,
        'current_volume': volumes[-1]
    }


def generate_signal(indicators: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate trading signal based on indicators and R1 analysis
    
    Args:
        indicators: Calculated indicators
        analysis: R1 reasoning analysis
        
    Returns:
        Trading signal with action and parameters
    """
    if not indicators:
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'reason': 'Insufficient indicators'
        }
    
    action = 'HOLD'
    confidence = 0.5
    reason = 'Default hold position'
    
    # Trading logic (will be evolved by Architect)
    current_price = indicators.get('current_price', 0)
    sma_5 = indicators.get('sma_5', 0)
    sma_20 = indicators.get('sma_20', 0)
    
    # Simple crossover strategy
    if sma_5 > sma_20 and current_price > sma_5:
        action = 'BUY'
        confidence = 0.65
        reason = 'Short MA above long MA, price trending up'
    elif sma_5 < sma_20 and current_price < sma_5:
        action = 'SELL'
        confidence = 0.65
        reason = 'Short MA below long MA, price trending down'
    
    # Consider R1 analysis
    if analysis and analysis.get('signal'):
        r1_signal = analysis['signal']
        r1_confidence = analysis.get('confidence', 0.5)
        
        # Weight R1 analysis higher
        if r1_signal == action:
            confidence = (confidence + r1_confidence) / 2 + 0.1
        elif r1_signal != 'HOLD':
            action = r1_signal
            confidence = r1_confidence
            reason = f"R1 override: {analysis.get('reasoning', 'No reason')}"
    
    return {
        'action': action,
        'confidence': min(confidence, 1.0),
        'reason': reason
    }
