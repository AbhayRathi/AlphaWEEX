# WEEX AI Wars Tournament Compliance Guide

This document describes the tournament-specific compliance features implemented in AlphaWEEX for the "AI Wars: WEEX Alpha Awakens" competition.

## Overview

The bot has been enhanced with mandatory features required for tournament participation and ranking eligibility:

1. **Fixed Leverage Lock (20x)**
2. **Symbol Whitelisting**
3. **Auto-Initialization (Frozen Balance Detection)**
4. **Minimum Trade Count Tracking**
5. **AI Log Engine (Competition Submission Requirement)**
6. **Self-Healing (Error Recovery)**

---

## 1. Fixed Leverage Lock

### Requirement
All trades must use exactly **20x leverage**. Trading with higher leverage results in immediate disqualification.

### Implementation
- Leverage is set to 20x on bot startup for all symbols
- Before placing each order, the bot verifies and forces 20x leverage
- If leverage verification fails, the trade is skipped

### Code Location
- `competition_bot.py`: `initialize_leverage()` method (startup)
- `competition_bot.py`: Leverage verification before `place_market_order()` calls

### Verification
```python
# Logs show leverage enforcement:
# "⚙️ Initializing leverage to 20x for all symbols..."
# "Tournament Compliance: Verify 20x leverage before placing order"
```

---

## 2. Symbol Whitelisting

### Requirement
Only approved tournament pairs are allowed:
- `cmt_btcusdt` (Bitcoin)
- `cmt_ethusdt` (Ethereum)
- `cmt_solusdt` (Solana)
- `cmt_dogeusdt` (Dogecoin)
- `cmt_xrpusdt` (XRP)
- `cmt_adausdt` (Cardano)
- `cmt_bnbusdt` (Binance Coin)
- `cmt_ltcusdt` (Litecoin)

### Implementation
- Symbol list is defined in `SYMBOL_LIST` constant
- Bot only processes symbols in the whitelist
- The main loop iterates only over approved symbols

### Code Location
- `competition_bot.py`: Lines 52-62

---

## 3. Auto-Initialization

### Requirement
Detect "frozen" balance at startup (Equity > 0 but Available = 0) and automatically:
1. Close all open positions
2. Cancel all pending orders

### Implementation
- `check_frozen_balance()`: Detects frozen balance condition
- `auto_initialize()`: Executes cleanup if frozen balance detected
- Called automatically in the `run()` method before trading starts

### Code Location
- `competition_bot.py`: `check_frozen_balance()` method
- `competition_bot.py`: `auto_initialize()` method
- `core/weex_v2_client.py`: `close_all_positions()` and `cancel_all_orders()` methods

### Logs
```
🔧 Running auto-initialization check...
✅ No frozen balance detected - ready to trade
# OR
⚠️ Frozen balance detected - executing auto-initialization...
1️⃣ Closing all positions...
2️⃣ Cancelling all orders...
✅ Auto-initialization complete - balance unfrozen
```

---

## 4. Minimum Trade Count

### Requirement
At least **10 valid trades** are required to qualify for tournament ranking.

### Implementation
- `valid_trade_count`: Counter incremented on every successful trade
- `min_required_trades`: Set to 10 (configurable)
- Progress displayed after each trade

### Code Location
- `competition_bot.py`: `__init__()` method (initialization)
- `competition_bot.py`: `process_symbol()` method (increment on trade)

### Logs
```
📊 Valid trade count: 5/10
📊 Valid trade count: 10/10  # Eligible for ranking
```

---

## 5. AI Log Engine

### Requirement
WEEX requires an **AI Log** for every trade that proves LLM decision-making. Logs must include:
- Timestamp (ISO 8601 format)
- Model version
- Input data (RSI, funding rate, sentiment, etc.)
- AI reasoning
- Order details (symbol, side, size, leverage)

### Implementation
#### Module: `logging_engine.py`
- `AILogEngine`: Main class for generating AI logs
- `generate_trade_log()`: Creates JSON log for each trade
- `generate_decision_log()`: Creates JSON log for decisions (including HOLD)

#### Storage
- Logs are stored in `ai_logs/` directory
- Filename format: `trade_2026-01-22T08-00-00_123456Z.json`
- One JSON file per trade

#### Log Format
```json
{
  "timestamp": "2026-01-22T08:00:00Z",
  "model_version": "GPT-4o-Competition-V1",
  "inputs": {
    "rsi": 32.5,
    "funding_rate": 0.01,
    "sentiment_score": 0.85,
    "current_price": 43250.50
  },
  "ai_reasoning": "RSI oversold on 15m chart with positive news sentiment. Executing Long.",
  "order_details": {
    "symbol": "cmt_btcusdt",
    "side": "buy",
    "size": "0.001",
    "leverage": "20"
  },
  "trade_id": "abc123xyz"
}
```

### Integration
- Called automatically in `competition_bot.py` after successful order placement
- Logs are generated for both BUY and SELL orders
- Model version adapts based on strategy (LLM provider or "RSI-SMA-Competition-V1")

### Code Location
- `logging_engine.py`: Full implementation
- `competition_bot.py`: Integration in `process_symbol()` method
- `.gitignore`: `ai_logs/` directory excluded from git

### Verification
```bash
# Run tests
python -m unittest tests.test_logging_engine -v

# Verify logs
ls -la ai_logs/
cat ai_logs/trade_*.json | jq .
```

---

## 6. Self-Healing (Error Recovery)

### Requirement
Handle **Error 40015 (Insufficient Balance)** by automatically closing positions to release margin.

### Implementation
- Error detection in `place_market_order()` response handling
- Automatic trigger of `close_all_positions()` when error detected
- Logs the self-healing action

### Code Location
- `core/weex_v2_client.py`: `place_market_order()` method (error detection)
- `core/weex_v2_client.py`: `close_all_positions()` method (recovery action)

### Logs
```
🚨 Error 40015: Insufficient Balance detected for cmt_btcusdt
🔧 Self-healing: Triggering closePositions...
✅ Self-healing: All positions closed
```

---

## Market Order Logic

### Numeric Type Codes
The bot uses numeric side codes for WEEX V2 API compatibility:
- `"1"`: Open Long (BUY)
- `"2"`: Open Short (SELL)
- `"3"`: Close Long
- `"4"`: Close Short

These are defined in `core/weex_v2_client.py`:
```python
side_map = {
    "BUY": "1", "SELL": "2",
    "CLOSE_LONG": "3", "CLOSE_SHORT": "4"
}
```

---

## Testing

### Unit Tests
```bash
# Test logging engine
python -m unittest tests.test_logging_engine -v

# Output:
# test_cleanup_old_logs ... ok
# test_generate_decision_log ... ok
# test_generate_trade_log ... ok
# test_get_log_count ... ok
# test_get_trade_log_count ... ok
# test_init_creates_directory ... ok
# test_log_format_compliance ... ok
# 
# Ran 7 tests in 0.006s
# OK
```

### Verification Script
```bash
# Run comprehensive verification
python verify_tournament_compliance.py

# Output:
# ============================================================
# TOURNAMENT COMPLIANCE VERIFICATION
# ============================================================
# 
# Testing AILogEngine ... ✅ PASSED
# Testing WEEXv2Client Updates ... ✅ PASSED
# Testing CompetitionTradingBot Updates ... ✅ PASSED
# 
# ✅ ALL TESTS PASSED
```

---

## Usage

### Running the Bot
```bash
# The bot now automatically:
# 1. Checks for frozen balance (auto-initialization)
# 2. Sets 20x leverage for all symbols
# 3. Tracks trade count (displays progress)
# 4. Generates AI logs for every trade
# 5. Self-heals on error 40015

python competition_bot.py
```

### Monitoring Trade Count
Check the logs for tournament eligibility:
```
📊 Tournament Compliance: Minimum 10 trades required for ranking
📊 Valid trade count: 1/10
📊 Valid trade count: 2/10
...
📊 Valid trade count: 10/10  # ✅ Eligible for ranking
```

### Submitting AI Logs
```bash
# Collect logs for submission
tar -czf ai_logs_submission.tar.gz ai_logs/

# Verify log count
python -c "from logging_engine import AILogEngine; e = AILogEngine(); print(f'Trade logs: {e.get_trade_log_count()}')"
```

---

## Troubleshooting

### Frozen Balance
**Symptom**: Bot detects frozen balance at startup
```
⚠️ Frozen balance detected: Equity=1000, Available=0
```

**Resolution**: Auto-initialization will automatically close positions and cancel orders. No manual intervention needed.

### Leverage Verification Failed
**Symptom**: Trade skipped with leverage warning
```
⚠️ Failed to verify 20x leverage for cmt_btcusdt - skipping trade
```

**Resolution**: Check API connection and permissions. The bot will retry on next cycle.

### Error 40015
**Symptom**: Insufficient balance error
```
🚨 Error 40015: Insufficient Balance detected
```

**Resolution**: Self-healing will automatically close positions. The bot continues running.

### Missing AI Logs
**Symptom**: No files in `ai_logs/` directory

**Resolution**: Ensure trades are actually being placed. Check bot logs for order execution messages.

---

## Configuration

### Constants (in `competition_bot.py`)
```python
# Tournament compliance
SYMBOL_LIST = [...]  # Whitelist of approved symbols

# Competition bot class initialization
self.valid_trade_count = 0      # Tracks valid trades
self.min_required_trades = 10   # Minimum for ranking

# Leverage (forced to 20x)
# No configuration needed - enforced automatically
```

---

## Code Review Summary

### New Files
- `logging_engine.py`: AI Log Engine implementation
- `tests/test_logging_engine.py`: Unit tests for AI logging
- `verify_tournament_compliance.py`: Manual verification script
- `TOURNAMENT_COMPLIANCE_GUIDE.md`: This documentation

### Modified Files
- `competition_bot.py`: Added auto-init, leverage enforcement, trade counting, AI logging integration
- `core/weex_v2_client.py`: Added self-healing, `close_all_positions()`, `cancel_all_orders()`
- `.gitignore`: Exclude `ai_logs/` directory

### Lines Changed
- Added: ~436 lines
- Modified: ~100 lines
- Total impact: ~536 lines

---

## Compliance Checklist

Before tournament participation, verify:

- [ ] Bot initializes with 20x leverage for all symbols
- [ ] Only approved symbols (8 pairs) are traded
- [ ] Auto-initialization runs on startup
- [ ] Trade counter displays and increments
- [ ] AI logs are generated in `ai_logs/`
- [ ] Log format meets WEEX requirements (JSON structure)
- [ ] Self-healing triggers on Error 40015
- [ ] At least 10 valid trades completed before round ends

---

## Support

For issues or questions:
1. Check logs for error messages
2. Run verification script: `python verify_tournament_compliance.py`
3. Review this documentation
4. Check WEEX tournament rules and API documentation

---

## License

This implementation is part of AlphaWEEX and follows the repository's license.
