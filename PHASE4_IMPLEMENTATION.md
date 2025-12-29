# Phase 4 Implementation Summary

## Global Oracle, Sentiment Perception, and Automated Testing

This document summarizes the implementation of Phase 4 features for the AlphaWEEX trading system.

---

## 🎯 Overview

Phase 4 introduces three major components:

1. **TradFi Oracle**: Monitors traditional finance markets (SPY, QQQ) via Alpaca API
2. **Sentiment Agent**: Analyzes market sentiment using Fear & Greed Index and news
3. **Dynamic Position Sizing**: Adjusts trade sizes based on global risk and sentiment

---

## 📁 New Files

### Core Components

- **`data/shared_state.py`** - Thread-safe global state manager
  - Manages global risk level (NORMAL/HIGH)
  - Stores sentiment multiplier (0.5-1.5)
  - Provides singleton access pattern

- **`core/oracle.py`** - TradFi Oracle
  - Connects to Alpaca Market Data API
  - Fetches 1-hour bars for SPY and QQQ
  - Sets global risk level based on SPY performance (-1% threshold)
  - Resilient fallback mode when API unavailable

- **`agents/perception.py`** - Sentiment Agent
  - Fetches Fear & Greed Index from alternative.me API
  - Fetches Bitcoin news headlines
  - Analyzes sentiment using rule-based logic (R1 integration ready)
  - Returns sentiment multiplier (0.5-1.5)

### Updated Components

- **`architect.py`** - Enhanced with position sizing
  - Added `get_adjusted_size()` method
  - Formula: `Final_Size = Base_Size × Sentiment_Multiplier`
  - Safety override: 50% reduction when global risk is HIGH

- **`dashboard/app.py`** - New Global Context tab
  - Displays global risk level and TradFi market data
  - Shows sentiment analysis and Fear & Greed Index
  - Visualizes BTC vs SPY correlation (24h normalized chart)
  - Demonstrates position sizing impact

### Testing

- **`tests/test_phase4.py`** - Comprehensive test suite
  - Syntax checks for all new modules
  - Unit tests for Oracle with mock data
  - Unit tests for Sentiment Agent
  - Integration tests for position sizing
  - Case test: 0.5 sentiment + HIGH risk = 75% reduction

### Demo

- **`demo_phase4.py`** - Interactive demonstration
  - Shows all Phase 4 features in action
  - Demonstrates different risk/sentiment scenarios
  - Provides clear output for verification

---

## 🔧 Configuration

Add these environment variables to your `.env` file:

```bash
# Alpaca Market Data API (Phase 4 - TradFi Oracle)
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
```

---

## 📦 Dependencies

New dependencies added to `requirements.txt`:

```
alpaca-trade-api>=3.0.0    # TradFi Oracle
requests>=2.31.0            # API calls
pytest>=7.4.0               # Testing
pytest-asyncio>=0.21.0      # Async testing
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### 1. Run Tests

```bash
# Run all Phase 4 tests
pytest tests/test_phase4.py -v

# Run specific test class
pytest tests/test_phase4.py::TestTradFiOracle -v

# Run with detailed output
pytest tests/test_phase4.py -v -s
```

All 24 tests should pass ✅

### 2. Run Demo

```bash
python demo_phase4.py
```

The demo will:
- Initialize Oracle and Sentiment Agent
- Fetch market data (or use fallback)
- Analyze sentiment
- Demonstrate position sizing in 4 scenarios

### 3. View Dashboard

```bash
streamlit run dashboard/app.py
```

Navigate to the **Global Context** tab to see:
- Real-time global risk level
- TradFi market data (SPY/QQQ)
- Sentiment analysis
- BTC vs SPY correlation chart
- Position sizing impact visualization

---

## 🏗️ Architecture

### Data Flow

```
┌─────────────────┐
│  Alpaca API     │ (SPY/QQQ 1h bars)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TradFi Oracle  │
└────────┬────────┘
         │ Sets global_risk_level
         ▼
┌─────────────────┐
│  SharedState    │◄────────────┐
└────────┬────────┘             │
         │                      │
         │                      │ Sets sentiment_multiplier
         │                      │
         │              ┌───────┴────────┐
         │              │ Sentiment Agent│
         │              └───────┬────────┘
         │                      ▲
         │                      │
         │              ┌───────┴────────┐
         │              │ Fear & Greed   │
         │              │ + News API     │
         │              └────────────────┘
         │
         ▼
┌─────────────────┐
│   Architect     │
│ get_adjusted_   │
│    size()       │
└─────────────────┘
         │
         ▼
    Final Position Size
```

### Position Sizing Formula

```python
# Step 1: Apply sentiment multiplier
adjusted_size = base_size × sentiment_multiplier

# Step 2: Apply safety override if HIGH risk
if global_risk_level == HIGH:
    adjusted_size = adjusted_size × 0.5

# Result: Final position size
```

---

## 📊 Examples

### Example 1: Normal Conditions
- **Risk**: NORMAL
- **Sentiment**: 1.0x (Neutral)
- **Base Size**: $100
- **Final Size**: $100 (no change)

### Example 2: Cautious Sentiment
- **Risk**: NORMAL
- **Sentiment**: 0.7x (Fearful)
- **Base Size**: $100
- **Final Size**: $70 (30% reduction)

### Example 3: High Risk
- **Risk**: HIGH
- **Sentiment**: 1.0x (Neutral)
- **Base Size**: $100
- **Final Size**: $50 (50% reduction)

### Example 4: Worst Case
- **Risk**: HIGH
- **Sentiment**: 0.5x (Panicked)
- **Base Size**: $100
- **Final Size**: $25 (75% reduction)

---

## 🛡️ Safety Features

### 1. Resilient Fallback Modes

- **Oracle**: Falls back to neutral market data if Alpaca API fails
- **Sentiment**: Falls back to neutral sentiment if Fear & Greed API fails
- **Default Risk**: Always defaults to NORMAL on error (safe fallback)

### 2. Safety Overrides

- **HIGH Risk**: Forces 50% reduction on all positions
- **Sentiment Clamping**: Multiplier constrained to [0.5, 1.5] range

### 3. Thread Safety

- **SharedState**: Uses threading locks for concurrent access
- **Singleton Pattern**: Ensures single source of truth

---

## 🧪 Test Coverage

### Test Categories

1. **Syntax Checks** (4 tests)
   - Verify all modules import correctly
   - Check method existence

2. **SharedState Tests** (3 tests)
   - Singleton pattern
   - Risk level management
   - Sentiment multiplier clamping

3. **Oracle Tests** (5 tests)
   - Initialization
   - Fallback data
   - Risk calculation (HIGH/NORMAL)
   - Error handling

4. **Sentiment Tests** (6 tests)
   - Initialization
   - Fear & Greed fallback
   - News fetching
   - Rule-based sentiment (Euphoric/Panicked/Neutral)

5. **Position Sizing Tests** (4 tests)
   - Normal conditions
   - With sentiment
   - With HIGH risk
   - Worst case (combined)

6. **Integration Tests** (2 tests)
   - Full workflow
   - Case test: 0.5 sentiment + HIGH risk

**Total: 24 tests, all passing ✅**

---

## 🔮 Future Enhancements

### 1. DeepSeek R1 Integration
Currently using rule-based sentiment analysis. Can be enhanced with:
```python
sentiment_agent = SentimentAgent(
    deepseek_api_key="your_key",
    use_deepseek=True  # Enable R1 reasoning
)
```

### 2. Real-time Data Feeds
- Add WebSocket support for real-time market data
- Implement streaming sentiment updates
- Continuous risk monitoring

### 3. Advanced Analytics
- Correlation analysis between BTC and TradFi markets
- Machine learning for sentiment classification
- Historical backtesting with Phase 4 features

### 4. Additional Risk Factors
- VIX volatility index
- Treasury yields
- Crypto market dominance

---

## 📝 API Documentation

### SharedState

```python
from data.shared_state import get_shared_state, RiskLevel

state = get_shared_state()

# Set global risk level
state.set_global_risk_level(RiskLevel.HIGH)

# Get global risk level
risk = state.get_global_risk_level()

# Set sentiment multiplier (clamped to 0.5-1.5)
state.set_sentiment_multiplier(0.8)

# Get sentiment multiplier
multiplier = state.get_sentiment_multiplier()
```

### TradFi Oracle

```python
from core.oracle import TradFiOracle

oracle = TradFiOracle(
    alpaca_api_key="your_key",
    alpaca_secret_key="your_secret",
    spy_threshold=-0.01  # -1% threshold
)

# Update global risk based on market data
risk_level = oracle.update_global_risk()

# Get market summary
summary = oracle.get_market_summary()
```

### Sentiment Agent

```python
from agents.perception import SentimentAgent

agent = SentimentAgent(
    deepseek_api_key="your_key",
    use_deepseek=False  # True for R1 reasoning
)

# Update sentiment multiplier
multiplier = await agent.update_sentiment()

# Get sentiment summary
summary = agent.get_sentiment_summary()
```

### Position Sizing

```python
from architect import Architect

architect = Architect(guardrails)

# Get adjusted position size
base_size = 100.0
final_size = architect.get_adjusted_size(base_size)
```

---

## ✅ Verification Checklist

- [x] All new modules import correctly
- [x] All 24 tests pass
- [x] Demo script runs without errors
- [x] Dashboard displays Global Context tab
- [x] Position sizing works correctly
- [x] Fallback modes handle API failures
- [x] Thread-safe SharedState implementation
- [x] Safety overrides applied correctly
- [x] Documentation complete
- [x] Code follows repository conventions

---

## 🤝 Contributing

When extending Phase 4:

1. Add tests to `tests/test_phase4.py`
2. Update this documentation
3. Ensure all existing tests still pass
4. Follow the existing code style
5. Add logging for debugging

---

## 📚 References

- **Alpaca API**: https://alpaca.markets/docs/
- **Fear & Greed Index**: https://alternative.me/crypto/fear-and-greed-index/
- **pytest Documentation**: https://docs.pytest.org/

---

**Phase 4 Status**: ✅ Complete and Tested

All deliverables implemented:
- ✅ `core/oracle.py`
- ✅ `agents/perception.py`
- ✅ Updated `architect.py`
- ✅ `tests/test_phase4.py`
- ✅ Dashboard Global Context tab
- ✅ Comprehensive testing and verification
