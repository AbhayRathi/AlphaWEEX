"""
Demo script for Competition-Ready Trading Bot
Shows how to use the bot with mock/test data
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set test credentials for demo
os.environ['API_KEY'] = 'demo_key'
os.environ['API_SECRET'] = 'demo_secret'
os.environ['API_PASSWORD'] = 'demo_password'

from core.weex_v2_client import WEEXv2Client
from core.ai_logger import AITradingLogger


def demo_signature_generation():
    """Demo 1: Signature generation"""
    print("=" * 60)
    print("DEMO 1: Signature Generation")
    print("=" * 60)
    
    client = WEEXv2Client("test_key", "test_secret", "test_pass")
    
    timestamp = "1234567890000"
    method = "GET"
    path = "/capi/v2/market/candles"
    query = "?symbol=cmt_btcusdt&interval=1m&limit=100"
    body = ""
    
    signature = client.generate_signature(timestamp, method, path, query, body)
    
    print(f"✅ Timestamp: {timestamp}")
    print(f"✅ Method: {method}")
    print(f"✅ Path: {path}")
    print(f"✅ Query: {query}")
    print(f"✅ Signature: {signature}")
    print(f"✅ Signature Length: {len(signature)} characters")
    print()


def demo_tp_sl_calculation():
    """Demo 2: TP/SL Calculation"""
    print("=" * 60)
    print("DEMO 2: TP/SL Calculation")
    print("=" * 60)
    
    client = WEEXv2Client("test_key", "test_secret", "test_pass")
    
    # Simulate LONG position
    symbol = "cmt_btcusdt"
    entry_price = 50000
    
    client.open_positions[symbol] = {
        "entryPrice": str(entry_price),
        "side": "LONG",
        "size": "0.1"
    }
    
    print(f"📊 Position: LONG {symbol} @ ${entry_price}")
    print()
    
    # Test different price scenarios
    test_prices = [
        (51000, "2% gain (TP should trigger)"),
        (49500, "1% loss (SL should trigger)"),
        (50500, "1% gain (no trigger)"),
        (49800, "0.4% loss (no trigger)"),
    ]
    
    for price, description in test_prices:
        trigger = client.check_tp_sl_triggers(symbol, price)
        pct = ((price - entry_price) / entry_price) * 100
        emoji = "🎯" if trigger == "TP" else "🛑" if trigger == "SL" else "⏸️"
        print(f"{emoji} Price: ${price} ({pct:+.2f}%) - {description} → {trigger or 'No trigger'}")
    
    print()


def demo_ai_logger():
    """Demo 3: AI Logger"""
    print("=" * 60)
    print("DEMO 3: AI Trading Logger")
    print("=" * 60)
    
    # Create temporary log file
    log_file = "/tmp/demo_trading.log"
    logger = AITradingLogger(log_file)
    
    print(f"✅ Logger initialized: {log_file}")
    print()
    
    # Log various events
    print("📝 Logging events...")
    
    # 1. Heartbeat
    logger.force_heartbeat(
        market_data={"symbol": "cmt_btcusdt", "price": 50000, "rsi": 50},
        sentiment="RSI is 50, Neutral stance"
    )
    print("✅ Logged: HEARTBEAT")
    
    # 2. Trade decision
    logger.log_trade_decision(
        symbol="cmt_btcusdt",
        action="BUY",
        reason="RSI oversold at 25",
        confidence=0.75,
        indicators={"rsi": 25, "sma_20": 49000}
    )
    print("✅ Logged: TRADE_DECISION")
    
    # 3. Order execution
    logger.log_order_execution(
        symbol="cmt_btcusdt",
        side="BUY",
        size=0.001,
        price=50000,
        order_id="12345"
    )
    print("✅ Logged: ORDER_EXECUTION")
    
    # 4. TP trigger
    logger.log_tp_sl_trigger(
        symbol="cmt_btcusdt",
        trigger_type="TP",
        entry_price=50000,
        exit_price=51000,
        pnl_pct=2.0
    )
    print("✅ Logged: TP_TRIGGER")
    
    # 5. Error
    logger.log_error(
        error_type="521_ERROR",
        error_message="Firewall block detected",
        context={"symbol": "cmt_btcusdt"}
    )
    print("✅ Logged: ERROR")
    
    print()
    
    # Display stats
    stats = logger.get_log_stats()
    print("📊 Log Statistics:")
    print(f"   Total Lines: {stats['total_lines']}")
    print(f"   Heartbeats: {stats['heartbeats']}")
    print(f"   Trade Decisions: {stats['trade_decisions']}")
    print(f"   Order Executions: {stats['order_executions']}")
    print(f"   TP Triggers: {stats['tp_triggers']}")
    print(f"   Errors: {stats['errors']}")
    print()
    
    # Show log file contents
    print("📄 Log File Contents (JSON format):")
    print("-" * 60)
    with open(log_file, 'r') as f:
        for i, line in enumerate(f, 1):
            print(f"Line {i}: {line.strip()}")
    print("-" * 60)
    print()


def demo_rsi_calculation():
    """Demo 4: RSI Calculation"""
    print("=" * 60)
    print("DEMO 4: RSI Calculation")
    print("=" * 60)
    
    from competition_bot import CompetitionTradingBot
    
    bot = CompetitionTradingBot()
    
    # Test with trending data
    print("📈 Testing with uptrend data:")
    uptrend_prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116]
    rsi = bot.calculate_rsi(uptrend_prices, period=14)
    print(f"   Prices: {uptrend_prices[:5]}...{uptrend_prices[-3:]}")
    print(f"   RSI: {rsi:.2f} (Expected: > 50 for uptrend)")
    print()
    
    print("📉 Testing with downtrend data:")
    downtrend_prices = [100, 98, 96, 97, 95, 93, 94, 92, 90, 91, 89, 87, 88, 86, 84]
    rsi = bot.calculate_rsi(downtrend_prices, period=14)
    print(f"   Prices: {downtrend_prices[:5]}...{downtrend_prices[-3:]}")
    print(f"   RSI: {rsi:.2f} (Expected: < 50 for downtrend)")
    print()
    
    print("📊 Testing with oversold scenario:")
    oversold_prices = [100] + [95 - i for i in range(20)]
    rsi = bot.calculate_rsi(oversold_prices, period=14)
    print(f"   RSI: {rsi:.2f} (Expected: < 30 for oversold)")
    print()


def demo_signal_generation():
    """Demo 5: Signal Generation"""
    print("=" * 60)
    print("DEMO 5: Trading Signal Generation")
    print("=" * 60)
    
    from competition_bot import CompetitionTradingBot
    
    bot = CompetitionTradingBot()
    
    # Test BUY signal
    print("🟢 Testing BUY signal (Oversold RSI):")
    buy_indicators = {
        "valid": True,
        "current_price": 50000,
        "rsi": 25,
        "sma_20": 49000,
        "sma_50": 48000,
        "volume_ratio": 1.5
    }
    signal = bot.generate_signal(buy_indicators, "cmt_btcusdt")
    print(f"   Action: {signal['action']}")
    print(f"   Confidence: {signal['confidence']:.2%}")
    print(f"   Reason: {signal['reason']}")
    print()
    
    # Test SELL signal
    print("🔴 Testing SELL signal (Overbought RSI):")
    sell_indicators = {
        "valid": True,
        "current_price": 50000,
        "rsi": 76,
        "sma_20": 51000,
        "sma_50": 52000,
        "volume_ratio": 1.0
    }
    signal = bot.generate_signal(sell_indicators, "cmt_btcusdt")
    print(f"   Action: {signal['action']}")
    print(f"   Confidence: {signal['confidence']:.2%}")
    print(f"   Reason: {signal['reason']}")
    print()
    
    # Test HOLD signal
    print("⏸️ Testing HOLD signal (Neutral):")
    hold_indicators = {
        "valid": True,
        "current_price": 50000,
        "rsi": 50,
        "sma_20": 50000,
        "sma_50": 50000,
        "volume_ratio": 1.0
    }
    signal = bot.generate_signal(hold_indicators, "cmt_btcusdt")
    print(f"   Action: {signal['action']}")
    print(f"   Confidence: {signal['confidence']:.2%}")
    print(f"   Reason: {signal['reason']}")
    print()


def main():
    """Run all demos"""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  WEEX AI Trading Bot - Competition-Ready Demo  ".center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    print("\n")
    
    try:
        demo_signature_generation()
        demo_tp_sl_calculation()
        demo_ai_logger()
        demo_rsi_calculation()
        demo_signal_generation()
        
        print("=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        print()
        print("📚 Next Steps:")
        print("   1. Set up your API credentials in .env file")
        print("   2. Run the bot: python competition_bot.py")
        print("   3. Monitor logs: tail -f ai_trading.log | jq .")
        print("   4. Review documentation: COMPETITION_BOT_README.md")
        print()
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
