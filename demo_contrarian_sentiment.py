#!/usr/bin/env python
"""
Demo: Contrarian Sentiment Analyst

This script demonstrates the funding rate analysis feature.
It shows how the bot adjusts trading signals based on extreme funding rates.
"""
import sys
from core.funding_rate_analyzer import FundingRateAnalyzer


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_funding_rate_analysis():
    """Demonstrate funding rate analysis"""
    print_section("Contrarian Sentiment Analyst - Demo")
    
    print("This demo shows how the bot uses funding rates to make contrarian trades.")
    print("Funding rates indicate market leverage imbalance:\n")
    print("  • Extreme Positive (>0.05%): Too many longs → Crash risk → RESTRICT LONG")
    print("  • Extreme Negative (<-0.05%): Too many shorts → Short-squeeze → PRIORITIZE LONG")
    print("  • Neutral (-0.05% to 0.05%): Balanced → Follow technical analysis\n")
    
    # Initialize analyzer
    analyzer = FundingRateAnalyzer()
    print("✅ Funding Rate Analyzer initialized\n")
    
    # Scenario 1: Extreme Positive Funding (Restrict Long)
    print_section("Scenario 1: Extreme Positive Funding (>0.05%)")
    
    funding_rate_1 = 0.08  # 0.08% - Market over-leveraged LONG
    print(f"📊 Funding Rate: {funding_rate_1:.3f}%")
    
    sentiment_1 = analyzer.get_funding_sentiment(funding_rate_1)
    print(f"🔍 Classification: {sentiment_1['classification']}")
    print(f"🚨 Signal: {sentiment_1['signal']}")
    print(f"💡 Reasoning: {sentiment_1['reasoning']}")
    
    # Technical signal: Strong BUY from RSI
    tech_signal_1 = {
        "action": "BUY",
        "confidence": 0.80,
        "reason": "RSI oversold at 25, strong volume"
    }
    print(f"\n📈 Technical Signal: {tech_signal_1['action']} (Confidence: {tech_signal_1['confidence']:.2%})")
    print(f"   Reason: {tech_signal_1['reason']}")
    
    # Adjust with funding rate
    adjusted_1 = analyzer.adjust_signal_with_funding(tech_signal_1, funding_rate_1)
    print(f"\n⚡ Adjusted Signal: {adjusted_1['action']} (Confidence: {adjusted_1['confidence']:.2%})")
    print(f"   Reason: {adjusted_1['reason']}")
    
    if adjusted_1['confidence'] < 0.65:
        print(f"\n❌ TRADE REJECTED: Confidence {adjusted_1['confidence']:.2%} < 65% threshold")
        print("   The funding rate alert prevented a potentially bad trade!")
    
    # Scenario 2: Extreme Negative Funding (Prioritize Long)
    print_section("Scenario 2: Extreme Negative Funding (<-0.05%)")
    
    funding_rate_2 = -0.09  # -0.09% - Market over-leveraged SHORT
    print(f"📊 Funding Rate: {funding_rate_2:.3f}%")
    
    sentiment_2 = analyzer.get_funding_sentiment(funding_rate_2)
    print(f"🔍 Classification: {sentiment_2['classification']}")
    print(f"🚀 Signal: {sentiment_2['signal']}")
    print(f"💡 Reasoning: {sentiment_2['reasoning']}")
    
    # Technical signal: Weak BUY from RSI
    tech_signal_2 = {
        "action": "BUY",
        "confidence": 0.60,
        "reason": "RSI slightly oversold at 35"
    }
    print(f"\n📈 Technical Signal: {tech_signal_2['action']} (Confidence: {tech_signal_2['confidence']:.2%})")
    print(f"   Reason: {tech_signal_2['reason']}")
    
    # Adjust with funding rate
    adjusted_2 = analyzer.adjust_signal_with_funding(tech_signal_2, funding_rate_2)
    print(f"\n⚡ Adjusted Signal: {adjusted_2['action']} (Confidence: {adjusted_2['confidence']:.2%})")
    print(f"   Reason: {adjusted_2['reason']}")
    
    if adjusted_2['confidence'] >= 0.65:
        print(f"\n✅ TRADE APPROVED: Confidence {adjusted_2['confidence']:.2%} ≥ 65% threshold")
        print("   The funding rate boost enabled a profitable trade!")
    
    # Scenario 3: Upgrade HOLD to BUY
    print_section("Scenario 3: Upgrade HOLD to BUY on Short-Squeeze Setup")
    
    funding_rate_3 = -0.10  # -0.10% - Very extreme negative
    print(f"📊 Funding Rate: {funding_rate_3:.3f}%")
    
    # Technical signal: HOLD with borderline confidence
    tech_signal_3 = {
        "action": "HOLD",
        "confidence": 0.45,
        "reason": "Neutral technical conditions"
    }
    print(f"\n📈 Technical Signal: {tech_signal_3['action']} (Confidence: {tech_signal_3['confidence']:.2%})")
    print(f"   Reason: {tech_signal_3['reason']}")
    
    # Adjust with funding rate
    adjusted_3 = analyzer.adjust_signal_with_funding(tech_signal_3, funding_rate_3)
    print(f"\n⚡ Adjusted Signal: {adjusted_3['action']} (Confidence: {adjusted_3['confidence']:.2%})")
    print(f"   Reason: {adjusted_3['reason']}")
    
    if adjusted_3['action'] == "BUY" and tech_signal_3['action'] == "HOLD":
        print(f"\n✨ SIGNAL UPGRADED: HOLD → BUY!")
        print("   The contrarian strategy identified a short-squeeze opportunity!")
    
    # Scenario 4: Neutral Funding (No Adjustment)
    print_section("Scenario 4: Neutral Funding (No Adjustment)")
    
    funding_rate_4 = 0.02  # 0.02% - Neutral
    print(f"📊 Funding Rate: {funding_rate_4:.3f}%")
    
    sentiment_4 = analyzer.get_funding_sentiment(funding_rate_4)
    print(f"🔍 Classification: {sentiment_4['classification']}")
    print(f"➡️  Signal: {sentiment_4['signal']}")
    
    # Technical signal: BUY
    tech_signal_4 = {
        "action": "BUY",
        "confidence": 0.70,
        "reason": "Golden cross detected"
    }
    print(f"\n📈 Technical Signal: {tech_signal_4['action']} (Confidence: {tech_signal_4['confidence']:.2%})")
    
    # Adjust with funding rate
    adjusted_4 = analyzer.adjust_signal_with_funding(tech_signal_4, funding_rate_4)
    print(f"⚡ Adjusted Signal: {adjusted_4['action']} (Confidence: {adjusted_4['confidence']:.2%})")
    
    print("\n✅ Signal unchanged - neutral funding allows technical analysis to lead")
    
    # Summary
    print_section("Summary: Why This Matters")
    
    print("The Contrarian Sentiment Analyst provides an edge by:")
    print("")
    print("1. 🛡️  CRASH AVOIDANCE")
    print("   Detects over-leveraged markets BEFORE liquidation cascades")
    print("")
    print("2. 🚀 SHORT-SQUEEZE CAPTURE")
    print("   Identifies opportunities to profit from forced short covering")
    print("")
    print("3. 🎯 SMART FILTERING")
    print("   Adjusts technical signals based on market leverage imbalance")
    print("")
    print("4. 🤖 AI-ENHANCED")
    print("   LLM receives funding rate context for informed decisions")
    print("")
    print("5. ⚖️  BALANCED APPROACH")
    print("   Weighs contrarian sentiment against RSI/MACD indicators")
    print("")
    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        demo_funding_rate_analysis()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
