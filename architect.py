"""
Architect - Evolves the trading logic based on R1 analysis
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Architect:
    """
    Architect: Rewrites active_logic.py based on R1 recommendations
    Only evolves if guardrails approve and R1 suggests improvements
    """
    
    def __init__(self, guardrails, logic_file_path: str = "active_logic.py"):
        """Initialize Architect"""
        self.guardrails = guardrails
        self.logic_file_path = logic_file_path
        self.evolution_history: list = []
        
    async def propose_evolution(self, analysis: Dict[str, Any]) -> Optional[str]:
        """
        Propose code evolution based on R1 analysis
        
        Args:
            analysis: Latest R1 analysis with evolution suggestions
            
        Returns:
            Proposed new code or None if no evolution needed
        """
        if not analysis or not analysis.get('evolution_suggestion'):
            logger.info("No evolution suggestion from R1")
            return None
        
        suggestion = analysis['evolution_suggestion']
        logger.info(f"R1 Evolution Suggestion: {suggestion.get('reason')}")
        logger.info(f"Suggested changes: {suggestion.get('suggestion')}")
        
        # Read current logic
        try:
            with open(self.logic_file_path, 'r') as f:
                current_code = f.read()
        except Exception as e:
            logger.error(f"Failed to read current logic: {str(e)}")
            return None
        
        # Generate evolved code (simplified - in production, use DeepSeek R1)
        evolved_code = self._generate_evolved_code(current_code, suggestion)
        
        return evolved_code
    
    def _generate_evolved_code(self, current_code: str, suggestion: Dict[str, Any]) -> str:
        """
        Generate evolved code based on suggestions
        This is a simplified version - in production, use DeepSeek R1/V3
        """
        # Example evolution: Add RSI indicator
        evolved_code = '''"""
Active Logic - Self-evolving trading logic
This file is automatically rewritten by the Architect
Last evolved: ''' + datetime.now().isoformat() + '''
"""
from typing import Dict, List, Any


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index"""
    if len(closes) < period + 1:
        return 50.0  # Neutral
    
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


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
    
    # RSI - NEW INDICATOR
    rsi = calculate_rsi(closes)
    
    # Volume metrics
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    
    return {
        'sma_5': sma_5,
        'sma_20': sma_20,
        'rsi': rsi,
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
    
    # Trading logic with RSI enhancement
    current_price = indicators.get('current_price', 0)
    sma_5 = indicators.get('sma_5', 0)
    sma_20 = indicators.get('sma_20', 0)
    rsi = indicators.get('rsi', 50)
    
    # Enhanced strategy with RSI
    if sma_5 > sma_20 and current_price > sma_5:
        if rsi < 70:  # Not overbought
            action = 'BUY'
            confidence = 0.70
            reason = 'Uptrend with RSI confirmation (not overbought)'
        elif rsi >= 70:
            action = 'HOLD'
            confidence = 0.55
            reason = 'Uptrend but RSI overbought - waiting'
    elif sma_5 < sma_20 and current_price < sma_5:
        if rsi > 30:  # Not oversold
            action = 'SELL'
            confidence = 0.70
            reason = 'Downtrend with RSI confirmation (not oversold)'
        elif rsi <= 30:
            action = 'HOLD'
            confidence = 0.55
            reason = 'Downtrend but RSI oversold - potential reversal'
    
    # Consider R1 analysis
    if analysis and analysis.get('signal'):
        r1_signal = analysis['signal']
        r1_confidence = analysis.get('confidence', 0.5)
        
        # Weight R1 analysis
        if r1_signal == action:
            confidence = (confidence + r1_confidence) / 2 + 0.1
        elif r1_signal != 'HOLD' and r1_confidence > 0.7:
            action = r1_signal
            confidence = r1_confidence
            reason = f"R1 override: {analysis.get('reasoning', 'No reason')}"
    
    return {
        'action': action,
        'confidence': min(confidence, 1.0),
        'reason': reason
    }
'''
        return evolved_code
    
    async def evolve(self, analysis: Dict[str, Any]) -> bool:
        """
        Evolve the trading logic if conditions are met
        
        Returns:
            True if evolution occurred, False otherwise
        """
        # Check if evolution is allowed
        if not self.guardrails.can_evolve():
            logger.info("Evolution blocked by stability lock")
            return False
        
        if self.guardrails.is_kill_switch_active():
            logger.warning("Evolution blocked by kill-switch")
            return False
        
        # Get evolution proposal
        new_code = await self.propose_evolution(analysis)
        if not new_code:
            logger.info("No evolution proposal generated")
            return False
        
        # Audit the new code
        audit_passed, audit_error = self.guardrails.audit_code(new_code)
        if not audit_passed:
            logger.error(f"Evolution rejected - audit failed: {audit_error}")
            return False
        
        # Write new code
        try:
            # Backup current logic
            backup_path = f"{self.logic_file_path}.backup"
            with open(self.logic_file_path, 'r') as f:
                with open(backup_path, 'w') as backup:
                    backup.write(f.read())
            
            # Write evolved logic
            with open(self.logic_file_path, 'w') as f:
                f.write(new_code)
            
            # Mark evolution in guardrails
            self.guardrails.mark_evolution()
            
            # Record evolution
            self.evolution_history.append({
                'timestamp': datetime.now().isoformat(),
                'reason': analysis['evolution_suggestion']['reason'],
                'suggestion': analysis['evolution_suggestion']['suggestion']
            })
            
            logger.info("✨ Evolution successful! Logic has been rewritten.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write evolved logic: {str(e)}")
            # Attempt to restore backup
            try:
                with open(backup_path, 'r') as backup:
                    with open(self.logic_file_path, 'w') as f:
                        f.write(backup.read())
                logger.info("Restored backup after evolution failure")
            except:
                logger.critical("Failed to restore backup!")
            return False
    
    def get_evolution_history(self) -> list:
        """Get history of all evolutions"""
        return self.evolution_history
