"""
Contrarian Sentiment Analyzer based on Funding Rates

This module analyzes funding rates to provide contrarian trading signals.
- Extreme Positive funding (>0.05%): Restricts Long trades (over-leveraged, crash likely)
- Extreme Negative funding (<-0.05%): Prioritizes Long trades (short-squeeze likely)
"""
import logging
from typing import Dict, Any, Literal

logger = logging.getLogger(__name__)


class FundingRateAnalyzer:
    """
    Analyzes funding rates for contrarian trading signals
    
    Features:
    - Classifies funding rates as Extreme Positive, Extreme Negative, or Neutral
    - Provides trading restrictions/priorities based on market leverage
    - Integrates with technical indicators (RSI/MACD) for weighted decisions
    """
    
    # Funding rate thresholds
    EXTREME_POSITIVE_THRESHOLD = 0.05  # 0.05% - market is over-leveraged long
    EXTREME_NEGATIVE_THRESHOLD = -0.05  # -0.05% - market is over-leveraged short
    
    # Trading confidence thresholds
    CONFIDENCE_THRESHOLD = 0.5  # Threshold for overriding actions
    EXECUTION_THRESHOLD = 0.65  # Minimum confidence to execute trades
    
    def __init__(self):
        """Initialize the funding rate analyzer"""
        logger.info("✅ FundingRateAnalyzer initialized")
    
    def _adjust_confidence(self, confidence: float, weight: float) -> float:
        """
        Helper method to adjust confidence with weight
        
        Args:
            confidence: Original confidence (0.0-1.0)
            weight: Weight to apply (-1.0 to 1.0)
            
        Returns:
            Adjusted confidence clamped to [0.0, 1.0]
        """
        adjusted = confidence * (1.0 + weight)
        return max(0.0, min(1.0, adjusted))
    
    def classify_funding_rate(self, funding_rate: float) -> Literal["EXTREME_POSITIVE", "EXTREME_NEGATIVE", "NEUTRAL"]:
        """
        Classify funding rate into categories
        
        Args:
            funding_rate: Funding rate as percentage (e.g., 0.06 for 0.06%)
            
        Returns:
            Classification: EXTREME_POSITIVE, EXTREME_NEGATIVE, or NEUTRAL
        """
        if funding_rate > self.EXTREME_POSITIVE_THRESHOLD:
            return "EXTREME_POSITIVE"
        elif funding_rate < self.EXTREME_NEGATIVE_THRESHOLD:
            return "EXTREME_NEGATIVE"
        else:
            return "NEUTRAL"
    
    def get_funding_sentiment(self, funding_rate: float) -> Dict[str, Any]:
        """
        Analyze funding rate and generate sentiment
        
        Args:
            funding_rate: Funding rate as percentage
            
        Returns:
            Dictionary with sentiment analysis:
            - classification: EXTREME_POSITIVE, EXTREME_NEGATIVE, or NEUTRAL
            - signal: RESTRICT_LONG, PRIORITIZE_LONG, or NEUTRAL
            - confidence: 0.0-1.0 confidence in the signal
            - reasoning: Explanation of the sentiment
        """
        classification = self.classify_funding_rate(funding_rate)
        
        if classification == "EXTREME_POSITIVE":
            return {
                "classification": classification,
                "signal": "RESTRICT_LONG",
                "confidence": 0.8,
                "reasoning": f"Funding rate {funding_rate:.3f}% is extremely positive. Market is over-leveraged long, crash likely. Avoiding long positions.",
                "weight": -0.3  # Negative weight to reduce long confidence
            }
        elif classification == "EXTREME_NEGATIVE":
            return {
                "classification": classification,
                "signal": "PRIORITIZE_LONG",
                "confidence": 0.8,
                "reasoning": f"Funding rate {funding_rate:.3f}% is extremely negative. Market is over-leveraged short, short-squeeze likely. Prioritizing long positions.",
                "weight": 0.3  # Positive weight to increase long confidence
            }
        else:
            return {
                "classification": classification,
                "signal": "NEUTRAL",
                "confidence": 0.0,
                "reasoning": f"Funding rate {funding_rate:.3f}% is neutral. No contrarian signal.",
                "weight": 0.0  # No weight adjustment
            }
    
    def adjust_signal_with_funding(self, technical_signal: Dict[str, Any], 
                                   funding_rate: float) -> Dict[str, Any]:
        """
        Adjust technical signal (RSI/MACD) with funding rate sentiment
        
        Args:
            technical_signal: Technical indicator signal with action and confidence
            funding_rate: Current funding rate as percentage
            
        Returns:
            Adjusted signal with funding rate sentiment applied
        """
        funding_sentiment = self.get_funding_sentiment(funding_rate)
        
        # Start with original signal
        adjusted_signal = technical_signal.copy()
        original_action = technical_signal.get("action", "HOLD")
        original_confidence = technical_signal.get("confidence", 0.5)
        
        # Apply funding rate logic
        if funding_sentiment["signal"] == "RESTRICT_LONG":
            # Restrict long trades
            if original_action == "BUY":
                # Reduce confidence for BUY signals when funding is extreme positive
                adjusted_signal["confidence"] = self._adjust_confidence(
                    original_confidence, 
                    funding_sentiment["weight"]
                )
                adjusted_signal["reason"] = f"{technical_signal.get('reason', 'Technical signal')} | FUNDING ALERT: {funding_sentiment['reasoning']}"
                
                # If confidence drops too low, convert to HOLD
                if adjusted_signal["confidence"] < self.CONFIDENCE_THRESHOLD:
                    adjusted_signal["action"] = "HOLD"
                    adjusted_signal["reason"] += " | Overridden to HOLD due to extreme positive funding."
                
                logger.info(f"🛑 Funding Rate Alert: Restricted LONG trade (funding: {funding_rate:.3f}%)")
            
            # NEW: Boost short confidence when funding is extreme positive
            elif original_action == "SELL":
                adjusted_signal["confidence"] = self._adjust_confidence(
                    original_confidence,
                    0.3  # Boost by 30%
                )
                adjusted_signal["reason"] = f"{technical_signal.get('reason', 'Technical signal')} | FUNDING BOOST: Over-leveraged longs, prioritizing short entry."
                logger.info(f"📈 Boosted SHORT confidence from {original_confidence:.2%} to {adjusted_signal['confidence']:.2%} (funding: {funding_rate:.4%})")
        
        elif funding_sentiment["signal"] == "PRIORITIZE_LONG":
            # Prioritize long trades
            if original_action == "BUY":
                # Boost confidence for BUY signals when funding is extreme negative
                adjusted_signal["confidence"] = self._adjust_confidence(
                    original_confidence,
                    funding_sentiment["weight"]
                )
                adjusted_signal["reason"] = f"{technical_signal.get('reason', 'Technical signal')} | FUNDING BOOST: {funding_sentiment['reasoning']}"
                logger.info(f"🚀 Funding Rate Alert: Prioritized LONG trade (funding: {funding_rate:.3f}%)")
            
            elif original_action == "HOLD" and original_confidence >= 0.4:
                # Upgrade HOLD to BUY if technical signal was borderline
                adjusted_signal["action"] = "BUY"
                adjusted_signal["confidence"] = 0.7
                adjusted_signal["reason"] = f"Upgraded from HOLD. {funding_sentiment['reasoning']}"
                logger.info(f"🚀 Funding Rate Alert: Upgraded HOLD to BUY (funding: {funding_rate:.3f}%)")
            
            elif original_action == "SELL":
                # Reduce confidence for SELL signals when short-squeeze is likely
                adjusted_signal["confidence"] = original_confidence * 0.7  # 30% reduction
                adjusted_signal["reason"] = f"{technical_signal.get('reason', 'Technical signal')} | FUNDING WARNING: {funding_sentiment['reasoning']}"
                
                if adjusted_signal["confidence"] < self.CONFIDENCE_THRESHOLD:
                    adjusted_signal["action"] = "HOLD"
                    adjusted_signal["reason"] += " | Overridden to HOLD due to short-squeeze risk."
        
        else:
            # Neutral funding - no adjustment needed
            adjusted_signal["funding_sentiment"] = funding_sentiment
        
        # Add funding context to the signal
        adjusted_signal["funding_rate"] = funding_rate
        adjusted_signal["funding_classification"] = funding_sentiment["classification"]
        
        return adjusted_signal
    
    def format_for_llm_prompt(self, funding_rate: float) -> str:
        """
        Format funding rate analysis for LLM prompt
        
        Args:
            funding_rate: Current funding rate as percentage
            
        Returns:
            Formatted string for LLM context
        """
        sentiment = self.get_funding_sentiment(funding_rate)
        
        return f"""[Funding Rate Analysis]:
Funding Rate: {funding_rate:.3f}%
Classification: {sentiment['classification']}
Signal: {sentiment['signal']}
Reasoning: {sentiment['reasoning']}

Contrarian Strategy Guidelines:
- Funding > 0.05%: Market over-leveraged LONG → Restrict long positions (crash risk)
- Funding < -0.05%: Market over-leveraged SHORT → Prioritize long positions (short-squeeze risk)
- Funding neutral: Follow standard technical analysis"""
