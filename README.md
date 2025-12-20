# Aether-Evo: Self-Evolving WEEX Trading Engine

🌟 **Aether-Evo** is an autonomous, self-evolving trading engine for the WEEX exchange that uses AI-powered reasoning (DeepSeek R1/V3) to continuously improve its trading strategies.

## 🚀 Phase 3: The Alpha Factory & Reasoning Visualizer

Phase 3 introduces advanced exploration, validation, and visualization capabilities:

1. **Stochastic Alpha Explorer** - Generates novel trading hypotheses every 6 hours using high-temperature DeepSeek-V3
2. **Vectorized Backtester** - Validates strategies with Sharpe Ratio > 1.2 and Max Drawdown < 5% before deployment
3. **Reasoning Dashboard** - Streamlit-based visualization of the system's "brain" with thinking logs and strategy lineage
4. **Enhanced Telemetry** - Complete reasoning trace logging for analysis and debugging

## 🏗️ Architecture

Aether-Evo consists of seven core components:

### 1. Discovery Agent
- **Dynamic API Mapping**: Automatically discovers WEEX exchange capabilities
- **Real-time Data**: Fetches OHLCV data, account balance, and market information
- **API Abstraction**: Provides clean interface for trading operations

### 2. Reasoning Loop (15-minute cycle)
- **R1 Analysis**: Uses DeepSeek R1 reasoning to analyze OHLCV data
- **Pattern Recognition**: Identifies trends, volume spikes, and market conditions
- **Evolution Suggestions**: Proposes improvements when confidence is low
- **Continuous Learning**: Runs every 15 minutes to stay current

### 3. Evolution System (Architect)
- **Self-Modification**: Rewrites `active_logic.py` to improve trading strategies
- **R1-Driven**: Only evolves when R1 approves and suggests improvements
- **Version Control**: Maintains backups and evolution history
- **Dynamic Reloading**: Hot-swaps logic without system restart

### 4. Guardrails (Safety Mechanisms)
- **12-Hour Stability Lock**: Prevents frequent changes after evolution
- **3% Kill-Switch**: Auto-halts trading if equity drops >3% in 1 hour
- **Syntax Audit**: Validates Python syntax before code deployment
- **Logic Audit**: Ensures required functions exist and are callable

### 5. Stochastic Alpha Explorer (Phase 3)
- **6-Hour Exploration Cycle**: Generates novel hypotheses periodically
- **High Temperature (1.3)**: Uses creative DeepSeek-V3 for unconventional ideas
- **Failure Analysis**: Studies last 5 failed strategies to avoid repetition
- **Hypothesis Generation**: Proposes new trading signals (e.g., funding rate arbitrage)

### 6. Vectorized Backtester (Phase 3)
- **Pandas-Based**: Fast vectorized backtesting engine
- **Historical Validation**: Tests strategies against data/market_cache/ data
- **Performance Metrics**: Calculates Sharpe Ratio, Max Drawdown, Win Rate
- **Deployment Gates**: Enforces Sharpe > 1.2 and Max DD < 5% thresholds

### 7. Reasoning Dashboard (Phase 3)
- **Thinking Log**: Visualizes <thought> tags from DeepSeek-R1 decisions
- **Strategy Lineage**: Shows evolution history from v1.0 to current
- **Live Metrics**: Real-time PnL vs 3% kill-switch threshold
- **Streamlit UI**: Interactive web dashboard for system monitoring

## ⚠️ WEEX Exchange Support

**Important**: WEEX is not yet included in the standard CCXT library. The current implementation uses Binance as a fallback for demonstration purposes.

To use with actual WEEX exchange:

1. **Option 1**: Wait for CCXT to add WEEX support
2. **Option 2**: Implement a custom WEEX API client
3. **Option 3**: Use WEEX's official API directly and adapt the Discovery Agent

For now, the system works with any CCXT-supported exchange (100+ exchanges available).

## 📋 Requirements

```txt
ccxt>=4.1.0
pydantic>=2.5.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
streamlit>=1.28.0
plotly>=5.17.0
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# WEEX API Configuration
WEEX_API_KEY=your_api_key_here
WEEX_API_SECRET=your_api_secret_here
WEEX_API_PASSWORD=your_api_password_here

# DeepSeek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-r1

# Trading Configuration
TRADING_SYMBOL=BTC/USDT
INITIAL_EQUITY=1000.0
KILL_SWITCH_THRESHOLD=0.03
STABILITY_LOCK_HOURS=12
REASONING_INTERVAL_MINUTES=15
```

### 3. Run Aether-Evo
```bash
python main.py
```

### 4. Run Phase 3 Dashboard
```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501` with:
- **Thinking Log**: Real-time R1 reasoning traces
- **Strategy Lineage**: Visual evolution history
- **Live Metrics**: PnL tracking and system status

### 5. Run Demo (No Network Required)
To see a complete demonstration without needing real API credentials or network access:
```bash
python demo.py
```

This will demonstrate all features including:
- Configuration loading
- Discovery Agent
- R1 Reasoning Loop
- Trading signal generation
- Evolution system (with actual code rewriting!)
- Guardrails (kill-switch and stability lock)
- Code validation
- Phase 3 Explorer (hypothesis generation)
- Phase 3 Backtester (strategy validation)

## 📁 Project Structure

```
AlphaWEEX/
├── main.py                  # Main orchestrator - coordinates all components
├── config.py                # Configuration management with Pydantic
├── discovery_agent.py       # Dynamic API mapping and data fetching
├── reasoning_loop.py        # 15m R1 analysis loop
├── architect.py             # Evolution system - rewrites active_logic.py
├── guardrails.py            # Safety mechanisms (locks, kill-switch, audits)
├── active_logic.py          # Self-evolving trading logic (modified by Architect)
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment configuration
├── agents/
│   ├── __init__.py
│   └── explorer.py          # Stochastic Alpha Explorer (Phase 3)
├── core/
│   ├── __init__.py
│   ├── weex_client.py       # WEEX API client
│   └── backtester.py        # Vectorized Backtester (Phase 3)
├── data/
│   ├── __init__.py
│   ├── memory.py            # Evolution memory and blacklisting
│   ├── regime.py            # Market regime detection
│   ├── logger.py            # Reasoning trace logger (Phase 3)
│   ├── evolution_history.json
│   ├── reasoning_logs.jsonl  # R1 reasoning traces (Phase 3)
│   └── market_cache/
│       └── BTC_USDT.csv     # Historical market data for backtesting
├── dashboard/
│   ├── __init__.py
│   └── app.py               # Streamlit dashboard (Phase 3)
└── README.md                # This file
```

## 🔄 How It Works

1. **Initialization**: Discovery Agent maps WEEX API capabilities
2. **Data Collection**: Fetches OHLCV data every 15 minutes
3. **R1 Reasoning**: Analyzes market data and generates trading signals
4. **Signal Generation**: Active logic produces buy/sell/hold decisions
5. **Evolution Check**: Architect evaluates if logic should evolve
6. **Hypothesis Generation**: Explorer suggests novel strategies every 6 hours (Phase 3)
7. **Backtesting**: Validates proposed changes against historical data (Phase 3)
8. **Guardrail Validation**: Checks stability lock and kill-switch
9. **Code Audit**: Validates syntax and logic of proposed changes
10. **Evolution**: Rewrites `active_logic.py` with improved strategy
11. **Hot Reload**: Applies new logic without system restart
12. **Telemetry**: Logs all reasoning traces for dashboard analysis (Phase 3)

## 🛡️ Safety Features

### Kill-Switch (3% in 1 hour)
If equity drops more than 3% in any 1-hour period, trading is automatically halted.

### Stability Lock (12 hours)
After each evolution, the system must run for 12 hours before the next evolution is allowed.

### Backtesting Validation (Phase 3)
All proposed strategies must pass:
- **Sharpe Ratio > 1.2**: Ensures risk-adjusted returns
- **Max Drawdown < 5%**: Limits maximum loss exposure

### Code Auditing
All proposed code changes are validated for:
- Syntax correctness (AST parsing)
- Required functions present
- Functions are callable
- No runtime errors in dry-run

### Backup System
Original logic is backed up before each evolution and can be restored on failure.

### Reasoning Trace Logging (Phase 3)
Every decision is logged to `data/reasoning_logs.jsonl` for audit and analysis.

## 📊 Monitoring

### System Logs
The system logs status every 5 minutes, including:
- Kill-switch status
- Current equity and change percentage
- Evolution lock status
- Latest trading signal
- Time since last evolution
- Total number of evolutions

### Phase 3 Dashboard
Access the interactive dashboard at `http://localhost:8501` for:

#### Thinking Log
- Real-time reasoning traces from DeepSeek-R1
- Parsed <thought> tags showing AI decision process
- Complete prompt and response history
- Metadata including confidence and regime

#### Strategy Lineage
- Visual timeline of all evolutions
- Version-to-version changes
- PnL tracking per version
- Success/failure indicators
- Blacklisted parameter history

#### Live Metrics
- Real-time PnL chart
- 3% kill-switch threshold visualization
- System component status
- Evolution statistics
- Backtesting results

## 🧪 Demo Mode

If WEEX credentials are not configured, the system runs in demo mode with:
- Simulated market data
- No real trades
- Full evolution and reasoning capabilities
- Safe for testing and development

## 🔧 Customization

### Adjusting Reasoning Interval
Change `REASONING_INTERVAL_MINUTES` in `.env` (default: 15 minutes)

### Modifying Kill-Switch Threshold
Change `KILL_SWITCH_THRESHOLD` in `.env` (default: 0.03 = 3%)

### Changing Stability Lock Duration
Change `STABILITY_LOCK_HOURS` in `.env` (default: 12 hours)

### Trading Symbol
Change `TRADING_SYMBOL` in `.env` (default: BTC/USDT)

## 🤖 DeepSeek Integration

Currently, the system uses simulated R1 reasoning. To integrate real DeepSeek R1/V3:

1. Set `DEEPSEEK_API_KEY` in `.env`
2. Modify `reasoning_loop.py` to call DeepSeek API
3. Update `architect.py` to use DeepSeek for code generation

Example API integration point in `reasoning_loop.py`:
```python
# Replace simulate_r1_reasoning() with actual API call
response = await deepseek_api.analyze(ohlcv_data, model="deepseek-r1")
```

## 📈 Evolution History

The system maintains a history of all evolutions:
- Timestamp of each evolution
- Reason for evolution
- Suggested improvements
- Backup of previous logic

## ⚠️ Warnings

- **Use at your own risk**: Automated trading involves financial risk
- **Test thoroughly**: Always test with small amounts first
- **Monitor actively**: Keep an eye on the system, especially after evolutions
- **API limits**: Respect WEEX API rate limits
- **Credentials security**: Never commit `.env` file to version control

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code passes syntax validation
- Guardrails are respected
- Documentation is updated
- Tests are included

## 🔗 Resources

- [CCXT Documentation](https://docs.ccxt.com/)
- [WEEX Exchange](https://www.weex.com/)
- [DeepSeek AI](https://www.deepseek.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Built with ❤️ for autonomous trading evolution**
