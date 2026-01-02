# Enhanced Adversarial Agent Documentation

## Overview

The Enhanced Adversarial Alpha agent ("The Alpha") is a behavioral economics-based trading agent that identifies where human traders make emotional mistakes (FOMO, Panic, Fatigue) and predicts liquidity traps where whales hunt retail stop-losses.

## Core Mission

**Act as a "Contrarian Predator"** - Instead of following standard technical indicators, this agent analyzes market data through human psychological bias archetypes to generate contrarian trading signals.

## Key Features

### 1. Psychological Bias Detection

The agent detects four primary human bias archetypes:

#### The FOMO Chaser
- **Detection Logic**: Price > 5% above 1-hour VWAP
- **Signal**: Bull Trap Warning (SELL signal)
- **Confidence Boost**: Increases with "extreme greed" sentiment or rapid price rises (>3%)
- **Example**: BTC at $95,000 with VWAP at $90,000 → SELL signal (64% confidence)

#### The Panic Seller
- **Detection Logic**: RSI < 25 + "Extreme Fear" sentiment
- **Signal**: Mean Reversion Opportunity (BUY signal)
- **Confidence Boost**: Increases when at support levels or price drops >5%
- **Example**: BTC at $82,000 with RSI 22 + Extreme Fear → BUY signal (70% confidence)

#### The Liquidity Hunter
- **Detection Logic**: Identifies stop-loss clusters 0.5% below recent swing lows
- **Signal**: Predicts "wick" to trap zone
- **Use Case**: Helps avoid getting stopped out at obvious levels
- **Example**: Swing low at $89,000 → Trap predicted at $88,555

#### Recency Bias / Trend Exhaustion
- **Detection Logic**: 3+ consecutive days in same direction
- **Signal**: Reversal warning (contrarian signal)
- **Confidence**: Scales with trend length
- **Example**: 4-day uptrend → SELL signal (trend exhaustion likely)

### 2. AI Brain: DeepSeek-V3 Integration

#### Chain-of-Thought Reasoning
The agent uses structured prompting to get LLM-powered analysis:

```
1. What emotional mistake are retail traders making right now?
2. Are they chasing FOMO into a bull trap, or panic selling into capitulation?
3. Where would whales place liquidity traps to hunt stop-losses?
4. What is the contrarian play that profits from human psychology?
```

#### Rate Limiting Logic
LLM calls are triggered ONLY when:
- Volatility > 1.5% in 15-minute period, OR
- High-impact narrative event detected (regulatory news, whale activity)

Otherwise, uses local heuristic math (RSI/Bollinger/VWAP) to save tokens.

#### Output Format
Strictly returns JSON with required fields:
```json
{
  "signal": "BUY|SELL|HOLD",
  "confidence": 0.75,
  "detected_bias": "FOMO_CHASER|PANIC_SELLER|LIQUIDITY_HUNTER|RECENCY_BIAS|NONE",
  "trap_prediction": "Description of predicted trap or opportunity",
  "reasoning_path": "Step-by-step psychological reasoning"
}
```

### 3. US-Compatible Shadow Mode

#### Regional Block Recovery (Error 451)
- **CCXT Fallback**: Defaults to `binanceus` if primary exchange blocked
- **Shadow Mock Mode**: Generates synthetic OHLCV data (baseline $90k BTC) when live data unavailable
- **Mock Portfolio**: Returns 10,000 USDT balance if `fetch_balance` blocked
- **Recovery Time**: <1 second switch to mock data

#### Benefits
- Agent never "goes blind" due to regional restrictions
- Reasoning loop continues functioning for testing/development
- Graceful degradation ensures system stays operational

### 4. Narrative Pulse Integration

#### Sentiment Fusion
Takes inputs from `narrative_pulse.py`:
- Whale activity monitoring
- News/regulatory events
- Overall market sentiment (Fear/Greed)

#### Contextual Logic
- **Regulatory News**: Increases panic score regardless of chart technicals
- **Whale Inflows**: Adjusts confidence on buy signals
- **High Impact Events**: Triggers LLM analysis even at low volatility

Example:
```python
# Regulatory crackdown news detected
if 'regulatory' in news.lower():
    panic_score += 0.3  # Increase panic detection
    trigger_llm = True  # Force detailed analysis
```

### 5. Security & Environment Variables

#### Zero-Leak Policy
- All API keys loaded via `os.getenv()` from `.env` file
- No hardcoded credentials in source code
- Sanitization removes server metadata before external API calls

#### Graceful Failure
```python
# If DEEPSEEK_API_KEY missing
if not api_key:
    switch_to_heuristic_mode()  # Don't crash
```

#### Data Sanitization
Before sending to external APIs:
- Strip file paths: `/home/user/...` → `[PATH]`
- Remove IPs: `192.168.1.1` → `[IP]`
- Clean sensitive metadata

## Usage Examples

### Basic Usage (Heuristic Mode)

```python
from core.adversary import AdversarialAlpha

# Initialize without API key (heuristic mode)
adversary = AdversarialAlpha(use_heuristic_mode=True)

# Analyze market data
market_data = {
    'price': 90000.0,
    'price_change_pct': -5.0,
    'sentiment': 'extreme fear',
    'volume': 5000.0,
    'recent_prices': [95000, 93000, 91000, 89000, 87000, 90000] * 3
}

result = adversary.analyze_market(market_data)

print(f"Signal: {result['signal']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Detected Bias: {result['detected_bias']}")
print(f"Reasoning: {result['reasoning_path']}")
```

### Advanced Usage (With LLM + Narrative)

```python
from core.adversary import AdversarialAlpha
from agents.narrative import NarrativePulse
import os

# Initialize with DeepSeek API
adversary = AdversarialAlpha(
    deepseek_api_key=os.getenv('DEEPSEEK_API_KEY'),
    volatility_threshold=1.5
)

# Initialize narrative monitor
narrative = NarrativePulse(whale_threshold_btc=1000.0)

# Get narrative data
narrative_data = narrative.monitor_narrative({
    'price': 88000.0,
    'volume_24h': 150000.0,
    'price_change_pct': -6.0
})

# Analyze with narrative context
result = adversary.analyze_market(
    market_data={
        'price': 88000.0,
        'price_change_pct': -6.0,
        'sentiment': 'fear',
        'volume': 5000.0
    },
    narrative_data=narrative_data
)

# High volatility triggers LLM analysis
if result.get('mode') == 'LLM':
    print("🤖 DeepSeek-V3 analysis used")
else:
    print("📊 Heuristic analysis used")
```

### With OHLCV Data

```python
# Fetch OHLCV from exchange or use mock data
ohlcv_data = [
    [timestamp, open, high, low, close, volume],
    # ... more candles
]

result = adversary.analyze_market(
    market_data={'price': 90000.0},
    ohlcv_data=ohlcv_data
)

# Agent calculates RSI, VWAP, volatility from OHLCV
print(f"RSI: {result['rsi']}")
print(f"VWAP: {result['vwap']}")
print(f"Volatility: {result['volatility']}%")
```

### Legacy Red Team Validation

```python
# Validate trading strategies
strategy_code = """
def my_strategy(data):
    stop_loss = data['price'] * 0.95
    position_size = min(100, data['equity'] * 0.1)
    
    if data['rsi'] < 30:
        return {'action': 'buy', 'size': position_size, 'stop_loss': stop_loss}
    return {'action': 'hold'}
"""

approved, report = adversary.red_team_strategy(strategy_code)

if approved:
    print("✅ Strategy APPROVED")
else:
    print("❌ Strategy REJECTED")
    for recommendation in report['recommendations']:
        print(f"  - {recommendation}")
```

## Configuration

### Environment Variables (.env)

```bash
# DeepSeek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat

# Exchange Configuration (for live data)
EXCHANGE_ID=binanceus  # US-compatible fallback
WEEX_API_KEY=your_api_key
WEEX_API_SECRET=your_api_secret

# Trading Symbol
TRADING_SYMBOL=BTC/USDT
```

### Initialization Parameters

```python
AdversarialAlpha(
    flash_crash_pct=-0.20,           # -20% flash crash simulation
    max_drawdown_threshold=0.15,     # 15% max acceptable drawdown
    stop_loss_required=True,         # Require stop-loss in strategies
    deepseek_api_key=None,           # Auto-load from env
    volatility_threshold=1.5,        # Min volatility to trigger LLM
    use_heuristic_mode=False         # Force heuristic mode
)
```

## Testing

### Run Comprehensive Test Suite

```bash
# Run integrated test suite
python core/adversary.py

# Run pytest tests
pytest tests/test_adversary.py -v

# Run demonstration
python demo_adversary_enhanced.py
```

### Test Coverage

The test suite validates:
1. ✅ Flash Crash Simulation - Detects panic, suggests contrarian buy
2. ✅ Schema Validation - All required JSON fields present
3. ✅ Regional Block Recovery - <1s switch to mock data
4. ✅ FOMO Detection - Bull trap warnings
5. ✅ Red Team Validation - Strategy safety checks

Current Results: **17/17 tests passing (100%)**

## Technical Indicators

### Calculated Automatically

1. **RSI (Relative Strength Index)**
   - Period: 14
   - Range: 0-100
   - Oversold: <30, Overbought: >70

2. **VWAP (Volume Weighted Average Price)**
   - Calculation: Σ(Price × Volume) / Σ(Volume)
   - Used for: FOMO detection

3. **Volatility (Standard Deviation of Returns)**
   - Period: 15 candles
   - Unit: Percentage
   - High: >3%

4. **Support/Resistance Levels**
   - Detected from recent swing highs/lows
   - Used for: Liquidity trap prediction

## Performance Characteristics

- **Response Time**: <1 second (heuristic mode)
- **LLM Response**: 2-5 seconds (when triggered)
- **Memory Usage**: Low (stateless analysis)
- **Token Cost**: Minimal (rate-limited LLM calls)

## Integration Points

### With Discovery Agent
```python
from discovery_agent import DiscoveryAgent

# Discovery agent provides OHLCV data
discovery = DiscoveryAgent()
ohlcv = await discovery.fetch_ohlcv('BTC/USDT', '15m')

# Adversary analyzes
result = adversary.analyze_market(
    {'price': ohlcv[-1][4]},
    ohlcv_data=ohlcv
)
```

### With Reasoning Loop
```python
# In main trading loop
if volatility > 1.5 or narrative_event:
    analysis = adversary.analyze_market(
        market_data,
        narrative_data=narrative_pulse_data
    )
    
    if analysis['signal'] == 'BUY' and analysis['confidence'] > 0.7:
        execute_trade('buy', size=calculate_position_size())
```

## Best Practices

1. **Always Monitor Confidence Scores**
   - Only act on signals with confidence >0.6
   - Higher confidence = stronger psychological pattern

2. **Combine with Other Signals**
   - Use as confirmation, not sole decision maker
   - Cross-reference with technical indicators

3. **Respect Risk Management**
   - Even high-confidence signals can fail
   - Always use stop-losses
   - Size positions appropriately

4. **Monitor Mode Usage**
   - Track `result['mode']` to see LLM vs heuristic usage
   - High LLM usage = high volatility periods
   - Optimize token costs vs. analysis depth

5. **Regular Testing**
   - Run `python core/adversary.py` periodically
   - Verify all tests pass after updates
   - Monitor false positive rate

## Troubleshooting

### LLM Not Triggering
```python
# Check volatility threshold
if volatility < adversary.volatility_threshold:
    # Too low, adjust threshold or force LLM
    adversary.volatility_threshold = 1.0
```

### Mock Data Always Active
```python
# Check if CCXT can connect
try:
    exchange = ccxt.binanceus()
    markets = exchange.load_markets()
    print(f"Live connection: {len(markets)} markets")
except Exception as e:
    print(f"Blocked: {e}")
    # Expected in US-restricted regions
```

### Confidence Always Low
```python
# Insufficient data for bias detection
# Ensure you provide:
# - recent_prices (list of 20+ prices)
# - ohlcv_data (list of 20+ candles)
# - accurate sentiment ('extreme fear' vs 'neutral')
```

## Future Enhancements

Potential additions:
- [ ] Machine learning for confidence calibration
- [ ] Historical backtest of signal accuracy
- [ ] Multi-timeframe bias detection
- [ ] Order book analysis for liquidity depth
- [ ] Social sentiment integration (Twitter/Reddit)

## Support

For issues or questions:
1. Check test suite output: `python core/adversary.py`
2. Review logs for ERROR/WARNING messages
3. Verify `.env` configuration
4. Check network connectivity (for LLM API)

## License

Part of the AlphaWEEX / Aether-Evo trading system.
