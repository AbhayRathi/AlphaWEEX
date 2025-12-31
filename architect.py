"""
Architect - Evolves the trading logic based on R1 analysis
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os
from data.memory import EvolutionMemory
from data.shared_state import get_shared_state, RiskLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
CONFIDENCE_BOOST = 0.1  # Boost when R1 signal matches our signal
R1_OVERRIDE_THRESHOLD = 0.7  # Confidence threshold for R1 to override
HIGH_RISK_REDUCTION = 0.5  # 50% reduction when global risk is HIGH


class Architect:
    """
    Architect: Rewrites active_logic.py based on R1 recommendations
    Only evolves if guardrails approve and R1 suggests improvements
    """
    
    def __init__(self, guardrails, logic_file_path: str = "active_logic.py", evolution_memory: Optional[EvolutionMemory] = None):
        """Initialize Architect"""
        self.guardrails = guardrails
        self.logic_file_path = logic_file_path
        self.evolution_history: list = []
        self.evolution_memory = evolution_memory or EvolutionMemory()
        self.shared_state = get_shared_state()
        
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
        
        # Extract parameters from suggestion (simplified)
        parameters = {
            'reason': suggestion.get('reason'),
            'suggestion': suggestion.get('suggestion'),
            'regime': analysis.get('regime', 'UNKNOWN')
        }
        
        # Check if parameters are blacklisted
        is_blacklisted, blacklist_reason = self.evolution_memory.is_blacklisted(parameters)
        if is_blacklisted:
            logger.warning(f"⚠️  Evolution blocked - parameters are blacklisted: {blacklist_reason}")
            return None
        
        # Read current logic
        try:
            with open(self.logic_file_path, 'r') as f:
                current_code = f.read()
        except Exception as e:
            logger.error(f"Failed to read current logic: {str(e)}")
            return None
        
        # Generate evolved code (simplified - in production, use DeepSeek R1)
        evolved_code = self._generate_evolved_code(current_code, suggestion, analysis)
        
        # Phase 5: Adversarial validation before deployment
        try:
            from core.adversary import AdversarialAlpha
            
            adversary = AdversarialAlpha(
                flash_crash_pct=-0.20,
                max_drawdown_threshold=0.15
            )
            
            approved, audit_report = adversary.red_team_strategy(evolved_code)
            
            if not approved:
                logger.error(
                    f"❌ Adversary REJECTED strategy\n"
                    f"   Failed tests: {audit_report.get('tests_failed', [])}\n"
                    f"   Recommendations: {audit_report.get('recommendations', [])}"
                )
                return None  # Don't deploy rejected strategy
            
            logger.info(
                f"✅ Adversary APPROVED strategy\n"
                f"   Passed tests: {audit_report.get('tests_passed', [])}"
            )
        except Exception as e:
            logger.error(f"Adversarial validation failed (non-critical): {e}")
            # Continue with evolution even if adversary check fails
        
        return evolved_code
    
    def _generate_evolved_code(self, current_code: str, suggestion: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """
        Generate evolved code based on suggestions and regime
        This is a simplified version - in production, use DeepSeek R1/V3
        """
        regime = analysis.get('regime', 'UNKNOWN')
        
        # Example evolution: Add regime-aware RSI indicator
        evolved_code = f'''"""
Active Logic - Self-evolving trading logic
This file is automatically rewritten by the Architect
Last evolved: {datetime.now().isoformat()}
Regime at evolution: {regime}
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
        return {{}}
    
    closes = [candle[4] for candle in ohlcv_data]
    volumes = [candle[5] for candle in ohlcv_data]
    
    # Simple Moving Averages
    sma_5 = sum(closes[-5:]) / min(5, len(closes)) if closes else 0
    sma_20 = sum(closes[-20:]) / min(20, len(closes)) if len(closes) >= 20 else sum(closes) / len(closes)
    
    # RSI - REGIME-AWARE INDICATOR
    rsi = calculate_rsi(closes)
    
    # Volume metrics
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    
    return {{
        'sma_5': sma_5,
        'sma_20': sma_20,
        'rsi': rsi,
        'current_price': closes[-1],
        'avg_volume': avg_volume,
        'current_volume': volumes[-1]
    }}


def generate_signal(indicators: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate trading signal based on indicators and R1 analysis
    REGIME-AWARE: Adapts strategy based on detected market regime
    
    Args:
        indicators: Calculated indicators
        analysis: R1 reasoning analysis
        
    Returns:
        Trading signal with action and parameters
    """
    if not indicators:
        return {{
            'action': 'HOLD',
            'confidence': 0.0,
            'reason': 'Insufficient indicators'
        }}
    
    action = 'HOLD'
    confidence = 0.5
    reason = 'Default hold position'
    
    # Get regime from analysis
    regime = analysis.get('regime', 'UNKNOWN')
    
    # Trading logic with REGIME-AWARENESS and RSI enhancement
    current_price = indicators.get('current_price', 0)
    sma_5 = indicators.get('sma_5', 0)
    sma_20 = indicators.get('sma_20', 0)
    rsi = indicators.get('rsi', 50)
    
    # Regime-specific strategy adaptation
    if regime == 'TRENDING_UP':
        # In uptrend, be more aggressive on buys
        if sma_5 > sma_20 and current_price > sma_5:
            if rsi < 70:  # Not overbought
                action = 'BUY'
                confidence = 0.75
                reason = f'Uptrend regime: Strong buy signal (RSI: {{rsi:.1f}})'
            else:
                action = 'HOLD'
                confidence = 0.55
                reason = 'Uptrend but RSI overbought - waiting'
    elif regime == 'TRENDING_DOWN':
        # In downtrend, be more aggressive on sells
        if sma_5 < sma_20 and current_price < sma_5:
            if rsi > 30:  # Not oversold
                action = 'SELL'
                confidence = 0.75
                reason = f'Downtrend regime: Strong sell signal (RSI: {{rsi:.1f}})'
            else:
                action = 'HOLD'
                confidence = 0.55
                reason = 'Downtrend but RSI oversold - potential reversal'
    elif regime == 'RANGE_VOLATILE':
        # In volatile range, use mean reversion with tighter thresholds
        if rsi < 35:
            action = 'BUY'
            confidence = 0.65
            reason = f'Range-volatile: Oversold mean reversion (RSI: {{rsi:.1f}})'
        elif rsi > 65:
            action = 'SELL'
            confidence = 0.65
            reason = f'Range-volatile: Overbought mean reversion (RSI: {{rsi:.1f}})'
        else:
            reason = 'Range-volatile: Waiting for extreme'
    elif regime == 'RANGE_QUIET':
        # In quiet range, wait for breakout confirmation
        if sma_5 > sma_20 and current_price > sma_5 and rsi > 55:
            action = 'BUY'
            confidence = 0.60
            reason = f'Range-quiet: Potential breakout up (RSI: {{rsi:.1f}})'
        elif sma_5 < sma_20 and current_price < sma_5 and rsi < 45:
            action = 'SELL'
            confidence = 0.60
            reason = f'Range-quiet: Potential breakout down (RSI: {{rsi:.1f}})'
        else:
            reason = 'Range-quiet: Waiting for breakout'
    
    # Consider R1 analysis for final decision
    if analysis and analysis.get('signal'):
        r1_signal = analysis['signal']
        r1_confidence = analysis.get('confidence', 0.5)
        
        # Weight R1 analysis using configured constants
        if r1_signal == action:
            confidence = min((confidence + r1_confidence) / 2 + CONFIDENCE_BOOST, 1.0)
        elif r1_signal != 'HOLD' and r1_confidence > R1_OVERRIDE_THRESHOLD:
            action = r1_signal
            confidence = r1_confidence
            reason = f"R1 override in {{regime}}: {{analysis.get('reasoning', 'No reason')}}"
    
    return {{
        'action': action,
        'confidence': min(confidence, 1.0),
        'reason': reason,
        'regime': regime
    }}
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
            
            # Record evolution in memory
            suggestion = analysis['evolution_suggestion']
            parameters = {
                'reason': suggestion.get('reason'),
                'suggestion': suggestion.get('suggestion'),
                'regime': analysis.get('regime', 'UNKNOWN')
            }
            self.evolution_memory.record_evolution(
                parameters=parameters,
                reason=suggestion['reason'],
                suggestion=suggestion['suggestion'],
                initial_equity=self.guardrails.current_equity
            )
            
            # Record evolution in local history
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
    
    def get_adjusted_size(self, base_size: float) -> float:
        """
        Calculate adjusted position size with ALL risk factors
        
        Formula: Final_Size = Base × Sentiment × Risk_Level_Multiplier × Whale_Adjustment
        
        Args:
            base_size: Base position size
            
        Returns:
            Adjusted position size
        """
        # Get sentiment multiplier
        sentiment_multiplier = self.shared_state.get_sentiment_multiplier()
        
        # Apply sentiment multiplier
        adjusted_size = base_size * sentiment_multiplier
        
        # Get global risk level
        global_risk = self.shared_state.get_global_risk_level()
        
        # Safety override: 50% reduction if HIGH risk
        if global_risk == RiskLevel.HIGH:
            adjusted_size *= HIGH_RISK_REDUCTION
            logger.warning(
                f"⚠️  HIGH RISK: Applying 50% reduction to position size "
                f"(Base: {base_size:.2f} → Sentiment: {base_size * sentiment_multiplier:.2f} "
                f"→ Final: {adjusted_size:.2f})"
            )
        else:
            logger.info(
                f"✅ Position sizing: Base: {base_size:.2f} × Sentiment: {sentiment_multiplier:.2f} "
                f"= {adjusted_size:.2f}"
            )
        
        # NEW: Whale dump risk reduction
        if self.shared_state.get_whale_dump_risk():
            adjusted_size *= 0.7  # 30% reduction
            logger.warning(
                f"🐋 Whale risk active: Position reduced by 30% "
                f"(Final size: {adjusted_size:.4f})"
            )
        
        return adjusted_size
