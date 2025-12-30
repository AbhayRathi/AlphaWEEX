# WEEX AI Trading Hackathon - Submission Policy

## Project Overview

**Project Name:** AlphaWEEX (Aether-Evo)  
**Team:** Independent Developer  
**Hackathon:** WEEX AI Trading Hackathon  
**Submission Date:** December 30, 2025  

## Project Description

AlphaWEEX is a self-evolving, AI-powered trading engine designed for the WEEX exchange. It combines advanced AI reasoning (DeepSeek R1/V3) with robust safety mechanisms to create an autonomous trading system that continuously improves its strategies while maintaining strict risk controls.

### Core Innovation

Our system implements a unique "Evolution Loop" where:
1. **DeepSeek R1** analyzes market data and generates trading insights
2. **DeepSeek V3** proposes strategy improvements
3. **Adversarial Alpha** validates strategies through stress testing
4. **Shadow Engine** tests high-risk alternatives in memory
5. **Narrative Pulse** monitors whale activity and market sentiment

### Key Differentiators

1. **Self-Evolution with Safety First**
   - Strategies evolve automatically based on market performance
   - Multiple safety layers prevent catastrophic failures
   - Adversarial testing ensures robustness

2. **Multi-Layered Risk Management**
   - Kill-Switch: Automatic halt at 3% equity loss
   - TradFi Oracle: Global risk adjustment based on SPY/QQQ
   - Sentiment Agent: Position sizing based on Fear & Greed Index
   - Whale Monitoring: Early warning system for large transfers

3. **Transparent AI Reasoning**
   - All AI decisions are logged and visible
   - Complete reasoning traces available in dashboard
   - Strategy lineage tracking shows evolution path

## AI Participation Disclosure

### DeepSeek R1/V3 Integration

**Current Status:** Framework implemented with rule-based fallbacks

The system is designed to integrate with DeepSeek R1 and V3 models:

1. **DeepSeek R1 (Reasoning):**
   - Purpose: Market analysis and pattern recognition
   - Usage: Analyzes OHLCV data every 15 minutes
   - Fallback: Rule-based technical analysis
   - Integration Point: `reasoning_loop.py`

2. **DeepSeek V3 (Code Generation):**
   - Purpose: Strategy code evolution
   - Usage: Generates improved trading logic
   - Fallback: Template-based evolution
   - Integration Point: `architect.py`

### Rule-Based Fallbacks

To ensure the system is functional without API dependencies, we've implemented sophisticated rule-based alternatives:

- **Technical Analysis:** RSI, moving averages, volume analysis
- **Regime Detection:** Volatility-based market classification
- **Risk Management:** Mathematical formulas for position sizing
- **Evolution Logic:** Template-based strategy improvements

### Human Oversight

While the system is designed to be autonomous, human oversight is maintained through:

1. **Dashboard Monitoring:** Real-time visibility into all decisions
2. **Stability Lock:** 12-hour cooldown after each evolution
3. **Approval Gates:** Critical decisions require validation
4. **Kill-Switch:** Manual override capability always available

## Trading Logic Explanation

### Strategy Generation

**Base Strategy:**
```python
1. Fetch 1-hour OHLCV data (Open, High, Low, Close, Volume)
2. Calculate technical indicators (RSI, SMA, volume trends)
3. Detect market regime (Bullish/Bearish/Sideways)
4. Check global risk level (TradFi Oracle)
5. Check sentiment multiplier (Fear & Greed Index)
6. Check whale dump risk (Narrative Pulse)
7. Generate signal (Buy/Sell/Hold)
8. Calculate position size with multiple adjustments
9. Execute trade (if conditions met)
```

### Position Sizing Formula

```
Final Position Size = Base Size × Sentiment Multiplier × Risk Multiplier

Where:
- Base Size: Calculated from available equity and risk per trade
- Sentiment Multiplier: 0.5 to 1.5 based on Fear & Greed Index
- Risk Multiplier: 0.5 if TradFi risk is HIGH, 1.0 if NORMAL
```

### Safety Mechanisms

**Layer 1: Pre-Trade Validation**
- Sufficient balance check
- Position size limits
- Maximum leverage caps

**Layer 2: In-Trade Protection**
- Stop-loss orders
- Take-profit targets
- Trailing stops (when applicable)

**Layer 3: Portfolio-Level Safeguards**
- Kill-switch at 3% loss in 1 hour
- Maximum open positions limit
- Diversification requirements

**Layer 4: Evolution Safeguards**
- Stability lock (12 hours minimum between changes)
- Adversarial testing (flash crash simulation)
- Syntax and logic validation
- Performance backtesting (Sharpe > 1.2, Drawdown < 5%)

### Risk Parameters

```
Kill-Switch Threshold: 3% equity loss in 1 hour
Max Drawdown: 5% (in backtesting)
Min Sharpe Ratio: 1.2 (for strategy approval)
Stability Lock: 12 hours between evolutions
Flash Crash Test: -20% price drop simulation
```

## Technical Architecture

### Technology Stack

- **Language:** Python 3.9+
- **Exchange Integration:** CCXT (with WEEX support via custom client)
- **Data Processing:** Pandas, NumPy
- **Visualization:** Streamlit, Plotly
- **Testing:** Pytest
- **AI Integration:** DeepSeek API (with rule-based fallbacks)

### System Components

1. **Discovery Agent** (`discovery_agent.py`)
   - Dynamic API mapping for exchanges
   - Real-time data fetching
   - Connection health monitoring

2. **Reasoning Loop** (`reasoning_loop.py`)
   - 15-minute analysis cycle
   - Market regime detection
   - Signal generation

3. **Architect** (`architect.py`)
   - Strategy evolution engine
   - Code generation and validation
   - Position sizing adjustments

4. **Guardrails** (`guardrails.py`)
   - Kill-switch implementation
   - Stability lock enforcement
   - Code syntax and logic validation

5. **TradFi Oracle** (`core/oracle.py`)
   - SPY/QQQ monitoring via Alpaca API
   - Global risk level determination
   - Cross-market correlation

6. **Sentiment Agent** (`agents/perception.py`)
   - Fear & Greed Index integration
   - News headline analysis
   - Sentiment multiplier calculation

7. **Adversarial Alpha** (`core/adversary.py`)
   - Red Team strategy validation
   - Flash crash simulation
   - Stress testing

8. **Shadow Engine** (`core/shadow_engine.py`)
   - Parallel high-risk strategy testing
   - ROI comparison
   - Promotion alert system

9. **Narrative Pulse** (`agents/narrative.py`)
   - Whale inflow monitoring
   - Market narrative tracking
   - Early warning system

## Compliance & Ethics

### Trading Ethics

- **No Market Manipulation:** System does not engage in wash trading, spoofing, or market manipulation
- **Fair Trading:** All trades are legitimate market orders
- **Transparency:** Complete audit trail of all decisions
- **Responsible AI:** Human oversight maintained at all levels

### Data Usage

- **Public Data Only:** Uses only publicly available market data
- **No Insider Information:** No use of non-public information
- **Privacy:** No collection of user data beyond what's necessary for trading

### Risk Disclosure

⚠️ **Important Risk Warnings:**

1. **Automated Trading Risks:**
   - Automated systems can incur rapid losses
   - Past performance does not guarantee future results
   - Always use only funds you can afford to lose

2. **AI Limitations:**
   - AI models can make errors
   - Rule-based fallbacks may be less sophisticated
   - Human oversight recommended

3. **Market Risks:**
   - Cryptocurrency markets are highly volatile
   - Flash crashes can occur
   - Liquidity can disappear rapidly

## Testing & Validation

### Test Coverage

- **Unit Tests:** All core components have unit tests
- **Integration Tests:** End-to-end workflow tested
- **Stress Tests:** Flash crash and extreme volatility scenarios
- **Backtesting:** Historical validation on 30+ days of data

### Quality Assurance

- **PEP8 Compliance:** All code follows Python style guidelines
- **Docstrings:** Complete documentation for all functions
- **Error Handling:** Graceful degradation on API failures
- **CI/CD:** Automated testing on every commit

### Performance Metrics

Target performance (backtested):
- **Sharpe Ratio:** > 1.2
- **Max Drawdown:** < 5%
- **Win Rate:** > 50%
- **Risk-Adjusted Returns:** Positive across market regimes

## Repository & Documentation

**GitHub Repository:** https://github.com/AbhayRathi/AlphaWEEX  
**License:** MIT  
**Documentation:** Comprehensive README.md with setup instructions

### Key Documentation Files

- `README.md` - Complete setup and usage guide
- `SECURITY.md` - API key safety and security guidelines
- `SUBMISSION_POLICY.md` - This file
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
- `PHASE3_QUICKSTART.md` - Phase 3 features guide
- `PHASE4_QUICKSTART.md` - Phase 4 features guide

## Contact & Support

For questions about this submission or the AlphaWEEX system:

- **GitHub Issues:** Use repository issue tracker
- **Security Issues:** Report privately to maintainers
- **General Inquiries:** Contact through GitHub

## Acknowledgments

This project leverages:
- **WEEX Exchange:** For providing trading infrastructure
- **DeepSeek AI:** For reasoning and code generation capabilities
- **CCXT:** For exchange connectivity
- **Open Source Community:** For various supporting libraries

---

**Declaration:** This submission is original work created specifically for the WEEX AI Trading Hackathon. All AI assistance has been disclosed above. The system has been developed with safety, transparency, and responsible trading as core principles.

**Submission Date:** December 30, 2025  
**Version:** 5.0 (Phase 5: Wild Imagination + Professional Polish)
