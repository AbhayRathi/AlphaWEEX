"""
Phase 4 Integration Tests
Tests for Oracle, Sentiment Agent, Position Sizing, and Dashboard
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestSyntaxChecks:
    """Test that all new modules import correctly"""
    
    def test_import_shared_state(self):
        """Test SharedState module imports"""
        from data.shared_state import SharedState, RiskLevel, get_shared_state
        assert SharedState is not None
        assert RiskLevel is not None
        assert get_shared_state is not None
    
    def test_import_oracle(self):
        """Test Oracle module imports"""
        from core.oracle import TradFiOracle
        assert TradFiOracle is not None
    
    def test_import_perception(self):
        """Test Sentiment Agent module imports"""
        from agents.perception import SentimentAgent
        assert SentimentAgent is not None
    
    def test_architect_updated(self):
        """Test Architect has get_adjusted_size method"""
        from architect import Architect
        assert hasattr(Architect, 'get_adjusted_size')


class TestSharedState:
    """Test SharedState functionality"""
    
    def test_shared_state_singleton(self):
        """Test SharedState singleton pattern"""
        from data.shared_state import get_shared_state
        
        state1 = get_shared_state()
        state2 = get_shared_state()
        
        assert state1 is state2  # Should be same instance
    
    def test_risk_level_management(self):
        """Test global risk level management"""
        from data.shared_state import get_shared_state, RiskLevel
        
        state = get_shared_state()
        
        # Test setting and getting risk level
        state.set_global_risk_level(RiskLevel.HIGH)
        assert state.get_global_risk_level() == RiskLevel.HIGH
        
        state.set_global_risk_level(RiskLevel.NORMAL)
        assert state.get_global_risk_level() == RiskLevel.NORMAL
    
    def test_sentiment_multiplier(self):
        """Test sentiment multiplier management"""
        from data.shared_state import get_shared_state
        
        state = get_shared_state()
        
        # Test valid multiplier
        state.set_sentiment_multiplier(0.8)
        assert state.get_sentiment_multiplier() == 0.8
        
        # Test clamping to valid range
        state.set_sentiment_multiplier(2.0)  # Above max
        assert state.get_sentiment_multiplier() == 1.5  # Should be clamped
        
        state.set_sentiment_multiplier(0.1)  # Below min
        assert state.get_sentiment_multiplier() == 0.5  # Should be clamped


class TestTradFiOracle:
    """Test TradFi Oracle functionality"""
    
    def test_oracle_initialization(self):
        """Test Oracle initialization"""
        from core.oracle import TradFiOracle
        
        oracle = TradFiOracle()
        assert oracle is not None
        assert oracle.spy_threshold == -0.01
    
    def test_oracle_fallback_data(self):
        """Test Oracle fallback mode"""
        from core.oracle import TradFiOracle
        
        oracle = TradFiOracle()
        data = oracle._get_fallback_data()
        
        assert 'spy' in data
        assert 'qqq' in data
        assert 'timestamp' in data
        assert data['source'] == 'fallback'
    
    def test_oracle_risk_calculation_high(self):
        """Test Oracle sets HIGH risk when SPY drops > 1%"""
        from core.oracle import TradFiOracle
        from data.shared_state import get_shared_state, RiskLevel
        
        oracle = TradFiOracle()
        
        # Mock market data with SPY down 1.5%
        with patch.object(oracle, 'fetch_market_data') as mock_fetch:
            mock_fetch.return_value = {
                'timestamp': datetime.now().isoformat(),
                'spy': {
                    'price': 450.0,
                    'change_pct': -1.5,
                    'prev_price': 456.8
                },
                'qqq': {
                    'price': 380.0,
                    'change_pct': -1.2,
                    'prev_price': 384.6
                },
                'source': 'test'
            }
            
            risk = oracle.update_global_risk()
            
            assert risk == RiskLevel.HIGH
    
    def test_oracle_risk_calculation_normal(self):
        """Test Oracle sets NORMAL risk when SPY is stable"""
        from core.oracle import TradFiOracle
        from data.shared_state import get_shared_state, RiskLevel
        
        oracle = TradFiOracle()
        
        # Mock market data with SPY up 0.5%
        with patch.object(oracle, 'fetch_market_data') as mock_fetch:
            mock_fetch.return_value = {
                'timestamp': datetime.now().isoformat(),
                'spy': {
                    'price': 450.0,
                    'change_pct': 0.5,
                    'prev_price': 447.8
                },
                'qqq': {
                    'price': 380.0,
                    'change_pct': 0.7,
                    'prev_price': 377.4
                },
                'source': 'test'
            }
            
            risk = oracle.update_global_risk()
            
            assert risk == RiskLevel.NORMAL
    
    def test_oracle_error_handling(self):
        """Test Oracle defaults to NORMAL on error"""
        from core.oracle import TradFiOracle
        from data.shared_state import RiskLevel
        
        oracle = TradFiOracle()
        
        # Mock fetch to raise exception
        with patch.object(oracle, 'fetch_market_data', side_effect=Exception("API Error")):
            risk = oracle.update_global_risk()
            
            # Should default to NORMAL on error
            assert risk == RiskLevel.NORMAL


class TestSentimentAgent:
    """Test Sentiment Agent functionality"""
    
    def test_sentiment_agent_initialization(self):
        """Test Sentiment Agent initialization"""
        from agents.perception import SentimentAgent
        
        agent = SentimentAgent()
        assert agent is not None
    
    def test_fear_greed_fallback(self):
        """Test Fear & Greed fallback data"""
        from agents.perception import SentimentAgent
        
        agent = SentimentAgent()
        data = agent._get_fallback_fear_greed()
        
        assert data['value'] == 50
        assert data['classification'] == 'Neutral'
        assert data['source'] == 'fallback'
    
    def test_bitcoin_news_fetch(self):
        """Test Bitcoin news fetching"""
        from agents.perception import SentimentAgent
        
        agent = SentimentAgent()
        headlines = agent.fetch_bitcoin_news(count=5)
        
        assert len(headlines) == 5
        assert all(isinstance(h, str) for h in headlines)
    
    def test_rule_based_sentiment_euphoric(self):
        """Test rule-based sentiment for euphoric market"""
        from agents.perception import SentimentAgent
        
        agent = SentimentAgent()
        
        fear_greed = {
            'value': 85,  # Extreme Greed
            'classification': 'Extreme Greed'
        }
        headlines = ['Bitcoin surges to new highs', 'Bullish sentiment everywhere']
        
        result = agent._rule_based_sentiment(fear_greed, headlines)
        
        assert result['sentiment'] == 'Euphoric'
        assert 0.5 <= result['multiplier'] <= 0.8  # Should reduce exposure
    
    def test_rule_based_sentiment_panicked(self):
        """Test rule-based sentiment for panicked market"""
        from agents.perception import SentimentAgent
        
        agent = SentimentAgent()
        
        fear_greed = {
            'value': 15,  # Extreme Fear
            'classification': 'Extreme Fear'
        }
        headlines = ['Bitcoin crashes', 'Market panic spreads', 'Fear dominates']
        
        result = agent._rule_based_sentiment(fear_greed, headlines)
        
        assert result['sentiment'] == 'Panicked'
        assert 0.5 <= result['multiplier'] <= 0.8  # Should reduce exposure
    
    def test_rule_based_sentiment_neutral(self):
        """Test rule-based sentiment for neutral market"""
        from agents.perception import SentimentAgent
        
        agent = SentimentAgent()
        
        fear_greed = {
            'value': 50,  # Neutral
            'classification': 'Neutral'
        }
        headlines = ['Bitcoin holds steady', 'Markets remain balanced']
        
        result = agent._rule_based_sentiment(fear_greed, headlines)
        
        assert result['sentiment'] == 'Neutral'
        assert 0.9 <= result['multiplier'] <= 1.1  # Should maintain exposure


class TestPositionSizing:
    """Test position sizing integration"""
    
    def test_get_adjusted_size_normal(self):
        """Test position sizing with normal conditions"""
        from architect import Architect
        from data.shared_state import get_shared_state, RiskLevel
        from guardrails import Guardrails
        
        # Setup
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        architect = Architect(guardrails)
        
        state = get_shared_state()
        state.set_global_risk_level(RiskLevel.NORMAL)
        state.set_sentiment_multiplier(1.0)
        
        # Test
        base_size = 100.0
        adjusted = architect.get_adjusted_size(base_size)
        
        # Should be base_size * 1.0 (sentiment) = 100
        assert adjusted == 100.0
    
    def test_get_adjusted_size_with_sentiment(self):
        """Test position sizing with sentiment multiplier"""
        from architect import Architect
        from data.shared_state import get_shared_state, RiskLevel
        from guardrails import Guardrails
        
        # Setup
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        architect = Architect(guardrails)
        
        state = get_shared_state()
        state.set_global_risk_level(RiskLevel.NORMAL)
        state.set_sentiment_multiplier(0.8)  # Cautious sentiment
        
        # Test
        base_size = 100.0
        adjusted = architect.get_adjusted_size(base_size)
        
        # Should be base_size * 0.8 = 80
        assert adjusted == 80.0
    
    def test_get_adjusted_size_high_risk(self):
        """Test position sizing with HIGH risk"""
        from architect import Architect
        from data.shared_state import get_shared_state, RiskLevel
        from guardrails import Guardrails
        
        # Setup
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        architect = Architect(guardrails)
        
        state = get_shared_state()
        state.set_global_risk_level(RiskLevel.HIGH)
        state.set_sentiment_multiplier(1.0)
        
        # Test
        base_size = 100.0
        adjusted = architect.get_adjusted_size(base_size)
        
        # Should be base_size * 1.0 * 0.5 (HIGH risk reduction) = 50
        assert adjusted == 50.0
    
    def test_get_adjusted_size_combined_worst_case(self):
        """Test position sizing with both low sentiment and HIGH risk"""
        from architect import Architect
        from data.shared_state import get_shared_state, RiskLevel
        from guardrails import Guardrails
        
        # Setup
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        architect = Architect(guardrails)
        
        state = get_shared_state()
        state.set_global_risk_level(RiskLevel.HIGH)
        state.set_sentiment_multiplier(0.5)  # Very cautious sentiment
        
        # Test
        base_size = 100.0
        adjusted = architect.get_adjusted_size(base_size)
        
        # Should be base_size * 0.5 (sentiment) * 0.5 (HIGH risk) = 25
        assert adjusted == 25.0
        
        # Verify significant reduction
        reduction_pct = ((adjusted - base_size) / base_size) * 100
        assert reduction_pct == -75.0  # 75% reduction


class TestIntegration:
    """Integration tests for Phase 4 components"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: Oracle → Sentiment → Position Sizing"""
        from core.oracle import TradFiOracle
        from agents.perception import SentimentAgent
        from architect import Architect
        from data.shared_state import get_shared_state, RiskLevel
        from guardrails import Guardrails
        
        # Setup components
        oracle = TradFiOracle()
        sentiment_agent = SentimentAgent()
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        architect = Architect(guardrails)
        
        # Mock Oracle to return HIGH risk
        with patch.object(oracle, 'fetch_market_data') as mock_fetch:
            mock_fetch.return_value = {
                'timestamp': datetime.now().isoformat(),
                'spy': {'price': 450.0, 'change_pct': -1.5, 'prev_price': 456.8},
                'qqq': {'price': 380.0, 'change_pct': -1.2, 'prev_price': 384.6},
                'source': 'test'
            }
            
            # Step 1: Update Oracle
            risk = oracle.update_global_risk()
            assert risk == RiskLevel.HIGH
            
            # Step 2: Update Sentiment
            multiplier = await sentiment_agent.update_sentiment()
            assert 0.5 <= multiplier <= 1.5
            
            # Step 3: Calculate Position Size
            base_size = 100.0
            adjusted_size = architect.get_adjusted_size(base_size)
            
            # Verify: Should be significantly reduced due to HIGH risk
            # At minimum: base_size * sentiment * 0.5 (HIGH risk)
            assert adjusted_size <= base_size * 0.75  # At least 25% reduction


def test_case_sentiment_half_risk_high():
    """
    Case Test: Verify that if Sentiment is 0.5 and Risk is HIGH,
    the final position is significantly reduced
    """
    from architect import Architect
    from data.shared_state import get_shared_state, RiskLevel
    from guardrails import Guardrails
    
    # Setup
    guardrails = Guardrails(
        initial_equity=1000.0,
        kill_switch_threshold=0.03,
        stability_lock_hours=12
    )
    architect = Architect(guardrails)
    
    state = get_shared_state()
    
    # Set conditions: Sentiment 0.5, Risk HIGH
    state.set_sentiment_multiplier(0.5)
    state.set_global_risk_level(RiskLevel.HIGH)
    
    # Test with base size 100
    base_size = 100.0
    adjusted_size = architect.get_adjusted_size(base_size)
    
    # Expected: 100 * 0.5 (sentiment) * 0.5 (HIGH risk) = 25
    assert adjusted_size == 25.0
    
    # Verify significant reduction (75% reduction)
    reduction_pct = ((base_size - adjusted_size) / base_size) * 100
    assert reduction_pct == 75.0
    
    print(f"✅ Case Test Passed: Base ${base_size} → Final ${adjusted_size} ({reduction_pct:.0f}% reduction)")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
