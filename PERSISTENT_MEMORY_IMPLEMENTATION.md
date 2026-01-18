# Persistent Trade Memory Implementation

## Overview
This implementation adds persistent trade memory to the AlphaWEEX trading bot, enabling:
- **Trade Journal**: JSON-based history of all closed trades
- **Position State Persistence**: Automatic saving/restoration of active position states
- **AI Context Enhancement**: LLM receives last 5 trades when making decisions

## Architecture

### Components

#### 1. TradeJournal (`core/trade_journal.py`)
A lightweight, thread-safe JSON journal for recording trade outcomes.

**Features:**
- Append-only trade history
- Records: timestamp, symbol, direction, profit/loss, AI reasoning, trigger type
- Thread-safe operations with lock mechanism
- Efficient retrieval of recent trades

**Usage:**
```python
from core.trade_journal import TradeJournal

journal = TradeJournal("data/trade_history.json")

# Record a trade exit
journal.append_trade(
    symbol="cmt_btcusdt",
    direction="LONG",
    profit_loss=2.5,
    ai_reason="Strong bullish momentum",
    entry_price=50000.0,
    exit_price=51250.0,
    trigger_type="PARTIAL_1"
)

# Get last 5 trades for AI context
recent = journal.get_recent_trades(limit=5)
```

#### 2. PositionStatePersistence (`core/position_state.py`)
Manages persistence of position scaling state for crash recovery.

**Features:**
- Saves `position_scaling_state` to disk
- Restores state on bot startup
- Thread-safe operations
- Automatic file creation

**Usage:**
```python
from core.position_state import PositionStatePersistence

state_mgr = PositionStatePersistence("data/active_positions.json")

# Save state (called every 10 seconds)
state_mgr.save_state(position_scaling_state)

# Load state on startup
saved_state = state_mgr.load_state()
```

#### 3. StrategyEngine Integration
The LLM strategy engine now includes trade history in its decision-making context.

**Changes:**
- Imports `TradeJournal` on initialization
- New method: `_format_journal_trades()` formats last 5 trades
- Updated `_build_prompt()` to include journal trades in LLM context

**Prompt Enhancement:**
```
[Past Perf]:
[Trading Performance from Database...]

[Last 5 Trade Results from Journal]:
1. LONG cmt_btcusdt: +2.50% (PARTIAL_1) - Strong bullish momentum with high RSI...
2. SHORT cmt_ethusdt: -1.20% (SL) - Resistance at key level, overbought conditions...
...
```

#### 4. CompetitionBot Integration
The main trading bot now persists trade data and position state.

**Initialization:**
```python
# Initialize trade journal
self.trade_journal = TradeJournal("data/trade_history.json")

# Initialize position state persistence
self.position_state = PositionStatePersistence("data/active_positions.json")

# Load saved position state on startup
saved_state = self.position_state.load_state()
if saved_state:
    self.client.position_scaling_state = saved_state
```

**Periodic State Saving:**
State is saved every 10 seconds in the main loop:
```python
if current_time - self.last_state_save_time >= 10:
    self.save_position_state()
    self.last_state_save_time = current_time
```

**Trade Recording:**
All trade exits are recorded in the journal:
- Stop Loss (SL)
- Partial Profit 1 (PARTIAL_1)
- Partial Profit 2 (PARTIAL_2)
- Full Target (FULL_TP)
- Max Hold Time (MAX_HOLD)

## Data Format

### Trade Journal Format (`data/trade_history.json`)
```json
[
  {
    "timestamp": "2026-01-18T05:30:00.123456",
    "symbol": "cmt_btcusdt",
    "direction": "LONG",
    "profit_loss": 2.5,
    "ai_reason": "Strong bullish momentum with high RSI",
    "entry_price": 50000.0,
    "exit_price": 51250.0,
    "trigger_type": "PARTIAL_1"
  }
]
```

### Position State Format (`data/active_positions.json`)
```json
{
  "cmt_btcusdt": {
    "partial_taken": true,
    "breakeven_set": true,
    "reinvested": false,
    "original_size": 0.001,
    "realized_profit": 0.25
  }
}
```

## Benefits

### 1. Crash Recovery
- Bot can resume managing positions after restart
- No loss of TP/SL state
- Position scaling state preserved

### 2. AI Context Enhancement
- LLM sees last 5 trade outcomes
- Learns from recent successes/failures
- More informed decision making

### 3. Performance Analysis
- Complete trade history available
- Easy to analyze patterns
- JSON format for easy parsing

### 4. Debugging
- Full audit trail of trades
- AI reasoning preserved for each trade
- Trigger types recorded

## Testing

### Unit Tests (`test_trade_journal.py`)
Run with:
```bash
python test_trade_journal.py
```

Tests:
- ✅ TradeJournal functionality
- ✅ PositionStatePersistence functionality
- ✅ Integration with bot components

### Workflow Validation (`validate_persistent_memory.py`)
Run with:
```bash
python validate_persistent_memory.py
```

Simulates:
- Fresh bot start
- Opening positions
- Hitting profit targets
- Bot restart/crash recovery
- Trade exits
- LLM reading trade history

## Configuration

### File Paths
Default paths can be changed during initialization:
```python
journal = TradeJournal("custom/path/trades.json")
state_mgr = PositionStatePersistence("custom/path/state.json")
```

### .gitignore
The following patterns are added to `.gitignore` to prevent committing trade data:
```
data/trade_history.json
data/active_positions.json
```

## Performance Considerations

### Thread Safety
- Both components use threading locks
- Safe for concurrent access
- No race conditions

### File I/O
- Position state: Written every 10 seconds
- Trade journal: Written on each trade exit (typically < 1/minute)
- Minimal I/O overhead

### Memory Usage
- Trade journal is append-only
- Consider implementing rotation for very long-running bots
- Current implementation: ~500 bytes per trade entry

## Migration Notes

### Existing Bots
When upgrading an existing bot:
1. Files will be created automatically on first run
2. No existing data will be lost
3. Position state starts fresh (no active positions on first restart)

### Backward Compatibility
- All changes are additive
- No breaking changes to existing functionality
- Bot works with or without trade history

## Future Enhancements

Possible improvements:
1. **Journal Rotation**: Archive old trades after N entries
2. **Performance Metrics**: Calculate win rate, avg P&L in journal
3. **Symbol-Specific History**: Filter trades by symbol
4. **Time-Based Analysis**: Query trades by date range
5. **Export Functionality**: Export to CSV/Excel for analysis

## Troubleshooting

### Journal File Corruption
If the journal gets corrupted:
```python
journal.clear_journal()  # Start fresh
```

### Position State Issues
If position state is incorrect after restart:
```python
state_mgr.clear_state()  # Clear and start fresh
```

### Debugging
Enable debug logging to see file operations:
```python
import logging
logging.getLogger('core.trade_journal').setLevel(logging.DEBUG)
logging.getLogger('core.position_state').setLevel(logging.DEBUG)
```

## Code Quality

- ✅ Type hints throughout
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Thread-safe operations
- ✅ Clean separation of concerns
- ✅ Minimal dependencies (only stdlib)

## License

Same as AlphaWEEX project.
