# WEEX AI Trading Bot - Competition-Ready Implementation

## Overview

This is a **competition-ready** WEEX AI trading bot implementing all required features for the WEEX Trading Competition.

## Features Implemented

### ✅ 1. Working Authentication
- Uses WEEX v2 API (`https://api-contract.weex.com`)
- Proper HMAC SHA256 signature generation (Base64 encoded)
- Verified authentication headers:
  - `ACCESS-KEY`
  - `ACCESS-SIGN`
  - `ACCESS-TIMESTAMP`
  - `ACCESS-PASSPHRASE`

### ✅ 2. Multi-Symbol Flexibility
- Supports multiple trading symbols: `["cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt"]`
- Loops through symbols to check for opportunities
- Configurable symbol list in `competition_bot.py`

### ✅ 3. K-lines Data Retrieval
- Implements `get_market_klines(symbol, interval='1m', limit=100)`
- Uses endpoint: `/capi/v2/market/candles`
- Data passed to Decision Engine for analysis

### ✅ 4. Risk Management (TP/SL)
- **2% Take-Profit**: Automatically closes position at 2% gain
- **1% Stop-Loss**: Automatically closes position at 1% loss
- Tracks open positions in real-time
- Executes market close when targets hit

### ✅ 5. Enhanced AI Logging
- Log file: `ai_trading.log`
- **Single-line JSON format** for each entry
- **10-minute heartbeat**: Logs market sentiment even when no trades
- Example heartbeat: `"RSI is 50, Neutral stance"`
- Tracks: trades, orders, TP/SL triggers, errors, cooldowns

### ✅ 6. Safety Guardrails
- **20x Leverage**: Forced on startup for all symbols
- **Position Check**: `has_open_position()` prevents double-spending
- **60-second Cooldown**: Activated after 521 Error (Firewall)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.env` file (or create from `.env.example`):

```bash
# WEEX v2 API Configuration
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
API_PASSWORD=your_api_password_here
```

### 3. Run the Bot

```bash
python competition_bot.py
```

## Architecture

### Core Components

1. **`core/weex_v2_client.py`** - WEEX v2 API Client
   - Authentication & signature generation
   - K-lines data retrieval
   - Position management
   - TP/SL checking
   - 521 error cooldown

2. **`core/ai_logger.py`** - Enhanced AI Logger
   - JSON format logging
   - 10-minute heartbeat
   - Trade/order tracking
   - Error logging

3. **`competition_bot.py`** - Main Trading Bot
   - Multi-symbol processing
   - Decision engine (RSI, SMA)
   - Signal generation
   - Trade execution
   - TP/SL monitoring

## Trading Logic

### Decision Engine

The bot uses a simple but effective strategy:

1. **RSI (Relative Strength Index)**:
   - RSI < 30 → Oversold → BUY signal
   - RSI > 70 → Overbought → SELL signal

2. **Moving Averages**:
   - SMA 20 and SMA 50
   - Golden cross → BUY signal
   - Price above/below MA → Trend confirmation

3. **Volume Analysis**:
   - Volume ratio > 1.2 → Strong momentum
   - Used to confirm signals

### Risk Management

- **Entry**: Only BUY if no existing position (safety check)
- **Exit**: Automatic TP/SL monitoring every iteration
- **Position Size**: Configurable (default: 0.001)

## Log Format

All logs are in single-line JSON format:

```json
{"type": "HEARTBEAT", "timestamp": "2026-01-05T06:15:00", "market_sentiment": "RSI is 50, Neutral stance", "market_data": {...}}
{"type": "TRADE_DECISION", "timestamp": "2026-01-05T06:15:30", "symbol": "cmt_btcusdt", "action": "BUY", "confidence": 0.75, ...}
{"type": "ORDER_EXECUTION", "timestamp": "2026-01-05T06:15:35", "symbol": "cmt_btcusdt", "side": "BUY", "size": 0.001, ...}
{"type": "TP_TRIGGER", "timestamp": "2026-01-05T06:25:00", "symbol": "cmt_btcusdt", "pnl_pct": 2.05, ...}
```

## Safety Features

### 1. 20x Leverage Lock
```python
# Set on startup
self.client.set_leverage(symbol, leverage=20)
```

### 2. Position Check
```python
# Before every BUY
if self.client.has_open_position(symbol):
    logger.info("Position exists, skipping BUY")
    return
```

### 3. 521 Error Cooldown
```python
# Automatic 60-second cooldown
if response.status_code == 521:
    self.last_521_error_time = time.time()
    raise Exception("521 Firewall Error - Cooldown initiated")
```

## Configuration

Edit `competition_bot.py` to customize:

```python
# Multi-Symbol Support
SYMBOL_LIST = ["cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt"]

# Risk Management
TAKE_PROFIT_PCT = 2.0  # 2% TP
STOP_LOSS_PCT = 1.0    # 1% SL

# Trading Parameters
POSITION_SIZE = 0.001  # Adjust based on capital
MAIN_LOOP_INTERVAL = 30  # Check every 30 seconds
```

## Testing

Run unit tests:

```bash
pytest tests/test_competition_bot.py -v
```

Tests cover:
- Signature generation
- TP/SL calculations
- JSON logging format
- Heartbeat intervals
- RSI/SMA calculations
- Signal generation

## Monitoring

### Real-time Logs

```bash
# Watch logs in real-time
tail -f ai_trading.log | jq .
```

### Log Statistics

The bot displays statistics every 10 iterations:
- Total heartbeats
- Trade decisions
- Order executions
- TP/SL triggers
- Errors

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/capi/v2/market/candles` | GET | Get K-lines data |
| `/api/v2/account/set-leverage` | POST | Set leverage |
| `/api/v2/account/all-position` | GET | Check positions |
| `/capi/v2/order/placeOrder` | POST | Place orders |

**Note:** Private account endpoints use `/api/v2/` prefix with hyphenated paths (e.g., `set-leverage`, `all-position`).

## Error Handling

- **521 Firewall Error**: 60-second cooldown
- **Network Timeout**: 10-second timeout per request
- **API Errors**: Logged to `ai_trading.log`
- **Position Errors**: Safe handling, no double-spending

## Performance

- **Multi-symbol**: Processes 3 symbols per iteration
- **Interval**: 30 seconds between iterations
- **Heartbeat**: Every 10 minutes
- **TP/SL Check**: Every iteration (real-time)

## License

See main project LICENSE file.

## Support

For issues or questions, please refer to the main project documentation or create an issue on GitHub.
