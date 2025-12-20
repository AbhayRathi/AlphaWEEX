# Regime-Aware Native Engine Upgrade

## Overview

This document describes the major upgrade to AlphaWEEX, transforming it into a **Regime-Aware Native Engine** with enhanced market intelligence, precision trading, and self-correction memory.

## New Features

### 1. WEEX Native Client (`core/weex_client.py`)

A native Python client using `aiohttp` for direct API communication with WEEX exchange.

**Key Features:**
- **Async/await architecture** for high-performance concurrent operations
- **Direct API endpoints:**
  - `GET /capi/v2/market/contracts` - Fetch market information
  - `POST /capi/v2/order/placeOrder` - Place orders with precision enforcement
- **Precision Logic Enforcement:**
  - Automatically enforces `tick_size` for price precision
  - Automatically enforces `size_increment` for order size precision
  - Validates min/max order sizes before sending
  - Prevents precision-related order rejections

**Example Usage:**
```python
from core.weex_client import WEEXClient

async with WEEXClient(api_key, api_secret, api_password) as client:
    # Fetch market contracts
    contracts = await client.get_market_contracts()
    
    # Place order with automatic precision enforcement
    order = await client.place_order(
        symbol='BTC-USDT',
        side='buy',
        order_type='limit',
        size=0.123456789,  # Will be adjusted to precision
        price=50000.123456  # Will be adjusted to precision
    )
```

### 2. Market Regime Detection (`data/regime.py`)

Intelligent market regime detection using technical indicators.

**Regime Types:**
- `TRENDING_UP` - Strong upward trend (ADX > 25, +DI > -DI)
- `TRENDING_DOWN` - Strong downward trend (ADX > 25, +DI < -DI)
- `RANGE_VOLATILE` - Ranging market with high volatility (ADX ≤ 25, ATR above median)
- `RANGE_QUIET` - Ranging market with low volatility (ADX ≤ 25, ATR below median)

**Technical Indicators:**
- **ADX (Average Directional Index)** - Measures trend strength
- **ATR (Average True Range)** - Measures volatility
- **RSI (Relative Strength Index)** - Momentum indicator
- **+DI/-DI** - Directional indicators

**Example Usage:**
```python
from data.regime import detect_regime, get_regime_metrics, ohlcv_list_to_dataframe

# Convert OHLCV data to DataFrame
df = ohlcv_list_to_dataframe(ohlcv_data)

# Detect regime
regime = detect_regime(df)
print(f"Current regime: {regime}")

# Get all metrics
metrics = get_regime_metrics(df)
print(f"ADX: {metrics['adx']:.2f}")
print(f"ATR: {metrics['atr']:.4f}")
print(f"RSI: {metrics['rsi']:.2f}")
```

### 3. Enhanced Reasoning Loop

The reasoning loop now includes regime-aware analysis with markdown table snapshots.

**New Features:**
- **Markdown Table Snapshots** - Formats market data into structured tables
- **Regime-Aware Reasoning** - Adapts signals based on detected regime
- **DeepSeek-R1 Integration** - Prepares prompts with regime context
- **Performance History** - Includes evolution statistics in analysis

**Snapshot Format:**
```markdown
## Market Snapshot - 2023-11-14 23:52:20

### Price Action
| Metric | Value | Change |
|--------|-------|--------|
| **Open** | $50000.00 | - |
| **Close** | $50100.00 | +0.20% |

### Technical Indicators
| Indicator | Value | Interpretation |
|-----------|-------|----------------|
| **RSI** | 65.50 | Neutral |
| **ATR** | 2.5000 | Volatility measure |
| **ADX** | 30.50 | Strong trend |

### Market Regime
**Current Regime:** `TRENDING_UP`
```

### 4. Self-Correction Memory (`data/memory.py`)

Implements evolution memory with automatic parameter blacklisting.

**Features:**
- **PnL Tracking** - Monitors performance over 2-hour windows
- **Automatic Blacklisting** - Blacklists parameters that result in negative PnL
- **Persistent Storage** - Saves to `data/evolution_history.json`
- **Statistics Tracking** - Success rate, evaluation status, etc.

**Memory Structure:**
```json
{
  "evolutions": [
    {
      "timestamp": "2023-11-14T23:52:20",
      "parameters": {"rsi_period": 14, "regime": "TRENDING_UP"},
      "reason": "Low confidence in current logic",
      "initial_equity": 10000.0,
      "final_pnl": -250.0
    }
  ],
  "blacklisted_parameters": [
    {
      "parameters": {"rsi_period": 10, "regime": "RANGE_VOLATILE"},
      "pnl": -250.0,
      "reason": "Negative PnL (-250.00) over 2-hour window"
    }
  ]
}
```

**Example Usage:**
```python
from data.memory import EvolutionMemory

memory = EvolutionMemory()

# Record evolution
memory.record_evolution(
    parameters={'rsi_period': 14},
    reason='Low confidence',
    suggestion='Add RSI indicator',
    initial_equity=10000.0
)

# Check if parameters are blacklisted
is_blacklisted, reason = memory.is_blacklisted({'rsi_period': 10})
if is_blacklisted:
    print(f"Parameters blocked: {reason}")

# Get statistics
stats = memory.get_statistics()
print(f"Success rate: {stats['success_rate']:.1f}%")
```

### 5. Memory-Aware Architect

The Architect now integrates with evolution memory for intelligent evolution decisions.

**New Features:**
- **Blacklist Checking** - Prevents reusing failed parameters
- **Regime-Aware Code Generation** - Adapts strategy to current regime
- **Performance Tracking** - Records evolution outcomes
- **Memory Persistence** - Maintains long-term learning

**Evolution Decision Flow:**
1. Check if evolution is allowed (stability lock, kill-switch)
2. Check if parameters are blacklisted (memory check)
3. Generate regime-aware evolved code
4. Audit code (syntax and logic validation)
5. Record evolution in memory with initial equity
6. Monitor performance over 2-hour window
7. Blacklist if PnL is negative

## Dependencies

Added to `requirements.txt`:
- `pandas>=2.0.0` - Required for regime detection calculations

## Testing

Run the comprehensive test suite:
```bash
python test_regime_engine.py
```

Run the interactive demo:
```bash
python demo_regime_aware.py
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AlphaWEEX Engine                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ Discovery    │      │ WEEX Native  │                   │
│  │ Agent        │─────▶│ Client       │                   │
│  │ (CCXT)       │      │ (aiohttp)    │                   │
│  └──────────────┘      └──────────────┘                   │
│         │                     │                             │
│         │                     │ Precision                   │
│         │                     │ Enforcement                 │
│         ▼                     ▼                             │
│  ┌──────────────────────────────────────┐                 │
│  │      Reasoning Loop (15min)          │                 │
│  │  ┌────────────────────────────────┐  │                 │
│  │  │  Regime Detection              │  │                 │
│  │  │  • ADX (Trend Strength)        │  │                 │
│  │  │  • ATR (Volatility)            │  │                 │
│  │  │  • RSI (Momentum)              │  │                 │
│  │  └────────────────────────────────┘  │                 │
│  │  ┌────────────────────────────────┐  │                 │
│  │  │  Markdown Snapshot             │  │                 │
│  │  │  • Price Action Table          │  │                 │
│  │  │  • Technical Indicators        │  │                 │
│  │  │  • Market Regime               │  │                 │
│  │  └────────────────────────────────┘  │                 │
│  └──────────────────────────────────────┘                 │
│         │                                                   │
│         │ Analysis + Regime                                │
│         ▼                                                   │
│  ┌──────────────────────────────────────┐                 │
│  │         Architect                     │                 │
│  │  ┌────────────────────────────────┐  │                 │
│  │  │  Evolution Memory              │  │                 │
│  │  │  • Track PnL (2h windows)      │  │                 │
│  │  │  • Blacklist failures          │  │                 │
│  │  │  • Prevent repetition          │  │                 │
│  │  └────────────────────────────────┘  │                 │
│  │  ┌────────────────────────────────┐  │                 │
│  │  │  Regime-Aware Evolution        │  │                 │
│  │  │  • TRENDING_UP strategies      │  │                 │
│  │  │  • TRENDING_DOWN strategies    │  │                 │
│  │  │  • RANGE strategies            │  │                 │
│  │  └────────────────────────────────┘  │                 │
│  └──────────────────────────────────────┘                 │
│         │                                                   │
│         │ Updated Logic                                    │
│         ▼                                                   │
│  ┌──────────────────────────────────────┐                 │
│  │      active_logic.py                  │                 │
│  │  • Regime-aware signal generation     │                 │
│  │  • Adaptive strategy per regime       │                 │
│  └──────────────────────────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

1. **Higher Precision** - Native client ensures orders meet exchange requirements
2. **Intelligent Adaptation** - Regime detection enables context-aware strategies
3. **Self-Correction** - Memory prevents repeating failed strategies
4. **Better Risk Management** - Regime-specific stop losses and position sizing
5. **Improved Performance** - Strategies optimized for current market conditions

## Migration Guide

For existing AlphaWEEX users:

1. **Update dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **No configuration changes required** - The system automatically uses the new features

3. **Optional: Use WEEX Native Client** - Set up WEEX-specific credentials to use the native client instead of CCXT

4. **Monitor evolution memory** - Check `data/evolution_history.json` for performance tracking

## Future Enhancements

- Integration with actual DeepSeek-R1 API for reasoning
- Advanced parameter matching for blacklist (fuzzy matching)
- Multi-timeframe regime detection
- Regime transition detection and alerts
- Backtesting framework with regime simulation

## Support

For issues or questions, please refer to the main README.md or open an issue on GitHub.
