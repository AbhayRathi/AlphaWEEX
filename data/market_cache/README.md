# Market Cache Directory

This directory contains historical OHLCV data used for backtesting strategies.

## Data Format

CSV files with the following columns:
- `timestamp`: Unix timestamp in milliseconds
- `open`: Opening price
- `high`: Highest price in period
- `low`: Lowest price in period
- `close`: Closing price
- `volume`: Trading volume

## Current Data

### BTC_USDT.csv
- **Type**: Synthetic data generated for testing
- **Candles**: 1000
- **Timeframe**: 15 minutes
- **Price Range**: ~$40,000 - $46,000
- **Purpose**: Demo and testing of backtester

## Using Real Data

To use real market data:

1. Download historical data from your exchange
2. Convert to CSV format matching the columns above
3. Save with format: `{SYMBOL}.csv` (e.g., `BTC_USDT.csv`)
4. Place in this directory

Example using CCXT:

```python
import ccxt
import pandas as pd

exchange = ccxt.binance()
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=1000)

df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df.to_csv('data/market_cache/BTC_USDT.csv', index=False)
```

## Notes

- Timestamps should be in milliseconds
- Data should be sorted chronologically
- Minimum 100 candles recommended for meaningful backtest results
- 1000+ candles recommended for robust validation
