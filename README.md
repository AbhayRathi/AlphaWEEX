# AlphaWEEX: Self-Evolving AI Trading Engine

> **WEEX AI Trading Hackathon Submission** | Deadline: December 30, 2025

🏆 **AlphaWEEX** is an autonomous, self-evolving trading engine that combines advanced AI reasoning (DeepSeek R1/V3) with multi-layered safety mechanisms to create a trading system that continuously improves while maintaining strict risk controls.

---

## 📋 Prerequisites

Before running AlphaWEEX, ensure you have:

### System Requirements
- **Python**: 3.10 or higher (check: `python --version`)
- **Operating System**: Linux, macOS, or Windows with WSL
- **Memory**: 2GB RAM minimum, 4GB recommended for full operation
- **Disk Space**: 500MB for dependencies and logs

### API Keys Required
- **WEEX Exchange** (or Binance for demo mode)
  - API Key and Secret with trading permissions
  - Get at: [WEEX API Portal](https://www.weex.com/api-management)
  
- **DeepSeek API**
  - API key for V3 Architect and R1 Auditor models
  - Get at: [DeepSeek Platform](https://platform.deepseek.com)
  
- **Alpaca Markets** (Free Tier Available)
  - API Key and Secret for TradFi Oracle
  - Get at: [Alpaca Dashboard](https://alpaca.markets)

### Optional
- Docker (for containerized deployment)
- Make utility (for simplified commands)

---

## ⚡ Quick Start for Judges (2 Minutes)

Get AlphaWEEX running in 2 minutes with these simple commands:

### Step 0: Configure API Keys (30 seconds)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials:
# - WEEX_API_KEY and WEEX_API_SECRET (or Binance for demo)
# - DEEPSEEK_API_KEY (for R1/V3 reasoning models)
# - ALPACA_API_KEY and ALPACA_SECRET_KEY (for TradFi Oracle - free tier available)
```

**Note**: You can test with demo mode by setting `DEMO_MODE=true` in `.env`

### Step 1-4: Install and Run

```bash
# 1. Install dependencies and run tests (1 minute)
make install && make test

# 2. Verify system integrity
python scripts/check_integrity.py

# 3. (Optional) Start paper trading
make run-paper

# 4. (Optional) Launch dashboard
make dashboard
```

### What Just Happened?

✅ **72 tests passed** - Full test coverage verified  
✅ **All modules imported** - System integrity confirmed  
✅ **SharedState singleton** - Global risk management ready  
✅ **5-Layer Shield active** - TradFi Oracle + Narrative Pulse + Adversarial Testing + Shadow Engine + Kill-Switch

### Architecture Overview

See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) for complete technical details on:
- **Recursive Evolution Loop**: V3 Architect ↔ R1 Auditor ↔ Strategy
- **5-Layer Safety Shield**: Multiple redundant protection mechanisms
- **Data Flow**: WEEX API → SharedState → Architect → Executor

### Key Files to Review

| File | Description |
|------|-------------|
| `SYSTEM_ARCHITECTURE.md` | Complete system architecture and data flow |
| `CONTRARIAN_SENTIMENT_README.md` | **NEW** - Funding rate contrarian strategy documentation |
| `scripts/check_integrity.py` | Final integrity verification script |
| `main.py` | Main orchestrator coordinating all components |
| `active_logic.py` | Current live trading strategy (auto-evolved) |
| `tests/` | 72+ comprehensive tests (adversary, shadow, narrative, integration) |

---

## 🌟 Vision

**The Future of Autonomous Trading**

AlphaWEEX represents a paradigm shift in algorithmic trading:
- **Self-Evolution**: Strategies improve autonomously based on market performance
- **AI-Driven**: DeepSeek R1 analyzes markets, V3 generates code improvements
- **Safety First**: Multiple redundant safety layers prevent catastrophic failures
- **Transparent**: Every decision is logged and auditable
- **Adversarial Testing**: Strategies must survive simulated crashes before deployment

We're not just building a trading bot—we're building a trading system that learns, adapts, and evolves in real-time while maintaining professional risk management standards.

---

## 🔥 Key Innovations

### 1. **Adversarial Alpha** (Phase 5 - Wild Imagination)
Red Team debate protocol that validates strategies through stress testing:
- ✅ Simulates **-20% flash crashes** against proposed strategies
- ✅ Rejects strategies without proper stop-loss mechanisms
- ✅ Validates maximum drawdown limits (< 15%)
- ✅ **Architect (V3) vs Auditor (R1)** debate protocol
- ✅ Only deploys strategies that pass adversarial testing

### 2. **Shadow Trading Engine** (Phase 5 - Wild Imagination)
Parallel strategy testing with promotion alerts:
- ✅ Runs **high-risk/high-reward** strategies in memory
- ✅ Compares Shadow ROI vs Live ROI continuously
- ✅ **Promotion Alert**: Triggers when Shadow maintains higher Sharpe > 1.2 for 100+ iterations
- ✅ Zero-risk experimentation with real market data
- ✅ Dashboard visualization of Shadow vs Live performance

### 3. **Narrative Pulse** (Phase 5 - Wild Imagination)
Whale activity monitoring and market narrative tracking:
- ✅ **Whale Inflow Detection**: Monitors BTC flows > 1000 BTC to exchanges
- ✅ **whale_dump_risk Flag**: Integrates with SharedState for risk management
- ✅ Elevates global risk level on large transfers
- ✅ Early warning system for potential market movements

### 4. **Contrarian Sentiment Analyst** (NEW - Funding Rate Strategy)
Funding rate analysis for contrarian trading opportunities:
- ✅ **Live Funding Rate Monitoring**: Tracks funding rates for all 8 trading pairs
- ✅ **Extreme Positive (>0.05%)**: Restricts LONG trades (over-leveraged, crash risk)
- ✅ **Extreme Negative (<-0.05%)**: Prioritizes LONG trades (short-squeeze setup)
- ✅ **Weighted Against RSI/MACD**: Adjusts technical signal confidence dynamically
- ✅ **LLM Integration**: AI receives funding rate context for informed decisions
- 📖 See [CONTRARIAN_SENTIMENT_README.md](CONTRARIAN_SENTIMENT_README.md) for details

### 5. **TradFi Oracle** (Phase 4 - Global Context)
Traditional finance integration for cross-market risk assessment:
- ✅ Monitors **SPY/QQQ** via Alpaca Market Data API
- ✅ Sets **global_risk_level** (NORMAL/HIGH) based on 1-hour moves
- ✅ **Position sizing adjustment**: 50% reduction when SPY drops > 1%
- ✅ Brings macro context to crypto trading decisions

### 6. **Sentiment Agent** (Phase 4 - Market Psychology)
Fear & Greed Index integration with dynamic position sizing:
- ✅ Fetches **Fear & Greed Index** from alternative.me
- ✅ Analyzes Bitcoin news headlines
- ✅ **Sentiment Multiplier**: 0.5-1.5x adjustment to position sizes
- ✅ Reduces exposure during euphoria and panic

### 7. **Evolution System** (Phase 2 - Self-Improvement)
Autonomous strategy evolution with safety gates:
- ✅ **Architect** rewrites `active_logic.py` based on R1 suggestions
- ✅ **Backtesting gate**: Sharpe > 1.2, Max Drawdown < 5%
- ✅ **Stability lock**: 12-hour cooldown between evolutions
- ✅ Version control and rollback capability
- ✅ Syntax and logic validation before deployment

---

## 🛡️ Safety Gates

AlphaWEEX implements **5 layers of safety** to prevent catastrophic failures:

### Layer 1: Pre-Trade Validation
```
✓ Adversarial testing (flash crash simulation)
✓ Backtesting performance gates
✓ Syntax and logic validation
✓ Stop-loss requirement checks
```

### Layer 2: Position-Level Controls
```
✓ Dynamic position sizing (TradFi risk × Sentiment)
✓ Maximum position limits
✓ Leverage caps
✓ Whale dump risk adjustments
```

### Layer 3: Portfolio-Level Safeguards
```
✓ Kill-Switch: 3% equity drop in 1 hour → Halt trading
✓ Maximum open positions limit
✓ Diversification requirements
```

### Layer 4: Evolution Safeguards
```
✓ Stability Lock: 12 hours between evolutions
✓ Strategy blacklisting (failed strategies never retry)
✓ Backup and rollback mechanisms
✓ Red Team audit (Adversarial Alpha)
```

### Layer 5: Graceful Degradation
```
✓ API failure → Safe Mode (cached data)
✓ Invalid signals → Hold position
✓ Missing data → Conservative defaults
✓ Errors logged, never crash
```

---

## 🔄 The Evolution Loop

AlphaWEEX continuously improves through a closed feedback loop:

```
[Market Data] → [R1 Reasoning] → {Confidence > 0.7?}
                                        ↓ No
                            [Evolution Suggestion] → [Architect V3]
                                        ↓
                            [Generate New Code] → [Backtester]
                                        ↓
                            {Sharpe > 1.2?} → [Adversarial Alpha]
                                        ↓
                            {Pass Flash Crash?} → [Deploy to Live]
                                        ↓
                            [Market Data] (loop back)
```

**Cycle Frequency:**
- **Reasoning**: Every 15 minutes
- **Evolution**: When confidence < 0.7 (limited by 12h stability lock)
- **Exploration**: Every 6 hours (Alpha Explorer generates hypotheses)
- **Backtesting**: Before every evolution deployment

---

## 🧠 Tech Stack

### AI & Reasoning
- **DeepSeek R1**: Market analysis and reasoning
- **DeepSeek V3**: Code generation for strategy evolution
- **Rule-Based Fallbacks**: Ensure functionality without API dependency

### Trading Infrastructure
- **CCXT**: Multi-exchange connectivity (100+ exchanges)
- **Custom WEEX Client**: Direct WEEX API integration
- **Alpaca API**: TradFi market data (SPY/QQQ)

### Data & Analytics
- **Pandas**: Vectorized backtesting engine
- **NumPy**: Performance calculations
- **Streamlit + Plotly**: Interactive dashboard

### Safety & Testing
- **Guardrails**: Kill-switch and stability lock
- **Adversarial Alpha**: Red Team strategy validation
- **Pytest**: 56 comprehensive unit and integration tests
- **CI/CD**: Automated testing on every push

---

## 📊 Global Context Integration

AlphaWEEX doesn't trade in a vacuum—it considers multiple data sources:

| Data Source | Purpose | Update Frequency | Impact |
|------------|---------|------------------|---------|
| **BTC/USDT OHLCV** | Primary trading signal | 15 minutes | Direct |
| **SPY/QQQ (TradFi)** | Global risk level | 15 minutes | 50% position reduction if HIGH |
| **Fear & Greed Index** | Market sentiment | 15 minutes | 0.5-1.5x position multiplier |
| **Whale Inflows** | Large transfer monitoring | Real-time | Risk level elevation |
| **Bitcoin News** | Narrative analysis | 15 minutes | Sentiment adjustment |
| **Historical Backtest** | Strategy validation | On-demand | Go/No-go deployment |

**Final Position Size Formula:**
```python
position = base_size × sentiment_multiplier × risk_multiplier × whale_adjustment

where:
  risk_multiplier = 0.5 if global_risk_level == HIGH else 1.0
  sentiment_multiplier = 0.5 to 1.5 (from Fear & Greed)
  whale_adjustment = 0.7 if whale_dump_risk else 1.0
```

---

## 🚀 Quick Start

### Using Makefile (Recommended)

```bash
# Install dependencies
make install

# Run tests
make test

# Start paper trading
make run-paper

# Launch dashboard
make dashboard

# Quick setup (install + test)
make quickstart
```

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API credentials

# 3. Run tests
python -m pytest tests/ -v

# 4. Start trading
python main.py

# 5. Launch dashboard (separate terminal)
streamlit run dashboard/app.py
```

---

## 🧪 Testing & Quality Assurance

### Test Coverage

- **56 Tests Total** across 4 test files
  - ✅ 12 Adversarial Alpha tests
  - ✅ 18 Shadow Engine tests  
  - ✅ 18 Narrative Pulse tests
  - ✅ 8 Full-stack integration tests

### Quality Standards

- ✅ **PEP8 Compliant**: Python style guidelines
- ✅ **Docstrings**: Complete API documentation
- ✅ **Error Handling**: Graceful degradation on failures
- ✅ **CI/CD**: Automated testing on GitHub Actions

### Running Tests

```bash
# All tests
make test

# Specific test file
python -m pytest tests/test_adversary.py -v

# Integration tests only
python -m pytest tests/test_full_stack.py -v
```

---

## 🔒 Security & Risk Management

### API Key Safety

- ✅ Environment variables only (`.env` file)
- ✅ `.env` in `.gitignore` (never committed)
- ✅ API keys with **withdrawals disabled**
- ✅ IP whitelisting recommended
- ✅ Paper trading mode for testing

See [SECURITY.md](SECURITY.md) for complete security guidelines.

### Risk Parameters

```python
# Default Risk Configuration
KILL_SWITCH_THRESHOLD = 0.03     # 3% equity loss
MAX_DRAWDOWN = 0.05              # 5% maximum drawdown
STABILITY_LOCK_HOURS = 12        # Hours between evolutions
MIN_SHARPE_RATIO = 1.2           # Minimum for deployment
FLASH_CRASH_TEST = -0.20         # -20% stress test
```

### Cloudflare 521 Hardening Configuration

The bot includes advanced error handling for Cloudflare 521 errors with per-route cooldown tracking:

```bash
# API rate limiting and backoff configuration
WEEX_API_DELAY=0.5                  # Delay between API calls (seconds)
WEEX_521_BASE_BACKOFF=8             # Base backoff for 521 errors (seconds)
WEEX_521_MAX_BACKOFF=45             # Maximum backoff cap (seconds)
WEEX_521_MIN_JITTER=5               # Minimum jitter added to backoff (seconds)
WEEX_521_MAX_JITTER=25              # Maximum jitter added to backoff (seconds)

# Leverage initialization
WEEX_DISABLE_LEVERAGE_INIT=true     # Skip leverage init to reduce 404 noise

# Pending-orders caching (reduces API calls)
WEEX_PENDING_ORDERS_TTL=10          # Cache TTL for pending-orders (seconds)
WEEX_DISABLE_LIQUID_CAPITAL=false   # Emergency kill-switch to bypass liquid capital calc

# Available balance fallback
WEEX_AVAILABLE_FALLBACK_HAIRCUT=1.0 # Multiply fallback "available" by this factor (e.g., 0.98 for extra caution)

# Note: USE_CURL_CFFI is reserved for future TLS impersonation feature (not yet implemented)
```

**How it works:**
- **Per-route cooldown**: A 521 error on BTCUSDT K-lines won't block ETHUSDT K-lines or balance checks
- **Jittered exponential backoff**: Automatic retry with tunable randomized delays (default 5-25s jitter) to avoid thundering herd
- **Smart recovery**: Cooldown clears automatically on the first successful 200 response for each route
- **Symbol isolation**: Each symbol+endpoint combination has independent cooldown tracking
- **Pending-orders caching**: Reduces calls to `/capi/v2/positions/pending-orders` with TTL cache and cooldown-aware reuse

### WEEX V2 Symbol Format Auto-Fallback

The bot automatically handles WEEX V2's varying symbol format requirements across endpoints:

```bash
# CI/Testing overrides (optional - leave empty for production)
WEEX_CONTRACT_MAP_OVERRIDE=         # JSON to override contract discovery
WEEX_SYMBOL_FORMAT_HINT=            # JSON to pre-seed symbol format cache
```

**How it works:**
- **Central symbol rewrite**: All API requests normalize symbols before sending
- **40020 auto-fallback**: On "Parameter symbol is invalid" (code 40020), the bot tries:
  1. Contract format: `BTCUSDT_UMCBL` (resolved via contract discovery)
  2. Legacy cmt format: `cmt_btcusdt`
  3. Plain format: `BTCUSDT`
- **Per-endpoint caching**: First successful format is cached for 60 minutes per path+symbol
- **No retry for other 400 errors**: Only error code 40020 triggers the symbol fallback

**Example log output:**
```
Resolved symbol: BTCUSDT → BTCUSDT_UMCBL (preflight)
⚠️ 40020 error for BTCUSDT, trying fallback format: cmt
Cached symbol format: /capi/v2/order/placeOrder + BTCUSDT → cmt
```

---

## 📚 Documentation

### Core Documentation

- [README.md](README.md) - This file (overview & quick start)
- [SECURITY.md](SECURITY.md) - Security guidelines & API safety
- [SUBMISSION_POLICY.md](SUBMISSION_POLICY.md) - Hackathon submission details

### Phase-Specific Guides

- [PHASE3_QUICKSTART.md](PHASE3_QUICKSTART.md) - Alpha Explorer & Backtester
- [PHASE4_QUICKSTART.md](PHASE4_QUICKSTART.md) - Oracle & Sentiment Agent

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### "ModuleNotFoundError: No module named X"
**Cause**: Dependencies not installed or virtual environment not activated  
**Solution**:
```bash
# Ensure you're in a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### "API Connection Failed" or "Authentication Error"
**Cause**: Missing or invalid API keys  
**Solution**:
```bash
# Verify .env file exists and has all required keys
cat .env | grep -E "API_KEY|SECRET"

# Check for trailing spaces or quotes in .env values
# Correct format: WEEX_API_KEY=your_key_here (no quotes)
```

#### "External API Timeout" (api.alternative.me or data.alpaca.markets)
**Cause**: Firewall blocking external data sources  
**Solution**:
```bash
# Skip live API tests
pytest tests/ -k "not test_live" -v

# Or configure firewall to allow:
# - api.alternative.me (Fear & Greed Index)
# - data.alpaca.markets (TradFi data)
```

#### Test Failures with "72 tests expected"
**Cause**: Python version incompatibility or missing dependencies  
**Solution**:
```bash
# Verify Python version (requires 3.10+)
python --version

# Clean install
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
make test
```

#### "SharedState singleton not accessible"
**Cause**: Import path issues or corrupted installation  
**Solution**:
```bash
# Quick diagnostic
python -c "from data.shared_state import get_shared_state; print('✅ Core imports working')"

# If fails, reinstall in development mode
pip install -e .
```

#### General Debugging
Enable debug logging to see detailed operation:
```bash
# In your script or .env
LOG_LEVEL=DEBUG
```

#### Still Having Issues?
- Check the GitHub Issues for similar problems
- Review `SYSTEM_ARCHITECTURE.md` for system design context
- Examine log files in the `logs/` directory
- Open a new issue with:
  - Python version (`python --version`)
  - OS and version
  - Full error traceback
  - Steps to reproduce

---

## ⚠️ Disclaimer

**Important Risk Warnings:**

- ⚠️ **Automated trading involves significant financial risk**
- ⚠️ **Past performance does not guarantee future results**
- ⚠️ **Only trade with funds you can afford to lose**
- ⚠️ **Test thoroughly with paper trading first**
- ⚠️ **Monitor the system actively**

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🏆 Hackathon Submission

**Project:** AlphaWEEX (Aether-Evo)  
**Category:** WEEX AI Trading Hackathon  
**Submission Date:** December 30, 2025  
**Version:** 5.0 (Phase 5: Wild Imagination + Professional Polish)

### Key Differentiators

✅ **Only system with adversarial strategy testing**  
✅ **First to implement shadow strategy comparison**  
✅ **Most comprehensive safety layer architecture**  
✅ **Fully autonomous with human oversight**  
✅ **Complete test coverage (56 tests)**  
✅ **Professional-grade documentation**  

---

**Built with ❤️ for autonomous trading evolution**

*Submitted to WEEX AI Trading Hackathon - December 30, 2025*
