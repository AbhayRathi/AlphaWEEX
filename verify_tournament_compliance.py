#!/usr/bin/env python3
"""
Manual verification script for tournament compliance features
Tests the key components without requiring full environment setup
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging_engine():
    """Test logging_engine module"""
    print("\n" + "="*60)
    print("Testing AILogEngine")
    print("="*60)
    
    from logging_engine import AILogEngine
    import tempfile
    import json
    
    # Create test engine
    test_dir = tempfile.mkdtemp()
    engine = AILogEngine(test_dir)
    
    # Test trade log generation
    log_path = engine.generate_trade_log(
        symbol="cmt_btcusdt",
        side="buy",
        size="0.001",
        leverage="20",
        model_version="GPT-4o-Competition-V1",
        ai_reasoning="Test reasoning",
        inputs={"rsi": 30.0, "funding_rate": 0.01}
    )
    
    print(f"✅ Trade log created: {log_path}")
    
    # Verify log content
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    print(f"✅ Log contains required fields:")
    for key in ["timestamp", "model_version", "inputs", "ai_reasoning", "order_details"]:
        assert key in log_data, f"Missing field: {key}"
        print(f"   - {key}: ✓")
    
    # Verify order details
    print(f"✅ Order details:")
    for key in ["symbol", "side", "size", "leverage"]:
        assert key in log_data["order_details"], f"Missing order_details field: {key}"
        print(f"   - {key}: {log_data['order_details'][key]}")
    
    # Test log count
    count = engine.get_trade_log_count()
    print(f"✅ Trade log count: {count}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    print("\n✅ AILogEngine tests PASSED")
    return True


def test_weex_client_updates():
    """Test WEEXv2Client updates"""
    print("\n" + "="*60)
    print("Testing WEEXv2Client Updates")
    print("="*60)
    
    # Check if close_all_positions method exists
    import inspect
    from core.weex_v2_client import WEEXv2Client
    
    methods = [name for name, _ in inspect.getmembers(WEEXv2Client, predicate=inspect.isfunction)]
    
    required_methods = ["close_all_positions", "cancel_all_orders"]
    for method in required_methods:
        if method in methods:
            print(f"✅ Method exists: {method}")
        else:
            print(f"❌ Missing method: {method}")
            return False
    
    print("\n✅ WEEXv2Client updates PASSED")
    return True


def test_competition_bot_attributes():
    """Test CompetitionTradingBot updates"""
    print("\n" + "="*60)
    print("Testing CompetitionTradingBot Updates")
    print("="*60)
    
    # Test if we can see the expected updates in the source
    with open("competition_bot.py", "r") as f:
        bot_source = f.read()
    
    with open("core/weex_v2_client.py", "r") as f:
        client_source = f.read()
    
    checks = [
        ("AILogEngine import", "from logging_engine import AILogEngine", bot_source),
        ("Trade counter", "self.valid_trade_count", bot_source),
        ("Minimum trades", "self.min_required_trades", bot_source),
        ("AI log engine init", "self.ai_log_engine = AILogEngine", bot_source),
        ("Auto-initialization", "def auto_initialize", bot_source),
        ("Frozen balance check", "def check_frozen_balance", bot_source),
        ("Leverage verification", "Tournament Compliance: Verify 20x leverage", bot_source),
        ("AI log generation", "self.ai_log_engine.generate_trade_log", bot_source),
        ("Self-healing error", "Error 40015", client_source),
    ]
    
    for name, pattern, source in checks:
        if pattern in source:
            print(f"✅ Found: {name}")
        else:
            print(f"❌ Missing: {name}")
            return False
    
    print("\n✅ CompetitionTradingBot updates PASSED")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TOURNAMENT COMPLIANCE VERIFICATION")
    print("="*60)
    
    results = []
    
    try:
        results.append(("AILogEngine", test_logging_engine()))
    except Exception as e:
        print(f"❌ AILogEngine test failed: {str(e)}")
        results.append(("AILogEngine", False))
    
    try:
        results.append(("WEEXv2Client", test_weex_client_updates()))
    except Exception as e:
        print(f"❌ WEEXv2Client test failed: {str(e)}")
        results.append(("WEEXv2Client", False))
    
    try:
        results.append(("CompetitionTradingBot", test_competition_bot_attributes()))
    except Exception as e:
        print(f"❌ CompetitionTradingBot test failed: {str(e)}")
        results.append(("CompetitionTradingBot", False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_passed = all(result for _, result in results)
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
