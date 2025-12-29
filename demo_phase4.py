"""
Phase 4 Demo Script
Demonstrates Oracle, Sentiment Agent, and Position Sizing
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.oracle import TradFiOracle
from agents.perception import SentimentAgent
from architect import Architect
from guardrails import Guardrails
from data.shared_state import get_shared_state, RiskLevel


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def main():
    """Main demo function"""
    print_header("AlphaWEEX Phase 4 Demo")
    print("Global Oracle, Sentiment Perception, and Automated Testing")
    
    # Initialize components
    print("\n📦 Initializing components...")
    oracle = TradFiOracle()
    sentiment_agent = SentimentAgent()
    guardrails = Guardrails(
        initial_equity=1000.0,
        kill_switch_threshold=0.03,
        stability_lock_hours=12
    )
    architect = Architect(guardrails)
    shared_state = get_shared_state()
    
    # Demonstrate Oracle
    print_header("1. TradFi Oracle - Market Risk Assessment")
    print("\n🔍 Fetching market data from Alpaca API...")
    market_summary = oracle.get_market_summary()
    
    print(f"\n📊 Market Data:")
    market_data = market_summary['market_data']
    print(f"  SPY: ${market_data['spy']['price']:.2f} ({market_data['spy']['change_pct']:+.2f}%)")
    print(f"  QQQ: ${market_data['qqq']['price']:.2f} ({market_data['qqq']['change_pct']:+.2f}%)")
    print(f"  Source: {market_data['source']}")
    
    risk_level = oracle.update_global_risk()
    print(f"\n🚨 Global Risk Level: {risk_level}")
    print(f"  Threshold: SPY < {oracle.spy_threshold * 100:.1f}%")
    
    # Demonstrate Sentiment Agent
    print_header("2. Sentiment Agent - Market Sentiment Analysis")
    print("\n😱 Fetching Fear & Greed Index...")
    fear_greed = sentiment_agent.fetch_fear_greed_index()
    print(f"  Value: {fear_greed['value']}")
    print(f"  Classification: {fear_greed['classification']}")
    print(f"  Source: {fear_greed['source']}")
    
    print("\n📰 Fetching Bitcoin headlines...")
    headlines = sentiment_agent.fetch_bitcoin_news(5)
    for i, headline in enumerate(headlines, 1):
        print(f"  {i}. {headline}")
    
    print("\n💭 Analyzing sentiment...")
    multiplier = await sentiment_agent.update_sentiment()
    sentiment_summary = sentiment_agent.get_sentiment_summary()
    sentiment_info = sentiment_summary['data']
    
    print(f"\n  Sentiment: {sentiment_info['sentiment']}")
    print(f"  Multiplier: {multiplier:.2f}x")
    print(f"  Reasoning: {sentiment_info['reasoning']}")
    
    # Demonstrate Position Sizing
    print_header("3. Position Sizing Integration")
    print("\n💰 Calculating position sizes with different scenarios...\n")
    
    base_size = 100.0
    
    # Scenario 1: Normal conditions
    print("Scenario 1: Normal Market Conditions")
    shared_state.set_global_risk_level(RiskLevel.NORMAL)
    shared_state.set_sentiment_multiplier(1.0)
    size1 = architect.get_adjusted_size(base_size)
    print(f"  Base Size: ${base_size:.2f}")
    print(f"  Risk: NORMAL | Sentiment: 1.0x")
    print(f"  Final Size: ${size1:.2f}")
    
    # Scenario 2: Cautious sentiment
    print("\nScenario 2: Cautious Sentiment")
    shared_state.set_global_risk_level(RiskLevel.NORMAL)
    shared_state.set_sentiment_multiplier(0.7)
    size2 = architect.get_adjusted_size(base_size)
    print(f"  Base Size: ${base_size:.2f}")
    print(f"  Risk: NORMAL | Sentiment: 0.7x")
    print(f"  Final Size: ${size2:.2f}")
    reduction2 = ((size2 - base_size) / base_size) * 100
    print(f"  Reduction: {abs(reduction2):.1f}%")
    
    # Scenario 3: High risk
    print("\nScenario 3: High Risk Market")
    shared_state.set_global_risk_level(RiskLevel.HIGH)
    shared_state.set_sentiment_multiplier(1.0)
    size3 = architect.get_adjusted_size(base_size)
    print(f"  Base Size: ${base_size:.2f}")
    print(f"  Risk: HIGH | Sentiment: 1.0x")
    print(f"  Final Size: ${size3:.2f}")
    reduction3 = ((size3 - base_size) / base_size) * 100
    print(f"  Reduction: {abs(reduction3):.1f}%")
    
    # Scenario 4: Worst case (High risk + cautious sentiment)
    print("\nScenario 4: Worst Case (High Risk + Panicked Sentiment)")
    shared_state.set_global_risk_level(RiskLevel.HIGH)
    shared_state.set_sentiment_multiplier(0.5)
    size4 = architect.get_adjusted_size(base_size)
    print(f"  Base Size: ${base_size:.2f}")
    print(f"  Risk: HIGH | Sentiment: 0.5x")
    print(f"  Final Size: ${size4:.2f}")
    reduction4 = ((size4 - base_size) / base_size) * 100
    print(f"  Reduction: {abs(reduction4):.1f}%")
    
    # Summary
    print_header("Summary")
    state_snapshot = shared_state.get_all_state()
    print(f"\n📊 Current Global State:")
    print(f"  Risk Level: {state_snapshot['global_risk_level']}")
    print(f"  Sentiment Multiplier: {state_snapshot['sentiment_multiplier']:.2f}x")
    print(f"  Last Oracle Update: {state_snapshot['last_oracle_update']}")
    print(f"  Last Sentiment Update: {state_snapshot['last_sentiment_update']}")
    
    print("\n✅ Phase 4 Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("  ✓ TradFi Oracle monitoring SPY/QQQ with Alpaca API")
    print("  ✓ Sentiment analysis with Fear & Greed Index")
    print("  ✓ Dynamic position sizing based on risk and sentiment")
    print("  ✓ Safety override: 50% reduction when risk is HIGH")
    print("  ✓ Resilient fallback modes when APIs are unavailable")
    print("\nNext Steps:")
    print("  • View the dashboard: streamlit run dashboard/app.py")
    print("  • Run tests: pytest tests/test_phase4.py -v")
    print("  • Check logs for detailed reasoning traces")


if __name__ == "__main__":
    asyncio.run(main())
