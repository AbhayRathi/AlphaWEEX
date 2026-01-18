# Symbol Format Fix for Market Data Endpoints

## Issue
The bot was experiencing HTTP 400 errors when requesting market data (klines, funding rate, order book, ticker) with the error message: "Parameter symbol is invalid".

## Root Cause
The code was incorrectly transforming symbol names for market data endpoints:
- Input: `cmt_btcusdt`
- Transformed to: `BTCUSDT` (first attempt)
- Then tried: `BTCUSDT_SPBL` (fallback attempt)
- Both attempts failed with HTTP 400 errors

## Solution
Market data endpoints require the **original symbol format** with the `cmt_` prefix preserved. The fix updates the following methods in `core/weex_v2_client.py`:

1. `get_market_klines()` - Removed symbol transformation
2. `get_funding_rate()` - Removed symbol transformation
3. `get_order_book()` - Removed symbol transformation
4. `get_ticker()` - Removed symbol transformation

### Before (Incorrect)
```python
# Symbol transformation for market data endpoints
transformed_symbol = symbol.replace('cmt_', '').upper()  # "cmt_btcusdt" -> "BTCUSDT"
```

### After (Correct)
```python
# Use symbol as-is for market data endpoints
query_params = f"?symbol={urllib.parse.quote(symbol)}"  # "cmt_btcusdt" preserved
```

## Important Notes

### Symbol Formats by Endpoint Type

**Market Data Endpoints (Public)** - Use original symbol with `cmt_` prefix:
- `/capi/v2/market/candles` → `cmt_btcusdt`
- `/capi/v2/market/funding-rate` → `cmt_btcusdt`
- `/capi/v2/market/depth` → `cmt_btcusdt`
- `/capi/v2/market/ticker` → `cmt_btcusdt`

**Trading Endpoints (Private)** - Use original symbol with `cmt_` prefix:
- `/capi/v2/order/place` → `cmt_btcusdt`
- `/capi/v2/account/leverage` → `cmt_btcusdt`
- All other trading/account endpoints → `cmt_btcusdt`

## Testing
All tests have been updated and pass successfully:
```bash
pytest tests/test_competition_bot.py::TestWEEXv2Client -v
```

## Impact
✅ Fixes HTTP 400 errors for all market data requests
✅ Bot can now successfully fetch klines, funding rates, order books, and ticker data
✅ Simplifies code by removing unnecessary symbol transformations
✅ Removes the `_SPBL` suffix fallback logic

## Files Modified
- `core/weex_v2_client.py` - Updated 4 methods to preserve symbol format
- `tests/test_competition_bot.py` - Updated test expectations
