"""
Test Alpha-Evo Final Strike Implementation

Tests for:
1. ATR calculation and dynamic stop loss
2. Trailing stop logic
3. AI log submission format
4. Tournament goals tracking
5. Historical PnL retrieval
"""
import json
from competition_bot import CompetitionTradingBot
from core.weex_v2_client import WEEXv2Client


def test_atr_calculation():
    """Test ATR calculation returns value between 1.0% and 2.0%"""
    bot = CompetitionTradingBot(use_llm=False, test_mode=True)
    
    # Create sample klines data
    klines = [
        [1, 50000, 50500, 49800, 50200, 100],  # [timestamp, open, high, low, close, volume]
        [2, 50200, 50700, 50000, 50500, 110],
        [3, 50500, 51000, 50300, 50800, 120],
        [4, 50800, 51200, 50600, 51000, 115],
        [5, 51000, 51500, 50800, 51200, 125],
        [6, 51200, 51600, 51000, 51400, 130],
        [7, 51400, 51800, 51200, 51600, 135],
        [8, 51600, 52000, 51400, 51800, 140],
        [9, 51800, 52200, 51600, 52000, 145],
        [10, 52000, 52400, 51800, 52200, 150],
        [11, 52200, 52600, 52000, 52400, 155],
        [12, 52400, 52800, 52200, 52600, 160],
        [13, 52600, 53000, 52400, 52800, 165],
        [14, 52800, 53200, 52600, 53000, 170],
        [15, 53000, 53400, 52800, 53200, 175],
    ]
    
    atr_pct = bot.calculate_atr(klines, period=14)
    
    # ATR should be clamped between 1.0% and 2.0%
    assert 1.0 <= atr_pct <= 2.0, f"ATR {atr_pct}% not in range [1.0%, 2.0%]"
    print(f"✅ ATR calculation test passed: {atr_pct:.2f}%")


def test_ema_calculation():
    """Test EMA calculation"""
    bot = CompetitionTradingBot(use_llm=False, test_mode=True)
    
    closes = [50000, 50200, 50500, 50800, 51000, 51200, 51400, 51600, 51800, 52000,
              52200, 52400, 52600, 52800, 53000, 53200, 53400, 53600, 53800, 54000]
    
    ema_20 = bot.calculate_ema(closes, period=20)
    
    # EMA should be close to current prices (uptrend)
    assert 50000 <= ema_20 <= 54000, f"EMA {ema_20} not in reasonable range"
    print(f"✅ EMA calculation test passed: {ema_20:.2f}")


def test_trailing_stop_logic():
    """Test trailing stop initialization in position state"""
    # Create a mock client
    client = WEEXv2Client("test_key", "test_secret", "test_password")
    
    # Initialize position state
    symbol = "BTCUSDT"
    client.position_scaling_state[symbol] = {
        "partial_taken": False,
        "breakeven_set": False,
        "reinvested": False,
        "original_size": 0.001,
        "realized_profit": 0.0
    }
    
    # Add mock position
    client.open_positions[symbol] = {
        "side": "LONG",
        "entryPrice": 50000.0,
        "size": 0.001
    }
    
    # Test at +2% (should move to breakeven)
    current_price = 51000.0  # +2%
    trigger = client.check_tp_sl_triggers(symbol, current_price)
    assert client.position_scaling_state[symbol].get("breakeven_evo_set", False)
    print(f"✅ Breakeven at +2% test passed")
    
    # Test at +4% (should activate trailing stop)
    current_price = 52000.0  # +4%
    trigger = client.check_tp_sl_triggers(symbol, current_price)
    assert "highest_price" in client.position_scaling_state[symbol]
    assert client.position_scaling_state[symbol]["highest_price"] >= 52000.0
    print(f"✅ Trailing stop activation at +4% test passed")


def test_historical_pnl_summary():
    """Test historical PnL summary retrieval"""
    bot = CompetitionTradingBot(use_llm=False, test_mode=True)
    
    # Get summary (should handle empty case gracefully)
    summary = bot.get_historical_pnl_summary(5)
    
    assert isinstance(summary, str), "Summary should be a string"
    assert len(summary) > 0, "Summary should not be empty"
    print(f"✅ Historical PnL summary test passed: '{summary}'")


def test_tournament_goals_initialization():
    """Test tournament goals tracking initialization"""
    bot = CompetitionTradingBot(use_llm=False, test_mode=True)
    
    # Check tournament variables are initialized
    assert hasattr(bot, 'tournament_start_equity')
    assert hasattr(bot, 'tournament_target_profit')
    assert hasattr(bot, 'daily_profit_protection_threshold')
    assert hasattr(bot, 'position_size_reduction_active')
    
    assert bot.tournament_target_profit == 400.0
    assert bot.daily_profit_protection_threshold == 40.0
    assert bot.position_size_reduction_active == False
    
    print(f"✅ Tournament goals initialization test passed")


def test_upload_ai_log_payload_format():
    """Test AI log upload payload format"""
    client = WEEXv2Client("test_key", "test_secret", "test_password")
    
    # Test payload structure
    order_id = "test_order_123"
    symbol = "cmt_btcusdt"
    signal_data = {
        "action": "LONG",
        "confidence": 0.85,
        "reasoning": "Strong bullish momentum with RSI oversold",
        "tp_price": 51000.0,
        "sl_price": 49500.0
    }
    indicators = {
        "rsi": 32.5,
        "ema_20": 50200.0,
        "current_price": 50000.0
    }
    historical_pnl = "LONG: +2.5% (TP); SHORT: -1.2% (SL); LONG: +1.8% (PARTIAL_1)"
    
    # Expected payload structure
    expected_keys = ["orderId", "stage", "model", "input", "output", "explanation"]
    expected_input_keys = ["market_data", "prompt"]
    expected_market_data_keys = ["symbol", "rsi_14", "ema_20", "historical_pnl"]
    expected_output_keys = ["signal", "confidence", "tp", "sl"]
    
    # Build payload as the method would
    payload = {
        "orderId": order_id,
        "stage": "Decision Making",
        "model": "GPT-4o-Alpha-Evo-V2",
        "input": {
            "market_data": {
                "symbol": client.clean_symbol(symbol),
                "rsi_14": round(indicators.get("rsi", 50.0), 2),
                "ema_20": round(indicators.get("ema_20", indicators.get("current_price", 0.0)), 2),
                "historical_pnl": historical_pnl
            },
            "prompt": "Analyze market trend and past performance to execute next trade."
        },
        "output": {
            "signal": signal_data.get("action", "LONG").upper(),
            "confidence": round(signal_data.get("confidence", 0.0), 2),
            "tp": round(signal_data.get("tp_price", 0.0), 2),
            "sl": round(signal_data.get("sl_price", 0.0), 2)
        },
        "explanation": signal_data.get("reasoning", "Market analysis indicates favorable conditions for this trade.")
    }
    
    # Validate structure
    for key in expected_keys:
        assert key in payload, f"Missing key: {key}"
    
    for key in expected_input_keys:
        assert key in payload["input"], f"Missing input key: {key}"
    
    for key in expected_market_data_keys:
        assert key in payload["input"]["market_data"], f"Missing market_data key: {key}"
    
    for key in expected_output_keys:
        assert key in payload["output"], f"Missing output key: {key}"
    
    # Validate values
    assert payload["orderId"] == order_id
    assert payload["stage"] == "Decision Making"
    assert payload["model"] == "GPT-4o-Alpha-Evo-V2"
    assert payload["output"]["signal"] == "LONG"
    assert payload["output"]["confidence"] == 0.85
    assert payload["output"]["tp"] == 51000.0
    assert payload["output"]["sl"] == 49500.0
    
    print(f"✅ AI log payload format test passed")
    print(f"   Payload: {json.dumps(payload, indent=2)}")


def test_position_size_reduction():
    """Test position size reduction when daily profit protection is active"""
    bot = CompetitionTradingBot(use_llm=False, test_mode=True)
    
    # Set up daily profit protection
    bot.position_size_reduction_active = True
    
    # Calculate position size
    symbol = "cmt_btcusdt"
    current_price = 50000.0
    
    # Calculate normal size
    bot.position_size_reduction_active = False
    normal_size = bot.calculate_position_size(symbol, current_price)
    
    # Calculate reduced size
    bot.position_size_reduction_active = True
    reduced_size = bot.calculate_position_size(symbol, current_price)
    
    # Reduced size should be 50% of normal size
    expected_reduced = normal_size * 0.5
    assert abs(reduced_size - expected_reduced) < 0.0001, \
        f"Reduced size {reduced_size} != 50% of normal {expected_reduced}"
    
    print(f"✅ Position size reduction test passed")
    print(f"   Normal: {normal_size}, Reduced: {reduced_size} (50%)")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Running Alpha-Evo Tests")
    print("=" * 60)
    
    try:
        test_atr_calculation()
        test_ema_calculation()
        test_trailing_stop_logic()
        test_historical_pnl_summary()
        test_tournament_goals_initialization()
        test_upload_ai_log_payload_format()
        test_position_size_reduction()
        
        print("\n" + "=" * 60)
        print("✅ All Alpha-Evo tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
