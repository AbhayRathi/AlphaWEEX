"""
Demo: Enhanced Adversarial Alpha Agent
Demonstrates psychological bias detection and contrarian trading signals
"""
import logging
from core.adversary import AdversarialAlpha, test_adversary
from agents.narrative import NarrativePulse

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def demo_psychological_bias_detection():
    """
    Demo 1: Psychological Bias Detection
    """
    print("\n" + "="*70)
    print("🧠 DEMO 1: PSYCHOLOGICAL BIAS DETECTION")
    print("="*70)
    
    # Initialize adversary in heuristic mode (no API key needed)
    adversary = AdversarialAlpha(use_heuristic_mode=True)
    
    # Scenario 1: FOMO Chaser - Bull Trap
    print("\n📊 Scenario 1: FOMO Chaser (Bull Trap Warning)")
    print("-" * 70)
    fomo_data = {
        'price': 95000.0,
        'vwap': 90000.0,
        'price_change_pct': 5.5,
        'sentiment': 'extreme greed',
        'volume': 8000.0,
        'recent_prices': [88000, 89000, 90000, 92000, 94000, 95000] * 3
    }
    
    result = adversary.analyze_market(fomo_data)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Detected Bias: {result['detected_bias']}")
    print(f"Trap Prediction: {result['trap_prediction']}")
    print(f"Reasoning: {result['reasoning_path'][:150]}...")
    
    # Scenario 2: Panic Seller - Contrarian Buy
    print("\n📊 Scenario 2: Panic Seller (Mean Reversion Opportunity)")
    print("-" * 70)
    panic_data = {
        'price': 82000.0,
        'price_change_pct': -8.0,
        'sentiment': 'extreme fear',
        'volume': 12000.0,
        'recent_prices': [90000, 88000, 86000, 84000, 82000] * 4,
        'at_support': True
    }
    
    result = adversary.analyze_market(panic_data)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Detected Bias: {result['detected_bias']}")
    print(f"RSI: {result['rsi']:.2f}")
    print(f"Reasoning: {result['reasoning_path'][:150]}...")
    
    # Scenario 3: Trend Exhaustion - Recency Bias
    print("\n📊 Scenario 3: Trend Exhaustion (Recency Bias)")
    print("-" * 70)
    exhaustion_data = {
        'price': 98000.0,
        'price_change_pct': 1.5,
        'sentiment': 'greed',
        'volume': 5000.0,
        'recent_prices': [90000, 91000, 92500, 94000, 95500, 97000, 98000] * 3
    }
    
    result = adversary.analyze_market(exhaustion_data)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Detected Bias: {result['detected_bias']}")
    print(f"Reasoning: {result['reasoning_path'][:150]}...")


def demo_narrative_integration():
    """
    Demo 2: Narrative Pulse Integration
    """
    print("\n" + "="*70)
    print("📡 DEMO 2: NARRATIVE PULSE INTEGRATION")
    print("="*70)
    
    # Initialize components
    adversary = AdversarialAlpha(use_heuristic_mode=True)
    narrative = NarrativePulse(whale_threshold_btc=1000.0)
    
    # Simulate market with whale activity
    print("\n📊 Scenario: Whale Inflow + Price Dump")
    print("-" * 70)
    
    # First, check for whale activity
    market_data = {
        'price': 88000.0,
        'volume_24h': 150000.0,
        'price_change_pct': -6.0
    }
    
    narrative_result = narrative.monitor_narrative(market_data)
    print(f"\n🐋 Narrative Analysis:")
    print(f"   Overall Sentiment: {narrative_result['overall_sentiment']}")
    print(f"   Whale Dump Risk: {narrative_result['whale_dump_risk']}")
    print(f"   Signals Detected: {len(narrative_result['signals'])}")
    for signal in narrative_result['signals']:
        print(f"   - {signal['type']}: {signal['message']}")
    
    # Now analyze with adversary, including narrative data
    adversary_market_data = {
        'price': 88000.0,
        'price_change_pct': -6.0,
        'sentiment': 'fear',
        'volume': 5000.0,
        'recent_prices': [92000, 91000, 90000, 89000, 88000] * 4
    }
    
    result = adversary.analyze_market(
        adversary_market_data,
        narrative_data=narrative_result
    )
    
    print(f"\n🎯 Adversarial Analysis (with Narrative):")
    print(f"   Signal: {result['signal']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Detected Bias: {result['detected_bias']}")
    print(f"   Reasoning: {result['reasoning_path'][:200]}...")


def demo_shadow_mode_resilience():
    """
    Demo 3: Shadow Mode - Regional Block Resilience
    """
    print("\n" + "="*70)
    print("🌐 DEMO 3: SHADOW MODE - REGIONAL BLOCK RESILIENCE")
    print("="*70)
    
    adversary = AdversarialAlpha(use_heuristic_mode=True)
    
    print("\n📊 Simulating operation with Mock/Synthetic data")
    print("    (What happens when live APIs return Error 451)")
    print("-" * 70)
    
    # Simulate mock/synthetic data scenario
    import time
    current_time = int(time.time() * 1000)
    mock_ohlcv = []
    for i in range(30):
        # Create slightly varying synthetic data
        base_price = 90000.0
        variation = (i % 10 - 5) * 50  # Small variations
        mock_ohlcv.append([
            current_time - (i * 900000),  # 15m intervals
            base_price + variation,
            base_price + variation + 200,
            base_price + variation - 200,
            base_price + variation + 50,
            1.5
        ])
    mock_ohlcv = sorted(mock_ohlcv, key=lambda x: x[0])
    
    mock_data = {
        'price': 90000.0,
        'price_change_pct': 0.3,
        'sentiment': 'neutral',
        'volume': 1.5,
        'source': 'SHADOW_MOCK'
    }
    
    start = time.time()
    result = adversary.analyze_market(mock_data, ohlcv_data=mock_ohlcv)
    elapsed = time.time() - start
    
    print(f"✅ Analysis completed with synthetic data")
    print(f"   Response Time: {elapsed:.3f}s (target: <1s)")
    print(f"   Signal: {result['signal']}")
    print(f"   Mode: {result.get('mode', 'UNKNOWN')}")
    print(f"   Status: Agent continues to function normally")
    print(f"\n💡 Key Point: Agent never 'goes blind' - falls back to mock data")
    print(f"   and continues reasoning loop for testing/development")


def demo_red_team_validation():
    """
    Demo 4: Red Team Strategy Validation (Legacy Feature)
    """
    print("\n" + "="*70)
    print("🔴 DEMO 4: RED TEAM STRATEGY VALIDATION")
    print("="*70)
    
    adversary = AdversarialAlpha()
    
    # Example 1: Risky strategy (should be rejected)
    print("\n📊 Example 1: Risky Strategy (No Stop-Loss)")
    print("-" * 70)
    risky_strategy = """
def aggressive_strategy(data):
    # High leverage, no protection
    leverage = 10.0
    if data['rsi'] < 40:
        return {'action': 'buy', 'leverage': leverage}
    return {'action': 'hold'}
"""
    
    approved, report = adversary.red_team_strategy(risky_strategy)
    print(f"Verdict: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    print(f"Tests Passed: {len(report['tests_passed'])}")
    print(f"Tests Failed: {len(report['tests_failed'])}")
    if report['recommendations']:
        print(f"Recommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    # Example 2: Safe strategy (should be approved)
    print("\n📊 Example 2: Safe Strategy (With Protections)")
    print("-" * 70)
    safe_strategy = """
def defensive_strategy(data):
    stop_loss = data['price'] * 0.95
    position_size = min(100, data['equity'] * 0.05)
    max_drawdown = 0.08
    risk_per_trade = 0.02
    
    if data['drawdown'] > max_drawdown:
        return {'action': 'halt'}
    
    if data['rsi'] < 30 and position_size < 1000:
        return {'action': 'buy', 'size': position_size, 'stop_loss': stop_loss}
    
    return {'action': 'hold'}
"""
    
    approved, report = adversary.red_team_strategy(safe_strategy)
    print(f"Verdict: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    print(f"Tests Passed: {len(report['tests_passed'])}")
    print(f"Tests Failed: {len(report['tests_failed'])}")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("🚀 ENHANCED ADVERSARIAL ALPHA - DEMONSTRATION SUITE")
    print("="*70)
    
    # Run demos
    demo_psychological_bias_detection()
    demo_narrative_integration()
    demo_shadow_mode_resilience()
    demo_red_team_validation()
    
    # Run test suite
    print("\n" + "="*70)
    print("🧪 RUNNING COMPREHENSIVE TEST SUITE")
    print("="*70)
    test_adversary()
    
    print("\n" + "="*70)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*70)
    print("\n📚 Key Features Demonstrated:")
    print("   1. ✅ Psychological Bias Detection (FOMO, Panic, Exhaustion)")
    print("   2. ✅ Narrative Pulse Integration (Whale Activity, News)")
    print("   3. ✅ Shadow Mode Resilience (451 Error Recovery)")
    print("   4. ✅ Red Team Validation (Strategy Safety Checks)")
    print("   5. ✅ Heuristic Mode (Works without API keys)")
    print("   6. ✅ DeepSeek-V3 Ready (LLM integration available)")
    print("\n💡 Next Steps:")
    print("   - Set DEEPSEEK_API_KEY in .env for LLM-powered analysis")
    print("   - Integrate with live trading system")
    print("   - Monitor signal history for performance tracking")


if __name__ == "__main__":
    main()
