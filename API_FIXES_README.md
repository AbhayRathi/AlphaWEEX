# WEEX API Fixes Applied

This document describes the API endpoint fixes applied to resolve 404/400 errors in the WEEX v2 API client.

## Leverage Endpoint

### Fixed Implementation (Latest - AI Wars Competition)
- **Correct Path:** `/api/v2/account/set-leverage`
- **Method:** POST
- **Body:** 
  ```json
  {
    "symbol": "cmt_btcusdt",
    "marginMode": 1,
    "leverage": 20
  }
  ```
- **Note:** 
  - `marginMode` must be an **integer**: 1 for Isolated, 2 for Cross
  - `leverage` must be an **integer**, not a string
  - "Already set" responses are treated as success

### Previous Implementation (Incorrect)
- **Path:** `/capi/v2/account/leverage` ❌
- **Path (Old Fix):** `/capi/v2/account/setLeverage` ❌ (CamelCase)
- **Body:** `{"symbol": "cmt_btcusdt", "marginMode": "isolated", "leverage": "10"}` ❌

### Why This Fix Was Needed
The WEEX API v2 for AI Wars Competition requires:
1. The correct endpoint path `/api/v2/account/set-leverage` (hyphenated, lowercase)
2. A `marginMode` field as an **integer** (1 = Isolated, 2 = Cross)
3. The `leverage` value as an **integer**, not a string
4. Graceful handling when leverage is already set (not an error condition)

## Positions Endpoint

### Fixed Implementation (Latest - AI Wars Competition)
- **Correct Path:** `/api/v2/account/all-position`
- **Fallback Path:** `/api/v2/account/position/all-position` (if primary returns 404)
- **Method:** GET
- **Query Parameters:** `?symbol={symbol}` (optional)
- **Note:** Returns all positions for the account

### Previous Implementation (Incorrect)
- **Path:** `/capi/v2/account/positions` ❌ (returns 404 error)
- **Path (Old Fix):** `/capi/v2/account/allPosition` ❌ (CamelCase)

### Why This Fix Was Needed
The WEEX API v2 for AI Wars Competition changed the positions endpoint path. Using hyphenated lowercase paths (`/api/v2/account/all-position`) instead of CamelCase paths. A fallback endpoint is also provided in case the primary endpoint returns a 404.

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

1. **test_set_leverage_endpoint** - Verifies correct path (`/api/v2/account/set-leverage`) and body format (integer marginMode and leverage)
2. **test_set_leverage_already_set_handling** - Verifies "already set" is handled as success
3. **test_margin_mode_isolated** - Verifies marginMode is integer 1 for isolated mode
4. **test_get_klines_granularity_parameter** - Verifies granularity parameter is used

Run tests with:
```bash
pytest tests/test_competition_bot.py::TestWEEXv2Client -v
```

Validate fixes with:
```bash
python3 validate_api_fixes.py
```

## Impact

These fixes resolve:
- ✅ 404 errors when setting leverage (updated to correct endpoint path `/api/v2/account/set-leverage` with hyphens)
- ✅ 400 errors when setting leverage (marginMode as integer, leverage as integer)
- ✅ 404 errors when fetching positions (updated to `/api/v2/account/all-position` with hyphens and fallback support)
- ✅ 400 errors when fetching candle data (wrong parameter name)
- ✅ False error reports when leverage is already set correctly
- ✅ Added request URL logging for debugging

## Files Modified

- `core/weex_v2_client.py` - Core API client with endpoint fixes and logging
- `tests/test_competition_bot.py` - Updated tests to verify new endpoints
- `API_FIXES_README.md` - Documentation updated for AI Wars Competition
- `tests/test_competition_bot.py` - Added comprehensive tests for new behavior

## No Breaking Changes

These fixes only correct the API integration. No changes were made to:
- Database layer (`core/db.py`)
- Strategy engine (`core/strategy_engine.py`)
- Competition bot logic (`competition_bot.py`)
- AI logger (`core/ai_logger.py`)

All existing functionality remains intact.
