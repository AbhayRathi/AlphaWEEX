"""
Tests for Funding Rate Analyzer

Tests the contrarian sentiment analysis based on funding rates.
"""
import pytest
from core.funding_rate_analyzer import FundingRateAnalyzer


class TestFundingRateAnalyzer:
    """Test suite for FundingRateAnalyzer"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = FundingRateAnalyzer()
    
    def test_initialization(self):
        """Test analyzer initialization"""
        assert self.analyzer is not None
        assert self.analyzer.EXTREME_POSITIVE_THRESHOLD == 0.05
        assert self.analyzer.EXTREME_NEGATIVE_THRESHOLD == -0.05
    
    def test_classify_extreme_positive(self):
        """Test classification of extreme positive funding rate"""
        classification = self.analyzer.classify_funding_rate(0.06)
        assert classification == "EXTREME_POSITIVE"
        
        classification = self.analyzer.classify_funding_rate(0.1)
        assert classification == "EXTREME_POSITIVE"
    
    def test_classify_extreme_negative(self):
        """Test classification of extreme negative funding rate"""
        classification = self.analyzer.classify_funding_rate(-0.06)
        assert classification == "EXTREME_NEGATIVE"
        
        classification = self.analyzer.classify_funding_rate(-0.1)
        assert classification == "EXTREME_NEGATIVE"
    
    def test_classify_neutral(self):
        """Test classification of neutral funding rate"""
        classification = self.analyzer.classify_funding_rate(0.0)
        assert classification == "NEUTRAL"
        
        classification = self.analyzer.classify_funding_rate(0.03)
        assert classification == "NEUTRAL"
        
        classification = self.analyzer.classify_funding_rate(-0.03)
        assert classification == "NEUTRAL"
    
    def test_get_funding_sentiment_extreme_positive(self):
        """Test sentiment for extreme positive funding"""
        sentiment = self.analyzer.get_funding_sentiment(0.08)
        
        assert sentiment["classification"] == "EXTREME_POSITIVE"
        assert sentiment["signal"] == "RESTRICT_LONG"
        assert sentiment["confidence"] == 0.8
        assert "over-leveraged long" in sentiment["reasoning"]
        assert sentiment["weight"] == -0.3
    
    def test_get_funding_sentiment_extreme_negative(self):
        """Test sentiment for extreme negative funding"""
        sentiment = self.analyzer.get_funding_sentiment(-0.08)
        
        assert sentiment["classification"] == "EXTREME_NEGATIVE"
        assert sentiment["signal"] == "PRIORITIZE_LONG"
        assert sentiment["confidence"] == 0.8
        assert "short-squeeze" in sentiment["reasoning"]
        assert sentiment["weight"] == 0.3
    
    def test_get_funding_sentiment_neutral(self):
        """Test sentiment for neutral funding"""
        sentiment = self.analyzer.get_funding_sentiment(0.02)
        
        assert sentiment["classification"] == "NEUTRAL"
        assert sentiment["signal"] == "NEUTRAL"
        assert sentiment["confidence"] == 0.0
        assert sentiment["weight"] == 0.0
    
    def test_adjust_signal_restrict_long(self):
        """Test signal adjustment when funding restricts long trades"""
        # BUY signal with high confidence, but extreme positive funding
        technical_signal = {
            "action": "BUY",
            "confidence": 0.8,
            "reason": "Strong RSI oversold"
        }
        
        adjusted = self.analyzer.adjust_signal_with_funding(technical_signal, 0.07)
        
        # Confidence should be reduced or signal blocked
        # With extreme positive funding (0.07 > 0.05), BUY is BLOCKED
        assert adjusted["action"] == "HOLD"
        assert "BLOCKED by funding rate enforcement" in adjusted["reason"]
        assert adjusted["funding_rate"] == 0.07
        assert adjusted["funding_classification"] == "EXTREME_POSITIVE"
    
    def test_adjust_signal_prioritize_long(self):
        """Test signal adjustment when funding prioritizes long trades"""
        # BUY signal with medium confidence, extreme negative funding
        technical_signal = {
            "action": "BUY",
            "confidence": 0.65,
            "reason": "RSI oversold"
        }
        
        adjusted = self.analyzer.adjust_signal_with_funding(technical_signal, -0.08)
        
        # Confidence should be boosted
        assert adjusted["confidence"] > 0.65
        assert "FUNDING BOOST" in adjusted["reason"]
        assert adjusted["funding_rate"] == -0.08
        assert adjusted["funding_classification"] == "EXTREME_NEGATIVE"
    
    def test_adjust_signal_upgrade_hold_to_buy(self):
        """Test upgrading HOLD to BUY when extreme negative funding"""
        # HOLD signal with borderline confidence
        technical_signal = {
            "action": "HOLD",
            "confidence": 0.45,
            "reason": "Neutral conditions"
        }
        
        adjusted = self.analyzer.adjust_signal_with_funding(technical_signal, -0.09)
        
        # Should be upgraded to BUY
        assert adjusted["action"] == "BUY"
        assert adjusted["confidence"] == 0.7
        assert "Upgraded" in adjusted["reason"]
    
    def test_adjust_signal_override_to_hold(self):
        """Test overriding BUY to HOLD when extreme positive funding blocks trade"""
        # BUY signal with medium confidence
        technical_signal = {
            "action": "BUY",
            "confidence": 0.65,
            "reason": "Technical signal"
        }
        
        adjusted = self.analyzer.adjust_signal_with_funding(technical_signal, 0.1)
        
        # Should be blocked to HOLD due to extreme positive funding (0.1 > 0.05)
        assert adjusted["action"] == "HOLD"
        assert "BLOCKED by funding rate enforcement" in adjusted["reason"]
    
    def test_adjust_signal_neutral_funding(self):
        """Test that neutral funding doesn't affect signals"""
        technical_signal = {
            "action": "BUY",
            "confidence": 0.7,
            "reason": "Technical signal"
        }
        
        adjusted = self.analyzer.adjust_signal_with_funding(technical_signal, 0.02)
        
        # Signal should remain unchanged
        assert adjusted["action"] == "BUY"
        assert adjusted["confidence"] == 0.7
        assert adjusted["funding_rate"] == 0.02
        assert adjusted["funding_classification"] == "NEUTRAL"
    
    def test_format_for_llm_prompt(self):
        """Test formatting for LLM prompt"""
        prompt_text = self.analyzer.format_for_llm_prompt(0.08)
        
        assert "Funding Rate: 0.080%" in prompt_text
        assert "EXTREME_POSITIVE" in prompt_text
        assert "RESTRICT_LONG" in prompt_text
        assert "Contrarian Strategy Guidelines" in prompt_text
        assert "over-leveraged LONG" in prompt_text
    
    def test_format_for_llm_prompt_negative(self):
        """Test formatting for LLM prompt with negative funding"""
        prompt_text = self.analyzer.format_for_llm_prompt(-0.07)
        
        assert "Funding Rate: -0.070%" in prompt_text
        assert "EXTREME_NEGATIVE" in prompt_text
        assert "PRIORITIZE_LONG" in prompt_text
        assert "short-squeeze" in prompt_text
    
    def test_boundary_conditions(self):
        """Test boundary conditions at thresholds"""
        # Just below extreme positive threshold
        classification = self.analyzer.classify_funding_rate(0.049)
        assert classification == "NEUTRAL"
        
        # At extreme positive threshold
        classification = self.analyzer.classify_funding_rate(0.051)
        assert classification == "EXTREME_POSITIVE"
        
        # Just above extreme negative threshold
        classification = self.analyzer.classify_funding_rate(-0.049)
        assert classification == "NEUTRAL"
        
        # At extreme negative threshold
        classification = self.analyzer.classify_funding_rate(-0.051)
        assert classification == "EXTREME_NEGATIVE"
    
    def test_reduce_sell_confidence_on_negative_funding(self):
        """Test blocking SELL when extreme negative funding indicates short-squeeze risk"""
        # SELL signal with good confidence, but extreme negative funding
        technical_signal = {
            "action": "SELL",
            "confidence": 0.75,
            "reason": "Overbought RSI"
        }
        
        adjusted = self.analyzer.adjust_signal_with_funding(technical_signal, -0.08)
        
        # With extreme negative funding (-0.08 < -0.05), SELL should be BLOCKED
        assert adjusted["action"] == "HOLD"
        assert "BLOCKED by funding rate enforcement" in adjusted["reason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
