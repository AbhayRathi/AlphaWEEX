# WEEX API Fixes Applied

This document describes the API endpoint fixes applied to resolve 404/400 errors in the WEEX v2 API client.

## Leverage Endpoint

### Fixed Implementation
- **Correct Path:** `/capi/v2/account/leverage`
- **Method:** POST
- **Body:** 
  ```json
  {
    "symbol": "cmt_btcusdt",
    "marginMode": "crossed",
    "leverage": "10"
  }
  ```
- **Note:** Leverage must be a string, not an integer. "Already set" responses are treated as success.

### Previous Implementation (Incorrect)
- **Path:** `/capi/v2/account/setLeverage` ❌
- **Body:** `{"symbol": "cmt_btcusdt", "leverage": 10}` ❌

### Why This Fix Was Needed
The WEEX API v2 requires:
1. The correct endpoint path `/capi/v2/account/leverage`
2. A `marginMode` field set to `"crossed"` in the request body
3. The `leverage` value as a string, not an integer
4. Graceful handling when leverage is already set (not an error condition)

## Candles Endpoint

### Fixed Implementation
- **Correct Path:** `/capi/v2/market/candles`
- **Parameters:** `?symbol={symbol}&granularity={interval}&limit={limit}`
- **Note:** Use `granularity` parameter instead of `interval`

### Previous Implementation (Incorrect)
- **Parameters:** `?symbol={symbol}&interval={interval}&limit={limit}` ❌

### Why This Fix Was Needed
The WEEX API v2 expects the time interval parameter to be named `granularity`, not `interval`. Using the wrong parameter name results in 400 Bad Request errors.

## Valid Granularities

The following time intervals are supported:
- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `30m` - 30 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day

## Testing

All changes have been tested with comprehensive unit tests in `tests/test_competition_bot.py`:

1. **test_set_leverage_endpoint** - Verifies correct path and body format
2. **test_set_leverage_already_set_handling** - Verifies "already set" is handled as success
3. **test_get_klines_granularity_parameter** - Verifies granularity parameter is used

Run tests with:
```bash
pytest tests/test_competition_bot.py::TestWEEXv2Client -v
```

## Impact

These fixes resolve:
- ✅ 404 errors when setting leverage (wrong endpoint path)
- ✅ 400 errors when setting leverage (missing marginMode, wrong leverage type)
- ✅ 400 errors when fetching candle data (wrong parameter name)
- ✅ False error reports when leverage is already set correctly

## Files Modified

- `core/weex_v2_client.py` - Core API client with endpoint fixes
- `tests/test_competition_bot.py` - Added comprehensive tests for new behavior

## No Breaking Changes

These fixes only correct the API integration. No changes were made to:
- Database layer (`core/db.py`)
- Strategy engine (`core/strategy_engine.py`)
- Competition bot logic (`competition_bot.py`)
- AI logger (`core/ai_logger.py`)

All existing functionality remains intact.
