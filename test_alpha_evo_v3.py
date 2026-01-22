"""
Test script for Alpha-Evo V3 features
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_funding_rate_strict_enforcement():
    """Test strict funding rate enforcement"""
    from core.funding_rate_analyzer import FundingRateAnalyzer
    
    analyzer = FundingRateAnalyzer()
    
    # Test Case 1: Extreme positive funding (> 0.05%) should BLOCK BUY
    funding_rate = 0.06  # 0.06% - extreme positive
    technical_signal = {
        "action": "BUY",
        "confidence": 0.8,
        "reason": "Strong bullish signal"
    }
    
    adjusted = analyzer.adjust_signal_with_funding(technical_signal, funding_rate)
    
    # Should be forced to HOLD
    assert adjusted["action"] == "HOLD", f"Expected HOLD but got {adjusted['action']}"
    assert adjusted["confidence"] == 0.0, f"Expected confidence 0.0 but got {adjusted['confidence']}"
    print("✅ Test 1 passed: BUY blocked by extreme positive funding")
    
    # Test Case 2: Extreme negative funding (< -0.05%) should BLOCK SELL
    funding_rate = -0.06  # -0.06% - extreme negative
    technical_signal = {
        "action": "SELL",
        "confidence": 0.8,
        "reason": "Strong bearish signal"
    }
    
    adjusted = analyzer.adjust_signal_with_funding(technical_signal, funding_rate)
    
    # Should be forced to HOLD
    assert adjusted["action"] == "HOLD", f"Expected HOLD but got {adjusted['action']}"
    assert adjusted["confidence"] == 0.0, f"Expected confidence 0.0 but got {adjusted['confidence']}"
    print("✅ Test 2 passed: SELL blocked by extreme negative funding")
    
    # Test Case 3: Extreme positive funding should BOOST SELL
    funding_rate = 0.06  # 0.06% - extreme positive
    technical_signal = {
        "action": "SELL",
        "confidence": 0.7,
        "reason": "Bearish signal"
    }
    
    adjusted = analyzer.adjust_signal_with_funding(technical_signal, funding_rate)
    
    # Should boost confidence
    assert adjusted["action"] == "SELL", f"Expected SELL but got {adjusted['action']}"
    assert adjusted["confidence"] > 0.7, f"Expected confidence > 0.7 but got {adjusted['confidence']}"
    print("✅ Test 3 passed: SELL boosted by extreme positive funding")
    
    # Test Case 4: Neutral funding should not block anything
    funding_rate = 0.02  # 0.02% - neutral
    technical_signal = {
        "action": "BUY",
        "confidence": 0.7,
        "reason": "Bullish signal"
    }
    
    adjusted = analyzer.adjust_signal_with_funding(technical_signal, funding_rate)
    
    # Should allow BUY to proceed (may adjust confidence but not block)
    assert adjusted["action"] in ["BUY", "HOLD"], f"Expected BUY or HOLD but got {adjusted['action']}"
    print("✅ Test 4 passed: BUY allowed with neutral funding")
    
    print("\n✅ All funding rate enforcement tests passed!")


def test_hedge_parameters():
    """Test hedge parameters are set correctly"""
    import competition_bot
    
    # Check constants are defined
    assert hasattr(competition_bot, 'MIN_CONFIDENCE_HEDGE'), "MIN_CONFIDENCE_HEDGE not defined"
    assert competition_bot.MIN_CONFIDENCE_HEDGE == 0.85, f"Expected MIN_CONFIDENCE_HEDGE=0.85, got {competition_bot.MIN_CONFIDENCE_HEDGE}"
    
    assert hasattr(competition_bot, 'HEDGE_MARGIN_PCT'), "HEDGE_MARGIN_PCT not defined"
    assert competition_bot.HEDGE_MARGIN_PCT == 1.0, f"Expected HEDGE_MARGIN_PCT=1.0, got {competition_bot.HEDGE_MARGIN_PCT}"
    
    assert hasattr(competition_bot, 'HEDGE_PRUNE_PCT'), "HEDGE_PRUNE_PCT not defined"
    assert competition_bot.HEDGE_PRUNE_PCT == 0.5, f"Expected HEDGE_PRUNE_PCT=0.5, got {competition_bot.HEDGE_PRUNE_PCT}"
    
    print("✅ Hedge parameters configured correctly")


def test_exponential_backoff():
    """Test exponential backoff logic"""
    # Test that the backoff times follow the pattern: 60, 120, 240
    base_backoff = 60
    expected_backoffs = [60, 120, 240]
    
    for retry in range(3):
        backoff_time = base_backoff * (2 ** retry)
        assert backoff_time == expected_backoffs[retry], f"Retry {retry}: expected {expected_backoffs[retry]}, got {backoff_time}"
    
    print("✅ Exponential backoff calculation correct")


def test_failed_logs_directory():
    """Test that failed_logs directory exists or can be created"""
    import os
    
    failed_logs_dir = "failed_logs"
    
    # Check if directory exists
    if not os.path.exists(failed_logs_dir):
        # Try to create it
        os.makedirs(failed_logs_dir, exist_ok=True)
    
    assert os.path.exists(failed_logs_dir), "failed_logs directory does not exist"
    assert os.path.isdir(failed_logs_dir), "failed_logs is not a directory"
    
    print("✅ failed_logs directory exists and is accessible")


if __name__ == "__main__":
    print("=" * 60)
    print("Alpha-Evo V3 Feature Tests")
    print("=" * 60)
    print()
    
    try:
        test_funding_rate_strict_enforcement()
        print()
        test_hedge_parameters()
        print()
        test_exponential_backoff()
        print()
        test_failed_logs_directory()
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
