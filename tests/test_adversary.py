"""
Unit Tests for Adversarial Alpha
Tests the Red Team debate protocol and strategy validation
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.adversary import AdversarialAlpha


class TestAdversarialAlpha:
    """Test Adversarial Alpha functionality"""
    
    def test_initialization(self):
        """Test Adversarial Alpha initialization"""
        adversary = AdversarialAlpha()
        
        assert adversary is not None
        assert adversary.flash_crash_pct == -0.20
        assert adversary.max_drawdown_threshold == 0.15
        assert adversary.stop_loss_required is True
    
    def test_reject_strategy_without_stop_loss(self):
        """Test that strategy without stop-loss is rejected"""
        adversary = AdversarialAlpha(stop_loss_required=True)
        
        # Strategy code without stop-loss
        strategy_code = """
def generate_signal(data):
    if data['rsi'] < 30:
        return 'buy'
    elif data['rsi'] > 70:
        return 'sell'
    return 'hold'
"""
        
        approved, report = adversary.red_team_strategy(strategy_code)
        
        assert approved is False
        assert 'stop_loss_missing' in report['tests_failed']
        assert len(report['recommendations']) > 0
    
    def test_approve_strategy_with_stop_loss(self):
        """Test that strategy with stop-loss and risk management is approved"""
        adversary = AdversarialAlpha(stop_loss_required=True)
        
        # Strategy code with stop-loss and risk management
        strategy_code = """
def generate_signal(data, position_size=100):
    stop_loss = data['price'] * 0.95
    max_drawdown = 0.05
    
    if data['rsi'] < 30 and position_size < 1000:
        return 'buy'
    elif data['rsi'] > 70:
        return 'sell'
    
    # Check stop-loss
    if data['price'] < stop_loss:
        return 'emergency_exit'
    
    return 'hold'
"""
        
        approved, report = adversary.red_team_strategy(strategy_code)
        
        assert approved is True
        assert 'stop_loss_present' in report['tests_passed']
        assert 'flash_crash_survival' in report['tests_passed']
    
    def test_flash_crash_simulation(self):
        """Test flash crash simulation with defensive strategy"""
        adversary = AdversarialAlpha(flash_crash_pct=-0.20)
        
        # Strategy with multiple defensive mechanisms
        strategy_code = """
def trade(price):
    stop_loss = price * 0.95
    position_size = min(100, max_position_limit)
    risk_factor = calculate_risk(volatility)
    
    if drawdown > max_drawdown:
        return 'halt'
"""
        
        approved, report = adversary.red_team_strategy(strategy_code)
        
        # Check that flash crash test was performed
        assert 'flash_crash_survival' in report['tests_passed'] or 'flash_crash_failure' in report['tests_failed']
    
    def test_debate_protocol(self):
        """Test debate protocol between Architect and Auditor"""
        adversary = AdversarialAlpha()
        
        architect_proposal = """
def strategy(data):
    stop_loss = data['price'] * 0.98
    position_size = calculate_size(data['equity'])
    
    if data['signal'] == 'buy':
        return {'action': 'buy', 'size': position_size, 'stop_loss': stop_loss}
    return {'action': 'hold'}
"""
        
        architect_reasoning = "Strategy with stop-loss and position sizing"
        
        result = adversary.debate_protocol(
            architect_proposal,
            architect_reasoning
        )
        
        assert 'auditor_verdict' in result
        assert result['auditor_verdict'] in ['APPROVED', 'REJECTED']
        assert 'audit_report' in result
        assert 'consensus_reached' in result
    
    def test_audit_history(self):
        """Test audit history tracking"""
        adversary = AdversarialAlpha()
        
        # Perform multiple audits
        strategy1 = "def trade(): stop_loss = 0.95"
        strategy2 = "def trade(): return 'buy'"
        
        adversary.red_team_strategy(strategy1)
        adversary.red_team_strategy(strategy2)
        
        summary = adversary.get_audit_summary()
        
        assert summary['total_audits'] == 2
        assert 'approved' in summary
        assert 'rejected' in summary
        assert 'approval_rate' in summary
    
    def test_position_limits_detection(self):
        """Test detection of position limits in strategy"""
        adversary = AdversarialAlpha()
        
        strategy_with_limits = """
def trade(equity):
    max_position = equity * 0.1
    position_size = min(calculated_size, max_position)
    leverage_limit = 2.0
"""
        
        has_limits, details = adversary._check_position_limits(strategy_with_limits)
        
        assert has_limits is True
        assert len(details['keywords_found']) > 0
    
    def test_drawdown_monitoring_detection(self):
        """Test detection of drawdown monitoring"""
        adversary = AdversarialAlpha()
        
        strategy_with_drawdown = """
def monitor():
    current_drawdown = (peak - current) / peak
    max_drawdown = 0.10
    
    if current_drawdown > max_drawdown:
        halt_trading()
"""
        
        has_monitoring, details = adversary._check_drawdown_monitoring(strategy_with_drawdown)
        
        assert has_monitoring is True
        assert len(details['keywords_found']) > 0


class TestAdversarialEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_strategy(self):
        """Test handling of empty strategy code"""
        adversary = AdversarialAlpha()
        
        approved, report = adversary.red_team_strategy("")
        
        assert approved is False
        assert isinstance(report, dict)
    
    def test_malformed_strategy(self):
        """Test handling of malformed strategy code"""
        adversary = AdversarialAlpha()
        
        malformed_code = "def broken( incomplete"
        
        # Should not crash, should handle gracefully
        approved, report = adversary.red_team_strategy(malformed_code)
        
        assert isinstance(approved, bool)
        assert isinstance(report, dict)
    
    def test_custom_thresholds(self):
        """Test custom flash crash and drawdown thresholds"""
        adversary = AdversarialAlpha(
            flash_crash_pct=-0.30,  # -30%
            max_drawdown_threshold=0.20  # 20%
        )
        
        assert adversary.flash_crash_pct == -0.30
        assert adversary.max_drawdown_threshold == 0.20


def test_failing_strategy_scenario():
    """
    Integration test: Verify that a strategy with infinite drawdown risk is rejected
    """
    adversary = AdversarialAlpha()
    
    # Strategy that will fail flash crash test
    risky_strategy = """
def high_leverage_strategy(price):
    # High leverage without proper protections
    leverage = 10.0
    return {'action': 'buy', 'leverage': leverage}
"""
    
    approved, report = adversary.red_team_strategy(risky_strategy)
    
    # Should be rejected (either due to stop loss or flash crash)
    assert approved is False
    
    # Should have some failures
    assert len(report['tests_failed']) > 0
    
    # Should have recommendations
    assert len(report['recommendations']) > 0
    
    print(f"✅ Test passed: Risky strategy rejected")
    print(f"   Failures: {report['tests_failed']}")
    print(f"   Recommendations: {report['recommendations']}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
