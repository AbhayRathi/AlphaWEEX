"""
Full Stack Integration Tests
Tests the complete workflow from data fetch to execution
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from core.oracle import TradFiOracle
from agents.perception import SentimentAgent
from agents.narrative import NarrativePulse
from core.adversary import AdversarialAlpha
from core.shadow_engine import ShadowEngine
from architect import Architect
from guardrails import Guardrails
from data.shared_state import get_shared_state, RiskLevel


class TestGoldenPath:
    """Test the golden path: Data → Oracle → Narrative → Adversarial → Execution"""
    
    @pytest.mark.asyncio
    async def test_full_stack_workflow(self):
        """
        Integration test: Complete workflow from data fetch to execution
        
        Steps:
        1. Data Fetch (simulated)
        2. Oracle Check (TradFi risk assessment)
        3. Narrative Check (whale monitoring)
        4. Sentiment Check (Fear & Greed)
        5. Adversarial Audit (strategy validation)
        6. Position Sizing (risk-adjusted)
        7. Execution (simulated)
        """
        print("\n🔄 Testing Full Stack Golden Path...")
        
        # Step 1: Initialize components
        oracle = TradFiOracle()
        sentiment_agent = SentimentAgent()
        narrative = NarrativePulse()
        adversary = AdversarialAlpha()
        shadow_engine = ShadowEngine()
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        architect = Architect(guardrails)
        shared_state = get_shared_state()
        
        print("   ✅ All components initialized")
        
        # Step 2: Mock data fetch (OHLCV)
        market_data = {
            'timestamp': datetime.now().isoformat(),
            'open': 50000.0,
            'high': 51000.0,
            'low': 49500.0,
            'close': 50500.0,
            'volume': 150000.0,
            'price': 50500.0,
            'volume_24h': 150000.0,
            'price_change_pct': 1.0
        }
        print("   ✅ Market data fetched (simulated)")
        
        # Step 3: Oracle check (TradFi risk)
        with patch.object(oracle, 'fetch_market_data') as mock_fetch:
            mock_fetch.return_value = {
                'timestamp': datetime.now().isoformat(),
                'spy': {'price': 450.0, 'change_pct': 0.5, 'prev_price': 447.8},
                'qqq': {'price': 380.0, 'change_pct': 0.7, 'prev_price': 377.4},
                'source': 'test'
            }
            
            risk_level = oracle.update_global_risk()
            print(f"   ✅ Oracle check complete: Risk = {risk_level}")
        
        # Step 4: Narrative check (whale monitoring)
        narrative_result = narrative.monitor_narrative(market_data)
        print(f"   ✅ Narrative check complete: Sentiment = {narrative_result['overall_sentiment']}")
        
        # Step 5: Sentiment check
        sentiment_multiplier = await sentiment_agent.update_sentiment()
        print(f"   ✅ Sentiment check complete: Multiplier = {sentiment_multiplier:.2f}")
        
        # Step 6: Generate strategy
        strategy_code = """
def generate_signal(data):
    stop_loss = data['price'] * 0.95
    position_size = 100
    
    if data['rsi'] < 30:
        return {'action': 'buy', 'size': position_size, 'stop_loss': stop_loss}
    elif data['rsi'] > 70:
        return {'action': 'sell', 'size': position_size, 'stop_loss': stop_loss}
    return {'action': 'hold'}
"""
        print("   ✅ Strategy generated")
        
        # Step 7: Adversarial audit
        approved, audit_report = adversary.red_team_strategy(strategy_code)
        print(f"   ✅ Adversarial audit complete: Approved = {approved}")
        
        # Step 8: Position sizing with risk adjustments
        base_position_size = 100.0
        adjusted_size = architect.get_adjusted_size(base_position_size)
        print(f"   ✅ Position sizing complete: Base = ${base_position_size}, Adjusted = ${adjusted_size:.2f}")
        
        # Step 9: Shadow engine comparison
        shadow_result = shadow_engine.simulate_trade_pair(
            market_signal="buy",
            market_price=market_data['price'],
            market_volatility=0.02
        )
        print(f"   ✅ Shadow engine comparison: Shadow PnL = ${shadow_result['shadow_pnl']:.2f}, Live PnL = ${shadow_result['live_pnl']:.2f}")
        
        # Verify workflow completion
        assert risk_level in [RiskLevel.NORMAL, RiskLevel.HIGH]
        assert 0.5 <= sentiment_multiplier <= 1.5
        assert isinstance(approved, bool)
        assert adjusted_size <= base_position_size
        assert isinstance(shadow_result, dict)
        
        print("   ✅ Full stack workflow completed successfully!")


class TestKillSwitchEdgeCase:
    """Test kill-switch under rapid price drop"""
    
    def test_kill_switch_5_percent_drop(self):
        """
        Test kill-switch activation on 5% rapid price drop
        """
        from datetime import datetime, timedelta
        
        print("\n🛑 Testing Kill-Switch Edge Case...")
        
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,  # 3%
            stability_lock_hours=12
        )
        
        # Add history entry from 59 minutes ago (within 1 hour window)
        one_hour_ago = datetime.now() - timedelta(minutes=59)
        guardrails.equity_history.append({
            'timestamp': one_hour_ago,
            'equity': 1000.0
        })
        
        # Simulate 5% equity drop
        guardrails.current_equity = 950.0  # 5% drop from 1000
        equity_change_pct = ((guardrails.current_equity - 1000.0) / 1000.0)
        
        print(f"   Initial Equity (59m ago): $1000.0")
        print(f"   Current Equity: ${guardrails.current_equity}")
        print(f"   Change: {equity_change_pct:.2%}")
        
        # Check kill-switch (internal method)
        guardrails._check_kill_switch()
        kill_switch_active = guardrails.is_kill_switch_active()
        
        print(f"   Kill-Switch Threshold: {guardrails.kill_switch_threshold:.2%}")
        print(f"   Kill-Switch Active: {kill_switch_active}")
        
        # 5% drop should trigger kill-switch (threshold is 3%)
        assert kill_switch_active is True
        assert abs(equity_change_pct) > guardrails.kill_switch_threshold
        
        print("   ✅ Kill-switch triggered correctly on 5% drop!")
    
    def test_kill_switch_2_percent_drop(self):
        """Test kill-switch does NOT activate on 2% drop (below threshold)"""
        from datetime import datetime, timedelta
        
        print("\n✅ Testing Kill-Switch Below Threshold...")
        
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,  # 3%
            stability_lock_hours=12
        )
        
        # Add history entry from 59 minutes ago (within 1 hour window)
        one_hour_ago = datetime.now() - timedelta(minutes=59)
        guardrails.equity_history.append({
            'timestamp': one_hour_ago,
            'equity': 1000.0
        })
        
        # Simulate 2% equity drop (below threshold)
        guardrails.current_equity = 980.0  # 2% drop from 1000
        
        # Check kill-switch
        guardrails._check_kill_switch()
        kill_switch_active = guardrails.is_kill_switch_active()
        
        print(f"   Current Equity: ${guardrails.current_equity} (2% drop)")
        print(f"   Kill-Switch Active: {kill_switch_active}")
        
        # 2% drop should NOT trigger kill-switch (threshold is 3%)
        assert kill_switch_active is False
        
        print("   ✅ Kill-switch correctly stayed inactive on 2% drop!")


class TestHighRiskScenario:
    """Test behavior under high-risk market conditions"""
    
    @pytest.mark.asyncio
    async def test_high_risk_position_reduction(self):
        """
        Test that position sizes are significantly reduced under high-risk conditions
        """
        print("\n⚠️  Testing High-Risk Scenario...")
        
        # Setup
        oracle = TradFiOracle()
        sentiment_agent = SentimentAgent()
        narrative = NarrativePulse()
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        architect = Architect(guardrails)
        shared_state = get_shared_state()
        
        # Simulate high-risk conditions
        # 1. TradFi Oracle: SPY down > 1%
        with patch.object(oracle, 'fetch_market_data') as mock_fetch:
            mock_fetch.return_value = {
                'timestamp': datetime.now().isoformat(),
                'spy': {'price': 450.0, 'change_pct': -2.0, 'prev_price': 459.2},
                'qqq': {'price': 380.0, 'change_pct': -1.8, 'prev_price': 387.0},
                'source': 'test'
            }
            risk_level = oracle.update_global_risk()
        
        # 2. Sentiment: Extreme fear
        shared_state.set_sentiment_multiplier(0.5)
        
        # 3. Narrative: Whale inflow
        narrative.check_whale_inflow(exchange_inflow_btc=2000.0)
        
        print(f"   Risk Level: {risk_level}")
        print(f"   Sentiment Multiplier: {shared_state.get_sentiment_multiplier()}")
        print(f"   Whale Dump Risk: {narrative.get_whale_dump_risk()}")
        
        # Calculate position size
        base_size = 100.0
        adjusted_size = architect.get_adjusted_size(base_size)
        reduction_pct = ((base_size - adjusted_size) / base_size) * 100
        
        print(f"   Base Position Size: ${base_size}")
        print(f"   Adjusted Position Size: ${adjusted_size:.2f}")
        print(f"   Reduction: {reduction_pct:.1f}%")
        
        # Under high risk + low sentiment, position should be significantly reduced
        assert adjusted_size < base_size
        assert reduction_pct >= 50.0  # At least 50% reduction
        
        print(f"   ✅ Position size reduced by {reduction_pct:.1f}% under high-risk conditions!")


class TestEvolutionSafety:
    """Test evolution safety mechanisms"""
    
    def test_stability_lock(self):
        """Test that stability lock prevents frequent evolutions"""
        print("\n🔒 Testing Stability Lock...")
        
        guardrails = Guardrails(
            initial_equity=1000.0,
            kill_switch_threshold=0.03,
            stability_lock_hours=12
        )
        
        # Record an evolution
        guardrails.mark_evolution()
        
        # Check if evolution is allowed immediately after
        can_evolve_result = guardrails.can_evolve()
        
        print(f"   Last Evolution: {guardrails.last_evolution_time}")
        print(f"   Can Evolve Now: {can_evolve_result}")
        
        # Should not be allowed (stability lock active)
        assert can_evolve_result is False
        
        print("   ✅ Stability lock prevents immediate re-evolution!")


class TestErrorRecovery:
    """Test error recovery and safe mode"""
    
    @pytest.mark.asyncio
    async def test_api_failure_safe_mode(self):
        """Test that system degrades gracefully on API failures"""
        print("\n🛟 Testing Safe Mode on API Failure...")
        
        # Test Oracle fallback
        oracle = TradFiOracle(alpaca_api_key="invalid", alpaca_secret_key="invalid")
        
        # Should fall back to mock data without crashing
        risk_level = oracle.update_global_risk()
        
        print(f"   Oracle Status: Fallback mode")
        print(f"   Risk Level: {risk_level}")
        
        assert risk_level in [RiskLevel.NORMAL, RiskLevel.HIGH]
        
        # Test Sentiment Agent fallback
        sentiment_agent = SentimentAgent()
        sentiment_multiplier = await sentiment_agent.update_sentiment()
        
        print(f"   Sentiment Agent Status: Fallback mode")
        print(f"   Sentiment Multiplier: {sentiment_multiplier:.2f}")
        
        assert 0.5 <= sentiment_multiplier <= 1.5
        
        print("   ✅ System operates in safe mode without crashing!")


def test_complete_golden_path():
    """Run the complete golden path test"""
    test = TestGoldenPath()
    asyncio.run(test.test_full_stack_workflow())


def test_kill_switch_edge_case():
    """Run kill-switch edge case test"""
    test = TestKillSwitchEdgeCase()
    test.test_kill_switch_5_percent_drop()
    test.test_kill_switch_2_percent_drop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
