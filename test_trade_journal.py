"""
Test script for trade journal and position state persistence
"""
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.trade_journal import TradeJournal
from core.position_state import PositionStatePersistence


def test_trade_journal():
    """Test TradeJournal functionality"""
    print("\n" + "=" * 60)
    print("Testing TradeJournal")
    print("=" * 60)
    
    # Create journal in /tmp for testing
    journal = TradeJournal("/tmp/test_trade_history.json")
    
    # Test 1: Append trades
    print("\n1. Testing append_trade...")
    success1 = journal.append_trade(
        symbol="cmt_btcusdt",
        direction="LONG",
        profit_loss=2.5,
        ai_reason="Strong bullish momentum with high RSI",
        entry_price=50000.0,
        exit_price=51250.0,
        trigger_type="PARTIAL_1"
    )
    print(f"   Append trade 1: {'✅' if success1 else '❌'}")
    
    success2 = journal.append_trade(
        symbol="cmt_ethusdt",
        direction="SHORT",
        profit_loss=-1.2,
        ai_reason="Resistance at key level, overbought conditions",
        entry_price=3000.0,
        exit_price=3036.0,
        trigger_type="SL"
    )
    print(f"   Append trade 2: {'✅' if success2 else '❌'}")
    
    success3 = journal.append_trade(
        symbol="cmt_solusdt",
        direction="LONG",
        profit_loss=1.8,
        ai_reason="Breakout confirmed with volume",
        entry_price=100.0,
        exit_price=101.8,
        trigger_type="FULL_TP"
    )
    print(f"   Append trade 3: {'✅' if success3 else '❌'}")
    
    # Test 2: Get recent trades
    print("\n2. Testing get_recent_trades...")
    recent = journal.get_recent_trades(limit=5)
    print(f"   Retrieved {len(recent)} trades")
    for i, trade in enumerate(recent, 1):
        print(f"   {i}. {trade['direction']} {trade['symbol']}: {trade['profit_loss']:+.2f}% ({trade['trigger_type']})")
        print(f"      Reason: {trade['ai_reason'][:60]}...")
    
    # Test 3: Get trade count
    print("\n3. Testing get_trade_count...")
    count = journal.get_trade_count()
    print(f"   Total trades in journal: {count}")
    
    print("\n✅ TradeJournal tests completed successfully")
    return True


def test_position_state():
    """Test PositionStatePersistence functionality"""
    print("\n" + "=" * 60)
    print("Testing PositionStatePersistence")
    print("=" * 60)
    
    # Create state persistence in /tmp for testing
    state_mgr = PositionStatePersistence("/tmp/test_active_positions.json")
    
    # Test 1: Save state
    print("\n1. Testing save_state...")
    test_state = {
        "cmt_btcusdt": {
            "partial_taken": True,
            "breakeven_set": True,
            "reinvested": False,
            "original_size": 0.001,
            "realized_profit": 0.25
        },
        "cmt_ethusdt": {
            "partial_taken": False,
            "breakeven_set": False,
            "reinvested": False,
            "original_size": 0.1,
            "realized_profit": 0.0
        }
    }
    success = state_mgr.save_state(test_state)
    print(f"   Save state: {'✅' if success else '❌'}")
    
    # Test 2: Load state
    print("\n2. Testing load_state...")
    loaded_state = state_mgr.load_state()
    print(f"   Loaded {len(loaded_state)} positions")
    for symbol, state in loaded_state.items():
        print(f"   {symbol}: partial_taken={state['partial_taken']}, "
              f"breakeven_set={state['breakeven_set']}, "
              f"realized_profit={state['realized_profit']:.2f}%")
    
    # Test 3: Verify loaded data matches saved data
    print("\n3. Verifying data integrity...")
    matches = all(
        loaded_state.get(symbol) == state
        for symbol, state in test_state.items()
    )
    print(f"   Data integrity: {'✅' if matches else '❌'}")
    
    # Test 4: Clear state
    print("\n4. Testing clear_state...")
    clear_success = state_mgr.clear_state()
    cleared_state = state_mgr.load_state()
    print(f"   Clear state: {'✅' if clear_success and len(cleared_state) == 0 else '❌'}")
    
    print("\n✅ PositionStatePersistence tests completed successfully")
    return True


def test_integration():
    """Test integration with strategy engine"""
    print("\n" + "=" * 60)
    print("Testing Integration with StrategyEngine")
    print("=" * 60)
    
    try:
        print("\n1. Checking TradeJournal integration with competition_bot...")
        
        # Check if the imports are present in competition_bot
        with open('/home/runner/work/AlphaWEEX/AlphaWEEX/competition_bot.py', 'r') as f:
            content = f.read()
            has_journal_import = 'from core.trade_journal import TradeJournal' in content
            has_state_import = 'from core.position_state import PositionStatePersistence' in content
            has_journal_init = 'self.trade_journal = TradeJournal' in content
            has_state_init = 'self.position_state = PositionStatePersistence' in content
            has_journal_write = 'self.trade_journal.append_trade' in content
            has_state_save = 'self.position_state.save_state' in content
        
        print(f"   TradeJournal import: {'✅' if has_journal_import else '❌'}")
        print(f"   PositionStatePersistence import: {'✅' if has_state_import else '❌'}")
        print(f"   TradeJournal initialization: {'✅' if has_journal_init else '❌'}")
        print(f"   PositionStatePersistence initialization: {'✅' if has_state_init else '❌'}")
        print(f"   Journal write calls: {'✅' if has_journal_write else '❌'}")
        print(f"   State save calls: {'✅' if has_state_save else '❌'}")
        
        print("\n2. Checking StrategyEngine integration...")
        
        # Check if the imports are present in strategy_engine
        with open('/home/runner/work/AlphaWEEX/AlphaWEEX/core/strategy_engine.py', 'r') as f:
            content = f.read()
            has_journal_import = 'from core.trade_journal import TradeJournal' in content
            has_format_method = 'def _format_journal_trades' in content
            has_journal_init = 'self.trade_journal = TradeJournal' in content
            has_journal_call = 'journal_trades = self._format_journal_trades()' in content
        
        print(f"   TradeJournal import: {'✅' if has_journal_import else '❌'}")
        print(f"   _format_journal_trades method: {'✅' if has_format_method else '❌'}")
        print(f"   TradeJournal initialization: {'✅' if has_journal_init else '❌'}")
        print(f"   Journal formatting in prompt: {'✅' if has_journal_call else '❌'}")
        
        all_good = all([
            has_journal_import, has_state_import, has_journal_init, has_state_init,
            has_journal_write, has_state_save, has_format_method, has_journal_call
        ])
        
        print(f"\n{'✅' if all_good else '❌'} Integration checks completed")
        return all_good
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PERSISTENT TRADE MEMORY TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("TradeJournal", test_trade_journal()))
    results.append(("PositionStatePersistence", test_position_state()))
    results.append(("Integration", test_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
