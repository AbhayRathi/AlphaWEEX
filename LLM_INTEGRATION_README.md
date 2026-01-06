# LLM Integration & SQLite Persistence

This document describes the autonomous LLM reasoning and SQLite persistence features added to the AlphaWEEX trading bot.

## Overview

The bot now uses AI (Large Language Models) to make trading decisions instead of simple RSI/SMA indicators. It also maintains a memory of past trades to learn and improve over time.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Competition Trading Bot                     │
└─────────────────────────────────────────────────────────────┘
                    │                   │
        ┌───────────┴────────┐  ┌───────┴──────────┐
        │                    │  │                   │
        ▼                    ▼  ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌─────────────────┐
│  Strategy    │    │   Database   │    │   AI Trading    │
│   Engine     │◄───┤   Manager    │    │     Logger      │
│   (LLM)      │    │  (SQLite)    │    │     (JSON)      │
└──────────────┘    └──────────────┘    └─────────────────┘
        │                    │
        │ OpenAI/Anthropic   │ Trade History
        │                    │
        ▼                    ▼
   LLM Decision      Performance Memory
   (BUY/SELL/HOLD)   (Win Rate, P&L)
```

## Components

### 1. Database Manager (`core/db.py`)

**Purpose**: Persistent storage of trade history and performance metrics.

**Key Features**:
- SQLite database for lightweight, serverless storage
- Records every trade execution with timestamp, symbol, side, price, and outcome
- Calculates performance metrics (win rate, avg P&L, total P&L)
- Provides recent trade history for LLM context

**API**:
```python
from core.db import DatabaseManager

db = DatabaseManager("trading_memory.db")

# Record trade entry
trade_id = db.record_trade_entry(
    symbol="cmt_btcusdt",
    side="BUY",
    price=50000.0,
    size=0.1,
    reasoning="AI detected bullish momentum",
    confidence=0.85
)

# Record trade exit
db.record_trade_exit(
    symbol="cmt_btcusdt",
    exit_price=51000.0,
    outcome=2.0  # 2% profit
)

# Get recent performance for LLM
performance = db.get_recent_performance(limit=20)
# Returns: {
#   "total_trades": 10,
#   "win_rate": 0.7,
#   "avg_profit": 1.2,
#   "total_pnl": 12.0,
#   "recent_trades": [...]
# }
```

### 2. Strategy Engine (`core/strategy_engine.py`)

**Purpose**: LLM-powered trading decision engine.

**Key Features**:
- Supports OpenAI (GPT-4) and Anthropic (Claude)
- Formats market data (last 100 candles) into readable prompts
- Includes trade history in context for learning
- Requests structured JSON responses
- Validates and sanitizes LLM output

**API**:
```python
from core.strategy_engine import StrategyEngine

# Initialize with OpenAI
engine = StrategyEngine(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"  # optional
)

# Get trading decision
decision = engine.get_decision(
    symbol="cmt_btcusdt",
    klines=market_klines,  # Last 100 candles
    performance=db.get_recent_performance(),
    balance=1000.0,
    leverage=20
)

# Returns: {
#   "action": "BUY",
#   "confidence": 0.85,
#   "reasoning": "Market volume is increasing while price consolidates..."
# }
```

### 3. Updated Competition Bot (`competition_bot.py`)

**Integration Points**:

1. **Initialization**: Creates database and strategy engine
   ```python
   self.db = DatabaseManager("trading_memory.db")
   self.strategy_engine = StrategyEngine(provider="openai", api_key=LLM_API_KEY)
   ```

2. **Decision Making**: Uses LLM instead of RSI/SMA
   ```python
   decision = self.strategy_engine.get_decision(
       symbol=symbol,
       klines=klines,
       performance=self.db.get_recent_performance()
   )
   ```

3. **Trade Recording**: Stores outcomes for learning
   ```python
   # On entry
   self.db.record_trade_entry(symbol, side, price, size, reasoning, confidence)
   
   # On exit
   self.db.record_trade_exit(symbol, exit_price, pnl_pct)
   ```

4. **AI Reasoning Logging**: Populates logs with LLM explanation
   ```python
   self.ai_logger.log_trade_decision(
       symbol=symbol,
       action=decision["action"],
       reason=decision["reasoning"],  # Direct from LLM
       confidence=decision["confidence"]
   )
   ```

## Setup

### 1. Install Dependencies

```bash
pip install openai anthropic python-dotenv
```

Or use the updated requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create/update your `.env` file:

```bash
# WEEX API credentials
API_KEY=your_weex_api_key
API_SECRET=your_weex_api_secret
API_PASSWORD=your_weex_api_password

# LLM Configuration
LLM_PROVIDER=openai  # or 'anthropic'
OPENAI_API_KEY=sk-...  # Your OpenAI API key
# ANTHROPIC_API_KEY=sk-ant-...  # Alternative: Anthropic API key

# Optional: Override default model
# LLM_MODEL=gpt-4o-mini  # or claude-3-5-sonnet-20241022
```

### 3. Run the Bot

```bash
# Run with LLM strategy (default)
python competition_bot.py

# Or fallback to RSI/SMA if no API key
python competition_bot.py  # Will auto-fallback
```

## Example LLM Prompt

The strategy engine formats prompts like this:

```
You are an expert cryptocurrency trader managing a futures trading account with 20x leverage.

CURRENT SITUATION:
- Symbol: cmt_btcusdt
- Balance: $1000.00 USDT
- Leverage: 20x
- Timestamp: 2026-01-05 08:30:00

Market Data Summary:
- Current Price: $51040.00
- Price Change (period): +1.98%
- Average Volume: 1049500.00
- Data Points: 100 candles
- Price Range: $50050.00 - $51040.00

Recent Price Action (last 10 candles):
1. O: $50910.00, H: $51010.00, L: $50810.00, C: $50960.00, Vol: 1090000.00
2. O: $50960.00, H: $51060.00, L: $50860.00, C: $51010.00, Vol: 1091000.00
...

Trading Performance History:
- Total Trades: 10
- Win Rate: 70.0%
- Average P&L: +1.20%
- Total P&L: +12.00%
- Best Trade: +5.00%
- Worst Trade: -2.50%

Recent Trades:
1. BUY cmt_btcusdt: +2.00% P&L
2. BUY cmt_btcusdt: -1.00% P&L
...

TASK:
Based on the market data and our trading history, make a decision: should we BUY, SELL, or HOLD?

RESPONSE FORMAT:
You must respond with valid JSON in this exact format:
{
    "action": "BUY" or "SELL" or "HOLD",
    "confidence": 0.0 to 1.0,
    "reasoning": "Your detailed explanation..."
}
```

## Example LLM Response

```json
{
    "action": "BUY",
    "confidence": 0.85,
    "reasoning": "Market volume is increasing while price consolidates at the $51,000 support level. Our trading history shows a strong 70% win rate, suggesting our strategy is working. The recent 1.98% price increase with strong volume indicates bullish momentum. With 20x leverage and proper risk management, a BUY position is warranted to capture the potential breakout above resistance. Our $1000 balance can sustain minor drawdowns, and the technical setup aligns with our successful past trades."
}
```

## Testing

Run the test suite:

```bash
# Run LLM integration tests
pytest tests/test_llm_integration.py -v

# Run validation script
python validate_llm_integration.py
```

## Database Schema

The SQLite database has the following structure:

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    price REAL NOT NULL,
    size REAL NOT NULL,
    outcome REAL DEFAULT NULL,        -- P&L percentage
    exit_price REAL DEFAULT NULL,
    exit_timestamp TEXT DEFAULT NULL,
    reasoning TEXT DEFAULT NULL,      -- LLM reasoning
    confidence REAL DEFAULT NULL,     -- Confidence level
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Performance

- **LLM Latency**: ~1-3 seconds per decision (OpenAI GPT-4o-mini)
- **Database Writes**: Microseconds (SQLite)
- **Memory Usage**: Minimal (<10MB for 1000s of trades)
- **Cost**: ~$0.001-0.003 per trading decision (using GPT-4o-mini)

## Safety Features

1. **Fallback Mode**: If LLM fails or API key is missing, bot falls back to RSI/SMA strategy
2. **Confidence Threshold**: Only executes trades with confidence ≥ 0.65
3. **Response Validation**: Sanitizes LLM output to ensure valid actions
4. **Error Handling**: Defaults to HOLD on any LLM error
5. **Conservative Defaults**: LLM is instructed to be risk-averse

## Benefits

1. **Adaptive Strategy**: Learns from past trades, adjusting based on performance
2. **Contextual Decisions**: Considers market conditions holistically
3. **Explainable AI**: Every decision includes reasoning for transparency
4. **Memory**: Builds institutional knowledge over time
5. **Natural Language**: Can incorporate complex market narratives

## Limitations

1. **API Costs**: Each decision costs money (mitigated by using efficient models)
2. **Latency**: 1-3 second delay per decision (acceptable for 30s intervals)
3. **Rate Limits**: Subject to LLM provider's rate limits
4. **Hallucination Risk**: LLM may occasionally produce invalid reasoning
5. **Market Conditions**: Performance depends on LLM's training data recency

## Future Enhancements

- [ ] Fine-tune LLM on historical trading data
- [ ] Multi-timeframe analysis in prompts
- [ ] Sentiment analysis from news/social media
- [ ] Ensemble decisions (multiple LLMs voting)
- [ ] Reinforcement learning feedback loop
- [ ] Cost optimization (caching similar market states)

## Support

For issues or questions:
1. Check the validation script: `python validate_llm_integration.py`
2. Review test output: `pytest tests/test_llm_integration.py -v`
3. Examine logs: `ai_trading.log` and database: `trading_memory.db`

## License

Same as parent project (see LICENSE file).
