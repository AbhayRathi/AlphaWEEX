# AlphaWEEX Phase 3: Quick Start Guide

## Overview

Phase 3 introduces the **Alpha Factory & Reasoning Visualizer** with four major enhancements:

1. **Stochastic Alpha Explorer** - Creative hypothesis generation
2. **Vectorized Backtester** - Strategy validation
3. **Reasoning Logger** - Complete trace logging
4. **Interactive Dashboard** - System visualization

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample data (if needed)
python -c "from core.backtester import VectorizedBacktester; VectorizedBacktester()._generate_sample_data()"
```

## Running Phase 3 Components

### 1. Main System (with Phase 3 Integration)

```bash
python main.py
```

This runs all components including:
- 15-minute reasoning loop
- 6-hour explorer cycle
- Backtesting validation before evolution
- Automatic reasoning trace logging

### 2. Interactive Dashboard

```bash
streamlit run dashboard/app.py
```

Access at `http://localhost:8501`

Dashboard sections:
- **Overview**: Quick stats and system status
- **Thinking Log**: Real-time R1 reasoning traces with <thought> tags
- **Strategy Lineage**: Visual evolution timeline
- **Live Metrics**: PnL tracking and kill-switch monitoring

### 3. Testing Components

```bash
# Run integration tests
python test_phase3.py

# Test individual components
python -c "from core.backtester import VectorizedBacktester; VectorizedBacktester().run_backtest()"
```

## Key Features

### Stochastic Alpha Explorer

**Trigger:** Every 6 hours  
**Temperature:** 1.3 (high creativity)  
**Input:** Current market regime + last 5 failed strategies  
**Output:** Novel trading hypothesis

Example output:
```
Hypothesis: Trading the gap between Spot and Futures funding rates on WEEX
Confidence: 65%
Suggested Indicators: Funding rate differential, Volume profile, RSI divergence
```

### Vectorized Backtester

**Deployment Thresholds:**
- Sharpe Ratio > 1.2
- Max Drawdown < 5%

**Process:**
1. Loads historical data from `data/market_cache/`
2. Runs strategy against 1000+ candles
3. Calculates performance metrics
4. Validates against thresholds
5. Blocks deployment if criteria not met

### Reasoning Logger

**Log File:** `data/reasoning_logs.jsonl`  
**Format:** JSON Lines (one trace per line)  
**Features:**
- Automatic <thought> tag extraction
- Source tracking (reasoning_loop, explorer, architect)
- Metadata storage
- Log rotation at 100MB

**Reading Logs:**
```python
from data.logger import ReasoningLogger

logger = ReasoningLogger()
traces = logger.read_recent_traces(count=10)
stats = logger.get_statistics()
```

### Dashboard Features

#### Thinking Log
- Latest decision with full reasoning
- Parsed <thought> tags
- Metadata (confidence, regime, metrics)
- Historical trace table

#### Strategy Lineage
- Evolution timeline visualization
- Version-to-version changes
- PnL tracking per evolution
- Blacklisted parameters list

#### Live Metrics
- Real-time system status
- PnL vs kill-switch threshold chart
- Component health indicators
- Evolution statistics

## Data Structure

```
data/
├── evolution_history.json      # Evolution tracking
├── reasoning_logs.jsonl        # R1 reasoning traces (Phase 3)
└── market_cache/
    └── BTC_USDT.csv           # Historical OHLCV data (Phase 3)
```

## Configuration

No additional configuration needed for Phase 3. Uses existing `.env` settings:

```env
# DeepSeek for Explorer (optional)
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_MODEL=deepseek-v3

# Trading parameters
TRADING_SYMBOL=BTC/USDT
INITIAL_EQUITY=10000.0
```

## Monitoring

### Command Line
Watch main.py output for:
- Explorer hypothesis generation (every 6h)
- Backtest validation results
- Evolution decisions with backtest metrics

### Dashboard
Access Streamlit dashboard for:
- Visual reasoning traces
- Evolution timeline
- Live PnL charts
- System health status

## Troubleshooting

### Dashboard won't start
```bash
# Check Streamlit is installed
pip install streamlit

# Try explicit Python version
python3 -m streamlit run dashboard/app.py
```

### No market data
```bash
# Generate sample data
python -c "
from core.backtester import VectorizedBacktester
bt = VectorizedBacktester()
bt._generate_sample_data()
"
```

### Backtester fails
- Ensure `data/market_cache/BTC_USDT.csv` exists
- Check active_logic.py has required functions
- Verify pandas/numpy are installed

## Next Steps

1. **Customize Explorer:**
   - Modify `agents/explorer.py`
   - Adjust temperature or interval
   - Add custom hypothesis templates

2. **Tune Backtester:**
   - Update thresholds in `core/backtester.py`
   - Add more performance metrics
   - Customize trading logic

3. **Enhance Dashboard:**
   - Add charts in `dashboard/app.py`
   - Create new visualization tabs
   - Integrate additional metrics

4. **Production Deployment:**
   - Connect to real DeepSeek API
   - Use actual WEEX exchange
   - Set up monitoring alerts

## Resources

- Main README: `README.md`
- Implementation Summary: `IMPLEMENTATION_SUMMARY.md`
- Test Suite: `test_phase3.py`

## Support

For issues or questions:
1. Check test output: `python test_phase3.py`
2. Review logs: `data/reasoning_logs.jsonl`
3. Verify installation: `pip install -r requirements.txt`
