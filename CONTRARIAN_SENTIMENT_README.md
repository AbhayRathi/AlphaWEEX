# Contrarian Sentiment Analyst - Funding Rate Strategy

## Overview

The Contrarian Sentiment Analyst is a strategic trading feature that uses **Funding Rates** from perpetual futures contracts to identify over-leveraged market conditions and take contrarian positions. This feature gives the AlphaWEEX trading bot a strategic edge by detecting when the market is at risk of rapid reversals.

## What are Funding Rates?

Funding rates are periodic payments exchanged between long and short position holders in perpetual futures contracts. They help keep the futures price anchored to the spot price:

- **Positive Funding Rate**: Longs pay shorts → Market is over-leveraged LONG → Bullish sentiment is excessive
- **Negative Funding Rate**: Shorts pay longs → Market is over-leveraged SHORT → Bearish sentiment is excessive

## Contrarian Strategy Logic

### Extreme Positive Funding (> 0.05%)
**Market Condition**: Over-leveraged LONG positions  
**Risk**: Market crash/dump likely as longs get liquidated  
**Action**: **RESTRICT LONG trades**  
**Reasoning**: When funding is extremely positive, too many traders are long with leverage. This creates liquidation cascade risk. The bot restricts opening new long positions to avoid getting caught in the crash.

### Extreme Negative Funding (< -0.05%)
**Market Condition**: Over-leveraged SHORT positions  
**Risk**: Short-squeeze likely as shorts get liquidated  
**Action**: **PRIORITIZE LONG trades**  
**Reasoning**: When funding is extremely negative, too many traders are short with leverage. This creates short-squeeze potential. The bot prioritizes long positions to profit from forced short covering.

### Neutral Funding (-0.05% to 0.05%)
**Market Condition**: Balanced market  
**Action**: Follow standard technical analysis (RSI/MACD/SMA)  
**Reasoning**: No extreme leverage imbalance, so rely on normal technical indicators.

## Implementation Details

### 1. Funding Rate Analyzer (`core/funding_rate_analyzer.py`)

The core module that analyzes funding rates and provides sentiment signals:

```python
from core.funding_rate_analyzer import FundingRateAnalyzer

analyzer = FundingRateAnalyzer()

# Classify funding rate
classification = analyzer.classify_funding_rate(0.08)
# Returns: "EXTREME_POSITIVE", "EXTREME_NEGATIVE", or "NEUTRAL"

# Get detailed sentiment
sentiment = analyzer.get_funding_sentiment(0.08)
# Returns: {
#     "classification": "EXTREME_POSITIVE",
#     "signal": "RESTRICT_LONG",
#     "confidence": 0.8,
#     "reasoning": "Funding rate 0.080% is extremely positive...",
#     "weight": -0.3
# }

# Adjust technical signals with funding rate
tech_signal = {"action": "BUY", "confidence": 0.8, "reason": "RSI oversold"}
adjusted = analyzer.adjust_signal_with_funding(tech_signal, 0.08)
# Reduces confidence or overrides to HOLD if funding is extreme positive
```

### 2. WEEX API Integration (`core/weex_v2_client.py`)

Added `get_funding_rate()` method to fetch live funding rates from WEEX:

```python
client = WEEXv2Client(API_KEY, API_SECRET, API_PASSWORD)

# Get current funding rate for a symbol
funding_rate = client.get_funding_rate("cmt_btcusdt")
# Returns: funding rate as percentage (e.g., 0.045 for 0.045%)
```

### 3. Strategy Integration (`competition_bot.py`)

Modified `generate_signal()` to incorporate funding rate analysis:

```python
# 1. Fetch funding rate
funding_rate = self.client.get_funding_rate(symbol)

# 2. Generate base signal (LLM or RSI/SMA)
base_signal = generate_base_signal(klines, symbol)

# 3. Adjust signal with funding rate
adjusted_signal = self.funding_analyzer.adjust_signal_with_funding(
    base_signal, 
    funding_rate
)

# 4. Execute trade with adjusted confidence/action
```

### 4. LLM Integration (`core/strategy_engine.py`)

Updated prompts to include funding rate context for AI decision-making:

```python
def get_decision(self, symbol, klines, performance, balance, leverage, funding_rate):
    # Build prompt with funding rate analysis
    prompt = f"""
    ...
    [Funding Rate Analysis]:
    Funding Rate: {funding_rate:.3f}%
    Classification: {classification}
    
    CRITICAL: If funding > 0.05%, RESTRICT long trades (crash risk)
    CRITICAL: If funding < -0.05%, PRIORITIZE long trades (short-squeeze)
    ...
    """
```

## Signal Adjustment Examples

### Example 1: Restrict Long During Extreme Positive Funding

**Input:**
- Technical Signal: BUY with 0.80 confidence (RSI oversold)
- Funding Rate: 0.08% (Extreme Positive)

**Output:**
- Adjusted Signal: BUY with 0.56 confidence (reduced by 30%)
- Reasoning: "RSI oversold | FUNDING ALERT: Market over-leveraged long, crash likely"

**Effect:** Confidence drops below 0.65 threshold → Trade is NOT executed

### Example 2: Prioritize Long During Extreme Negative Funding

**Input:**
- Technical Signal: BUY with 0.65 confidence (Golden cross)
- Funding Rate: -0.08% (Extreme Negative)

**Output:**
- Adjusted Signal: BUY with 0.85 confidence (boosted by 30%)
- Reasoning: "Golden cross | FUNDING BOOST: Short-squeeze likely, prioritizing long"

**Effect:** Higher confidence → More aggressive position sizing

### Example 3: Upgrade HOLD to BUY During Short-Squeeze Setup

**Input:**
- Technical Signal: HOLD with 0.45 confidence (Neutral)
- Funding Rate: -0.09% (Extreme Negative)

**Output:**
- Adjusted Signal: BUY with 0.70 confidence
- Reasoning: "Upgraded from HOLD. Market over-leveraged short, short-squeeze likely"

**Effect:** Creates trade opportunity from neutral technical signal

## Weighting Against Technical Indicators

The funding rate sentiment is weighted against RSI/MACD signals using confidence adjustments:

| Scenario | Funding Rate | Technical Signal | Adjustment | Result |
|----------|--------------|------------------|------------|--------|
| Aligned | < -0.05% | BUY (0.70) | +30% boost | BUY (0.91) |
| Conflicting | > 0.05% | BUY (0.75) | -30% penalty | BUY (0.53) or HOLD |
| Neutral | -0.05 to 0.05% | BUY (0.70) | No change | BUY (0.70) |

### Confidence Thresholds

- **Execute BUY**: Confidence ≥ 0.65
- **Execute SELL**: Confidence ≥ 0.65
- **HOLD**: Confidence < 0.65

The funding rate analysis can:
1. **Boost** borderline signals above the threshold
2. **Reduce** strong signals below the threshold
3. **Override** action from BUY to HOLD if too risky

## Benefits

1. **Crash Avoidance**: Detects over-leveraged markets before liquidation cascades
2. **Short-Squeeze Capture**: Identifies opportunities to profit from forced covering
3. **Risk Management**: Adds an additional layer of market sentiment analysis
4. **Contrarian Edge**: Trades against the crowd when leverage is excessive
5. **AI-Enhanced**: LLM receives funding rate context for informed decision-making

## Testing

Comprehensive test suite with 16 tests covering:
- Funding rate classification (positive, negative, neutral)
- Sentiment generation
- Signal adjustment logic
- Edge cases and boundary conditions
- LLM prompt formatting

**Test Results**: ✅ 16/16 tests passing

Run tests:
```bash
pytest tests/test_funding_rate_analyzer.py -v
```

## Supported Trading Pairs

The feature works with all 8 competition pairs:
- BTC/USDT (cmt_btcusdt)
- ETH/USDT (cmt_ethusdt)
- SOL/USDT (cmt_solusdt)
- LTC/USDT (cmt_ltcusdt)
- ADA/USDT (cmt_adausdt)
- DOGE/USDT (cmt_dogeusdt)
- XRP/USDT (cmt_xrpusdt)
- BNB/USDT (cmt_bnbusdt)

## Configuration

Thresholds can be adjusted in `core/funding_rate_analyzer.py`:

```python
class FundingRateAnalyzer:
    # Funding rate thresholds
    EXTREME_POSITIVE_THRESHOLD = 0.05  # 0.05%
    EXTREME_NEGATIVE_THRESHOLD = -0.05  # -0.05%
```

## Integration with Existing Features

The Contrarian Sentiment Analyst integrates seamlessly with:

1. **LLM Strategy Engine**: Funding rate context included in AI prompts
2. **Behavioral Adversary**: Works alongside FOMO/Panic/Revenge detection
3. **Risk Management**: Respects existing TP/SL and kill-switch mechanisms
4. **AI Logging**: Funding rate signals logged with full reasoning
5. **Database Persistence**: Trade outcomes tracked with funding rate context

## Example Usage

```python
from core.funding_rate_analyzer import FundingRateAnalyzer
from core.weex_v2_client import WEEXv2Client

# Initialize
client = WEEXv2Client(API_KEY, API_SECRET, API_PASSWORD)
analyzer = FundingRateAnalyzer()

# Get funding rate
symbol = "cmt_btcusdt"
funding_rate = client.get_funding_rate(symbol)
print(f"Funding Rate: {funding_rate:.4f}%")

# Analyze sentiment
sentiment = analyzer.get_funding_sentiment(funding_rate)
print(f"Signal: {sentiment['signal']}")
print(f"Reasoning: {sentiment['reasoning']}")

# Generate technical signal (example)
technical_signal = {
    "action": "BUY",
    "confidence": 0.75,
    "reason": "RSI oversold at 28"
}

# Adjust with funding rate
final_signal = analyzer.adjust_signal_with_funding(technical_signal, funding_rate)
print(f"Final Action: {final_signal['action']}")
print(f"Final Confidence: {final_signal['confidence']:.2f}")
print(f"Final Reasoning: {final_signal['reason']}")
```

## Future Enhancements

Potential improvements:
1. Historical funding rate analysis (trends)
2. Adaptive thresholds based on volatility
3. Cross-exchange funding rate arbitrage detection
4. Funding rate momentum indicators
5. Multi-timeframe funding rate analysis

## References

- **Funding Rate Mechanics**: [Perpetual Futures Guide](https://www.binance.com/en/support/faq/360033525031)
- **WEEX API Documentation**: Check WEEX API docs for funding rate endpoints
- **Contrarian Trading**: Strategy based on identifying over-leveraged market conditions

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 2026-01-14
