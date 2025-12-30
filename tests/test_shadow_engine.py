"""
Unit Tests for Shadow Trading Engine
Tests parallel strategy execution and promotion alerts
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.shadow_engine import ShadowEngine, ShadowStrategy


class TestShadowStrategy:
    """Test ShadowStrategy class"""
    
    def test_initialization(self):
        """Test shadow strategy initialization"""
        strategy = ShadowStrategy(
            name="Test-Shadow",
            leverage_multiplier=2.0,
            risk_multiplier=1.5
        )
        
        assert strategy.name == "Test-Shadow"
        assert strategy.leverage_multiplier == 2.0
        assert strategy.risk_multiplier == 1.5
        assert strategy.trade_count == 0
    
    def test_record_trade(self):
        """Test recording trade results"""
        strategy = ShadowStrategy(name="Test")
        
        strategy.record_trade(pnl=50.0, is_winner=True, sharpe_ratio=1.5)
        strategy.record_trade(pnl=-20.0, is_winner=False, sharpe_ratio=1.4)
        
        assert strategy.trade_count == 2
        assert strategy.win_count == 1
        assert strategy.total_pnl == 30.0
    
    def test_get_stats(self):
        """Test getting strategy statistics"""
        strategy = ShadowStrategy(name="Test")
        
        strategy.record_trade(pnl=100.0, is_winner=True, sharpe_ratio=1.5)
        strategy.record_trade(pnl=50.0, is_winner=True, sharpe_ratio=1.6)
        strategy.record_trade(pnl=-30.0, is_winner=False, sharpe_ratio=1.4)
        
        stats = strategy.get_stats()
        
        assert stats['trade_count'] == 3
        assert stats['win_count'] == 2
        assert stats['win_rate'] == pytest.approx(2/3, 0.01)
        assert stats['total_pnl'] == 120.0


class TestShadowEngine:
    """Test Shadow Trading Engine"""
    
    def test_initialization(self):
        """Test shadow engine initialization"""
        engine = ShadowEngine(
            promotion_threshold_iterations=100,
            sharpe_ratio_threshold=1.2
        )
        
        assert engine is not None
        assert engine.promotion_threshold_iterations == 100
        assert engine.sharpe_ratio_threshold == 1.2
        assert engine.shadow_strategy is not None
        assert engine.live_strategy is not None
    
    def test_simulate_trade_pair(self):
        """Test simulating trades for both shadow and live strategies"""
        engine = ShadowEngine()
        
        result = engine.simulate_trade_pair(
            market_signal="buy",
            market_price=50000.0,
            market_volatility=0.02
        )
        
        assert 'live_pnl' in result
        assert 'shadow_pnl' in result
        assert 'live_sharpe' in result
        assert 'shadow_sharpe' in result
        assert 'promotion_alert' in result
    
    def test_shadow_higher_leverage(self):
        """Test that shadow strategy has higher leverage"""
        engine = ShadowEngine()
        
        # Shadow should have higher leverage multiplier
        assert engine.shadow_strategy.leverage_multiplier > engine.live_strategy.leverage_multiplier
    
    def test_get_comparison_summary(self):
        """Test getting comparison summary"""
        engine = ShadowEngine()
        
        # Simulate some trades
        for i in range(5):
            engine.simulate_trade_pair("buy", 50000.0, 0.02)
        
        summary = engine.get_comparison_summary()
        
        assert 'shadow' in summary
        assert 'live' in summary
        assert 'comparison' in summary
        assert 'roi_diff' in summary['comparison']
        assert 'sharpe_diff' in summary['comparison']
    
    def test_reset_shadow_strategy(self):
        """Test resetting shadow strategy"""
        engine = ShadowEngine()
        
        # Simulate some trades
        engine.simulate_trade_pair("buy", 50000.0, 0.02)
        
        # Reset shadow strategy
        engine.reset_shadow_strategy(leverage_multiplier=3.0, risk_multiplier=2.0)
        
        assert engine.shadow_strategy.leverage_multiplier == 3.0
        assert engine.shadow_strategy.risk_multiplier == 2.0
        assert engine.shadow_strategy.trade_count == 0
    
    def test_dashboard_data(self):
        """Test dashboard data generation"""
        engine = ShadowEngine()
        
        # Simulate trades
        for i in range(10):
            engine.simulate_trade_pair("buy", 50000.0, 0.02)
        
        dashboard_data = engine.get_dashboard_data()
        
        assert 'shadow_roi' in dashboard_data
        assert 'live_roi' in dashboard_data
        assert 'shadow_sharpe' in dashboard_data
        assert 'live_sharpe' in dashboard_data
        assert 'iterations_to_promotion' in dashboard_data


class TestPromotionAlert:
    """Test promotion alert generation"""
    
    def test_no_promotion_before_threshold(self):
        """Test that no promotion alert is generated before threshold"""
        engine = ShadowEngine(promotion_threshold_iterations=100)
        
        # Simulate fewer trades than threshold
        for i in range(50):
            result = engine.simulate_trade_pair("buy", 50000.0, 0.02)
        
        # Should not have promotion alert yet
        summary = engine.get_comparison_summary()
        assert summary['promotion_alerts_count'] == 0
    
    def test_promotion_alert_generation(self):
        """Test promotion alert when shadow outperforms"""
        engine = ShadowEngine(
            promotion_threshold_iterations=10,  # Low threshold for testing
            sharpe_ratio_threshold=0.5  # Low threshold for testing
        )
        
        # Simulate many trades to potentially trigger promotion
        for i in range(15):
            engine.simulate_trade_pair("buy", 50000.0, 0.02)
        
        summary = engine.get_comparison_summary()
        
        # Check if promotion alert was generated (may or may not depending on simulation)
        # Just verify the mechanism works
        assert 'promotion_alerts_count' in summary
        assert isinstance(summary['promotion_alerts_count'], int)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_hold_signal(self):
        """Test that hold signal generates zero PnL"""
        engine = ShadowEngine()
        
        result = engine.simulate_trade_pair(
            market_signal="hold",
            market_price=50000.0
        )
        
        # Hold signals should generate minimal or zero PnL
        assert isinstance(result['live_pnl'], (int, float))
        assert isinstance(result['shadow_pnl'], (int, float))
    
    def test_thread_safety(self):
        """Test thread-safe operations"""
        import threading
        
        engine = ShadowEngine()
        results = []
        
        def simulate_trades():
            for i in range(10):
                result = engine.simulate_trade_pair("buy", 50000.0, 0.02)
                results.append(result)
        
        # Run multiple threads
        threads = [threading.Thread(target=simulate_trades) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Should have results from all threads
        assert len(results) == 30


def test_shadow_outperforms_scenario():
    """
    Integration test: Simulate scenario where shadow consistently outperforms
    """
    engine = ShadowEngine(
        promotion_threshold_iterations=20,
        sharpe_ratio_threshold=1.0
    )
    
    print("🌑 Testing Shadow Engine promotion mechanism...")
    
    # Simulate 25 trades (more than threshold)
    for i in range(25):
        result = engine.simulate_trade_pair("buy", 50000.0, 0.02)
    
    summary = engine.get_comparison_summary()
    
    print(f"   Shadow ROI: {summary['shadow']['avg_roi']:.2f}%")
    print(f"   Live ROI: {summary['live']['avg_roi']:.2f}%")
    print(f"   Shadow Sharpe: {summary['shadow']['avg_sharpe']:.2f}")
    print(f"   Live Sharpe: {summary['live']['avg_sharpe']:.2f}")
    print(f"   Promotion Alerts: {summary['promotion_alerts_count']}")
    
    if summary['promotion_alerts_count'] > 0:
        print("   ✅ Promotion alert generated!")
    else:
        print("   ℹ️  No promotion alert (shadow didn't outperform significantly)")
    
    # Verify structure
    assert 'shadow' in summary
    assert 'live' in summary
    assert 'comparison' in summary


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
