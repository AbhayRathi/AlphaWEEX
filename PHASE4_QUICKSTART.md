# Phase 4 Quick Start Guide

Get up and running with Phase 4 (Global Oracle, Sentiment Perception, and Automated Testing) in 5 minutes!

---

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `alpaca-trade-api` - For TradFi Oracle
- `requests` - For API calls
- `pytest` - For testing
- All existing dependencies

### 2. Configure API Keys (Optional)

Phase 4 works in fallback mode without API keys, but for full functionality:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:
```bash
# Optional: Alpaca for real TradFi data
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key

# Optional: DeepSeek for advanced sentiment analysis
DEEPSEEK_API_KEY=your_deepseek_api_key
```

**Note**: Phase 4 includes resilient fallback modes. If APIs are unavailable:
- Oracle uses mock SPY/QQQ data (slightly positive market)
- Sentiment uses neutral Fear & Greed (50) and mock news
- System continues working with safe defaults

---

## ✅ Verify Installation

### Run Tests (Recommended)

```bash
pytest tests/test_phase4.py -v
```

Expected output:
```
======================== 24 passed in 0.XX s ========================
```

All tests should pass! ✅

### Run Demo

```bash
python demo_phase4.py
```

This demonstrates:
- TradFi Oracle fetching SPY/QQQ data
- Sentiment Agent analyzing market sentiment
- Position sizing in 4 different scenarios

---

## 📊 View Dashboard

Launch the dashboard with Phase 4 features:

```bash
streamlit run dashboard/app.py
```

Navigate to **Global Context** tab to see:
- 🌍 Global Risk Level (NORMAL/HIGH)
- 📊 TradFi Market Data (SPY/QQQ)
- 💭 Sentiment Analysis (Fear & Greed Index)
- 📈 BTC vs SPY Correlation Chart
- 💰 Position Sizing Impact

---

## 💻 Basic Usage

### Example: Use in Trading Strategy

```python
from core.oracle import TradFiOracle
from agents.perception import SentimentAgent
from architect import Architect
from data.shared_state import get_shared_state

# Initialize components
oracle = TradFiOracle()
sentiment_agent = SentimentAgent()
architect = Architect(guardrails)

# Update global context
oracle.update_global_risk()  # Sets global risk level
await sentiment_agent.update_sentiment()  # Sets sentiment multiplier

# Calculate position size
base_size = 100.0
final_size = architect.get_adjusted_size(base_size)

print(f"Base: ${base_size} → Final: ${final_size}")
# Output adjusts based on risk and sentiment
```

### Example: Check Global State

```python
from data.shared_state import get_shared_state

state = get_shared_state()

# Check current risk level
risk = state.get_global_risk_level()
print(f"Risk: {risk}")  # NORMAL or HIGH

# Check sentiment multiplier
multiplier = state.get_sentiment_multiplier()
print(f"Sentiment: {multiplier}x")  # 0.5 to 1.5

# Get complete state
snapshot = state.get_all_state()
print(snapshot)
```

---

## 🧪 Testing Scenarios

### Test Normal Conditions
```python
from data.shared_state import get_shared_state, RiskLevel

state = get_shared_state()
state.set_global_risk_level(RiskLevel.NORMAL)
state.set_sentiment_multiplier(1.0)

# Result: Base size unchanged
```

### Test High Risk
```python
state.set_global_risk_level(RiskLevel.HIGH)
state.set_sentiment_multiplier(1.0)

# Result: Base size reduced by 50%
```

### Test Worst Case
```python
state.set_global_risk_level(RiskLevel.HIGH)
state.set_sentiment_multiplier(0.5)

# Result: Base size reduced by 75%
```

---

## 📚 Key Concepts

### 1. Global Risk Level

Set by TradFi Oracle based on SPY performance:
- **NORMAL**: SPY ≥ -1% (normal trading)
- **HIGH**: SPY < -1% (reduced exposure)

### 2. Sentiment Multiplier

Set by Sentiment Agent based on Fear & Greed:
- **0.5-0.7**: Extreme fear/greed → reduce exposure
- **0.9-1.1**: Neutral → normal exposure
- **Range**: Always constrained to [0.5, 1.5]

### 3. Position Sizing Formula

```
Step 1: adjusted_size = base_size × sentiment_multiplier
Step 2: if risk == HIGH: adjusted_size × 0.5
Result: final_size
```

---

## 🛠️ Troubleshooting

### Issue: Tests Fail

**Solution**: Ensure all dependencies installed
```bash
pip install -r requirements.txt
pytest tests/test_phase4.py -v
```

### Issue: Import Errors

**Solution**: Run from repository root
```bash
cd /path/to/AlphaWEEX
python demo_phase4.py
```

### Issue: API Connection Errors

**This is expected!** Phase 4 includes fallback modes:
- Oracle → Uses mock SPY/QQQ data
- Sentiment → Uses neutral Fear & Greed (50)
- System continues working normally

To use real APIs, configure API keys in `.env`

### Issue: Dashboard Not Loading

**Solution**: Install Streamlit
```bash
pip install streamlit plotly
streamlit run dashboard/app.py
```

---

## 📖 Next Steps

1. **Read Full Documentation**: See `PHASE4_IMPLEMENTATION.md`
2. **Explore Tests**: Review `tests/test_phase4.py` for examples
3. **Integrate**: Add Phase 4 components to your trading strategy
4. **Customize**: Adjust thresholds and multipliers for your needs

---

## 🎯 Quick Reference

### File Structure
```
AlphaWEEX/
├── core/
│   └── oracle.py              # TradFi Oracle
├── agents/
│   └── perception.py          # Sentiment Agent
├── data/
│   └── shared_state.py        # Global State Manager
├── architect.py               # Position Sizing
├── dashboard/app.py           # Dashboard (Global Context tab)
├── tests/test_phase4.py       # Test Suite
├── demo_phase4.py             # Demo Script
└── PHASE4_IMPLEMENTATION.md   # Full Documentation
```

### Common Commands
```bash
# Run tests
pytest tests/test_phase4.py -v

# Run demo
python demo_phase4.py

# Launch dashboard
streamlit run dashboard/app.py

# Check syntax
python -c "from core.oracle import TradFiOracle"
```

---

## ✅ Success Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] All tests pass (24/24)
- [ ] Demo runs without errors
- [ ] Dashboard loads Global Context tab
- [ ] Understand position sizing formula
- [ ] Know how to use in your code

---

**Ready to use Phase 4!** 🎉

For detailed documentation, see `PHASE4_IMPLEMENTATION.md`
For questions, check the test suite for examples: `tests/test_phase4.py`
