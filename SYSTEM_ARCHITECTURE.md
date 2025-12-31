# AlphaWEEX System Architecture

## Overview: The Recursive Evolution Loop

AlphaWEEX employs a **Recursive Evolution Loop** that continuously improves trading strategies through autonomous feedback cycles:

```
┌─────────────────────────────────────────────────────────────────┐
│                    RECURSIVE EVOLUTION LOOP                      │
└─────────────────────────────────────────────────────────────────┘

[Market Data] → [R1 Auditor Analysis]
                      ↓
         {Low Confidence < 0.7?}
                      ↓ Yes
         [Evolution Suggestion] → [V3 Architect]
                      ↓
         [Generate New Strategy Code]
                      ↓
         [Backtester Validation] → {Sharpe > 1.2? Drawdown < 5%?}
                      ↓ Yes
         [Adversarial Red Team] → {Pass Flash Crash Test?}
                      ↓ Yes
         [Deploy to Active Logic] → [Live Trading]
                      ↓
         [Performance Monitoring] → [Market Data] (loop back)
```

### Key Components:

1. **R1 Auditor (DeepSeek R1)**: Analyzes market conditions every 15 minutes and identifies weaknesses in current strategy
2. **V3 Architect (DeepSeek V3)**: Generates improved strategy code based on R1's recommendations
3. **Strategy Validator**: Multi-layer validation through backtesting and adversarial testing
4. **Live Deployment**: Approved strategies replace `active_logic.py` with 12-hour stability lock

---

## The 5-Layer Shield: Capital Protection System

AlphaWEEX protects capital through **5 redundant safety layers** that operate independently:

### Layer 1: TradFi Oracle - Macro Risk Detection

**Purpose**: Connect crypto trading decisions to global market conditions

**How It Works**:
- Monitors **SPY (S&P 500)** and **QQQ (NASDAQ)** via Alpaca Market Data API
- Fetches 1-hour price bars every 15 minutes
- Calculates percentage changes from previous hour
- Sets `global_risk_level` to **HIGH** when SPY drops > 1%

**Impact**:
```python
# Position sizing adjustment
if global_risk_level == HIGH:
    position_size = base_position * 0.5  # 50% reduction
```

**Key Files**: `core/oracle.py`, `data/shared_state.py`

---

### Layer 2: Narrative Pulse - Whale Move Detection

**Purpose**: Early warning system for potential market manipulation

**How It Works**:
- Monitors BTC inflows to exchanges (>1000 BTC threshold)
- Tracks large wallet movements via exchange APIs
- Sets `whale_dump_risk` flag in SharedState
- Elevates global risk level on whale events

**Impact**:
```python
# Whale risk adjustment
if whale_dump_risk:
    position_size = base_position * 0.7  # 30% reduction
    stop_loss_tighter = True
```

**Detection Logic**:
```python
if exchange_inflow_btc >= 1000:
    whale_dump_risk = True
    sentiment = "🐋 CAUTION: Large whale inflow detected"
```

**Key Files**: `agents/narrative.py`, `data/shared_state.py`

---

### Layer 3: Adversarial Red-Teaming - Logic Stress-Testing

**Purpose**: Validate strategies survive extreme market conditions before deployment

**How It Works**:
- Simulates **-20% flash crash** against proposed strategy
- Validates stop-loss triggers activate correctly
- Calculates maximum drawdown during stress test
- Rejects strategies with drawdown > 15%

**Debate Protocol**:
```
Architect (V3): "I propose aggressive momentum strategy"
Auditor (R1):   "Flash crash test shows 25% drawdown - REJECTED"
Architect (V3): "Revised strategy with 5% stop-loss"
Auditor (R1):   "Stress test passed: 8% drawdown - APPROVED"
```

**Validation Gates**:
```python
✓ Flash crash simulation: -20% price drop
✓ Stop-loss requirement: Must exist and trigger
✓ Max drawdown: < 15%
✓ Recovery behavior: Must not enter infinite loss
```

**Key Files**: `core/adversary.py`

---

### Layer 4: Shadow Engine - Comparative Performance Auditing

**Purpose**: Test high-risk strategies in parallel without capital exposure

**How It Works**:
- Runs **Shadow Strategy** with 2x leverage in memory only
- Receives same market signals as live strategy
- Tracks Shadow ROI vs Live ROI continuously
- Generates **Promotion Alert** when Shadow outperforms

**Promotion Criteria**:
```python
if shadow_iterations >= 100:
    if shadow_sharpe > 1.2 and shadow_sharpe > live_sharpe * 1.1:
        # Alert: Shadow strategy ready for promotion
        promote_shadow_to_live()
```

**Benefits**:
- Zero-risk experimentation
- Continuous strategy improvement
- Data-driven promotion decisions
- Real market validation without capital exposure

**Key Files**: `core/shadow_engine.py`

---

### Layer 5: Hard Guardrails - Kill-Switch & Stability Lock

**Purpose**: Circuit breakers for catastrophic scenarios

**3% Kill-Switch**:
```python
# Monitor 1-hour equity change
if (current_equity - equity_1h_ago) / equity_1h_ago <= -0.03:
    kill_switch_triggered = True
    halt_all_trading()
    log_critical_alert()
```

**Behavior**:
- Monitors equity every update
- Tracks 1-hour rolling window
- Triggers on 3% loss in 1 hour
- **Halts all trading** immediately
- Requires manual reset

**12-Hour Stability Lock**:
```python
if last_evolution_time + timedelta(hours=12) > now:
    reject_evolution("Stability lock active")
```

**Behavior**:
- Enforces 12-hour cooldown between strategy evolutions
- Prevents rapid strategy churn
- Allows performance stabilization
- Protects against over-optimization

**Additional Guardrails**:
- Syntax validation before code execution
- Logic audit (AST parsing)
- Blacklist for failed strategies
- Automatic rollback on errors

**Key Files**: `guardrails.py`

---

## Execution Flow: Data Path Mapping

### Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA EXECUTION FLOW                         │
└─────────────────────────────────────────────────────────────────┘

[WEEX API]
    ↓ fetch_ohlcv()
    ↓
[Discovery Agent] ──→ Raw OHLCV Data [timestamp, O, H, L, C, V]
    ↓
    ↓ format & validate
    ↓
[SharedState] ←──────← [TradFi Oracle] ← Alpaca API (SPY/QQQ)
    ↑                       ↓
    ↑                  global_risk_level
    ↑
    ↑                  [Narrative Pulse] ← Exchange APIs (Whale Data)
    ↑                       ↓
    └──────────────← whale_dump_risk
    ↑
    ↑                  [Sentiment Agent] ← Fear & Greed API
    └──────────────← sentiment_multiplier
    
    ↓
[R1 Reasoning Loop]
    ↓ analyze_market()
    ↓
{Low Confidence?} ──Yes──→ [Architect V3]
    ↓                           ↓
    No                     generate_code()
    ↓                           ↓
[Active Logic]            [Backtester] → {Pass?} ──Yes──→ [Adversarial Red Team]
    ↓                                                            ↓
get_signal()                                              {Pass Flash Crash?}
    ↓                                                            ↓
[Position Calculator]                                          Yes
    ↓                                                            ↓
base_size × risk × sentiment × whale                  [Update active_logic.py]
    ↓
[Guardrails]
    ↓
{Kill-Switch?} ──Yes──→ HALT
    ↓
    No
    ↓
[WEEX Executor]
    ↓
[Live Trade]
    ↓
[Shadow Engine] (parallel simulation)
    ↓
[Performance Metrics] ──→ Dashboard
```

---

## Component Details

### 1. WEEX API → Discovery Agent

**File**: `discovery_agent.py`

**Responsibilities**:
- Initialize CCXT exchange connection
- Fetch OHLCV data (15-minute candles)
- Validate API credentials
- Handle rate limiting
- Error recovery with retries

**Data Format**:
```python
[
    [timestamp_ms, open, high, low, close, volume],
    [1704067200000, 42500.0, 42800.0, 42400.0, 42650.0, 145.32],
    ...
]
```

---

### 2. Discovery Agent → SharedState

**File**: `data/shared_state.py`

**Responsibilities**:
- **Thread-safe singleton** for global state
- Stores `global_risk_level` (NORMAL/HIGH)
- Stores `sentiment_multiplier` (0.5 to 1.5)
- Stores `whale_dump_risk` (boolean flag)
- Provides atomic read/write operations

**Access Pattern**:
```python
from data.shared_state import get_shared_state

state = get_shared_state()  # Singleton instance
risk = state.get_global_risk_level()
sentiment = state.get_sentiment_multiplier()
whale_risk = state.get_whale_dump_risk()
```

---

### 3. SharedState → R1 Reasoning Loop

**File**: `reasoning_loop.py`

**Responsibilities**:
- Runs every 15 minutes
- Fetches OHLCV from Discovery Agent
- Queries SharedState for global context
- Sends data to DeepSeek R1 for analysis
- Generates confidence score (0.0 to 1.0)
- Suggests evolution if confidence < 0.7

**R1 Prompt Structure**:
```
"Analyze BTC/USDT market with:
- OHLCV data (last 100 candles)
- Global risk level: {risk_level}
- Sentiment multiplier: {sentiment}
- Whale dump risk: {whale_risk}

Provide:
1. Market analysis
2. Trading signal (BUY/SELL/HOLD)
3. Confidence (0.0-1.0)
4. Evolution suggestion (if confidence < 0.7)"
```

---

### 4. R1 Analysis → Architect V3

**File**: `architect.py`

**Responsibilities**:
- Triggered when R1 confidence < 0.7
- Receives evolution suggestion from R1
- Uses DeepSeek V3 to generate new strategy code
- Validates syntax (AST parsing)
- Runs backtester validation
- Sends to Adversarial Red Team
- Deploys if all gates pass

**Code Generation**:
```python
# V3 receives:
suggestion = {
    'reason': "Current strategy underperforms in ranging markets",
    'proposed_changes': "Add Bollinger Bands mean reversion"
}

# V3 generates:
new_code = """
def get_signal(ohlcv, shared_state):
    # New strategy with Bollinger Bands
    ...
"""
```

---

### 5. Architect → Executor

**File**: `active_logic.py` (dynamically updated)

**Responsibilities**:
- Contains current live trading strategy
- Exports `get_signal()` function
- Receives OHLCV and SharedState
- Returns signal dictionary:

```python
{
    'action': 'BUY' | 'SELL' | 'HOLD',
    'confidence': 0.8,
    'stop_loss': 0.05,  # 5% stop loss
    'take_profit': 0.10  # 10% take profit
}
```

**Position Sizing Logic**:
```python
# In main execution loop:
base_size = 1000  # $1000 base position

# Apply multipliers from SharedState
risk_multiplier = 0.5 if global_risk_level == HIGH else 1.0
sentiment_mult = sentiment_multiplier  # 0.5 to 1.5
whale_mult = 0.7 if whale_dump_risk else 1.0

final_size = base_size * risk_multiplier * sentiment_mult * whale_mult
```

---

## Safety Checkpoints Summary

| Layer | Trigger | Action | Override |
|-------|---------|--------|----------|
| **TradFi Oracle** | SPY < -1% | Reduce positions 50% | Manual only |
| **Narrative Pulse** | BTC inflow > 1000 | Reduce positions 30% | Auto-expire 24h |
| **Adversarial Alpha** | Drawdown > 15% in test | Reject strategy | None |
| **Shadow Engine** | Shadow Sharpe > 1.2 for 100+ iter | Promote alert | Manual approval |
| **Kill-Switch** | Equity drop > 3% in 1h | HALT trading | Manual reset |
| **Stability Lock** | Evolution < 12h ago | Block evolution | Emergency override |

---

## Dashboard Integration

**File**: `dashboard/app.py`

The Streamlit dashboard provides real-time visualization of:

1. **Current Position**: Live trades and P&L
2. **Global Risk State**: TradFi Oracle + Narrative Pulse + Sentiment
3. **Shadow Performance**: Shadow vs Live ROI comparison
4. **Evolution History**: Strategy changes and performance
5. **Adversarial Audit Log**: Red Team test results
6. **Kill-Switch Status**: Guardrail states

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **AI Reasoning** | DeepSeek R1 | Market analysis, strategy audit |
| **Code Generation** | DeepSeek V3 | Strategy evolution, code synthesis |
| **Exchange API** | CCXT + Custom WEEX Client | Multi-exchange connectivity |
| **TradFi Data** | Alpaca API | SPY/QQQ market data |
| **Backtesting** | Pandas + NumPy | Vectorized strategy validation |
| **State Management** | Threading + Singleton | Thread-safe shared state |
| **Dashboard** | Streamlit + Plotly | Real-time visualization |
| **Testing** | Pytest | 72 comprehensive tests |

---

## Performance Metrics

AlphaWEEX tracks and optimizes for:

- **Sharpe Ratio**: Risk-adjusted returns (target > 1.2)
- **Maximum Drawdown**: Peak-to-trough decline (limit < 5%)
- **Win Rate**: Percentage of profitable trades
- **ROI**: Return on investment (%)
- **Confidence Score**: R1's belief in current strategy (0.0-1.0)

---

## Conclusion

AlphaWEEX's architecture achieves **autonomous evolution** while maintaining **professional risk management** through:

1. **Recursive feedback loop** between R1 auditor and V3 architect
2. **5-layer safety shield** with redundant protection mechanisms
3. **Clear data flow** from WEEX API through SharedState to execution
4. **Comprehensive validation** via backtesting and adversarial testing
5. **Hard guardrails** preventing catastrophic losses

This architecture enables the system to **continuously improve** while **never compromising safety**.
