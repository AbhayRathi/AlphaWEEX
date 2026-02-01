# Symbol Resolution Implementation Summary - FINALIZED

## Overview
Successfully implemented **tolerant** contract discovery and symbol resolution to fix HTTP 400 "Parameter symbol is invalid" errors when calling WEEX V2 market/order endpoints. Now includes CI-friendly testing with override support.

## Problem Solved
Previously, the system used simple symbol cleaning (e.g., `BTCUSDT`), but WEEX V2 API requires official contract symbols (e.g., `BTCUSDT_UMCBL` for USDT-margined perpetual contracts).

## Solution Implemented

### 1. Tolerant Contract Discovery (`load_contracts()`)
- **Primary Endpoint**: `/capi/v2/market/contracts?productType=umcbl`
- **Fallback Endpoint**: `/capi/v2/public/contracts?productType=umcbl`
- **Caching**: Results cached for 60 minutes to minimize API calls
- **Mapping**: Builds internal symbol → exchange symbol dictionary
- **Graceful Degradation**: Falls back to `_UMCBL` suffix if discovery fails
- **CI Override**: Supports `WEEX_CONTRACT_MAP_OVERRIDE` env var for testing

#### Tolerant Field Parsing
Handles multiple field name variations:

**Exchange Symbol Fields** (tries in order):
- `symbol` (standard)
- `contractSymbol` (variation 1)
- `symbolName` (variation 2)
- `productId` (fallback)

**Base Coin Fields** (tries in order):
- `baseCoin` (standard)
- `base` (variation 1)
- `baseCurrency` (variation 2)

**Quote Coin Fields** (tries in order):
- `quoteCoin` (standard)
- `quote` (variation 1)
- `quoteCurrency` (variation 2)

### 2. Symbol Resolution (`resolve_contract_symbol()`)
- **Input**: Internal symbols (e.g., `BTCUSDT`, `cmt_btcusdt`)
- **Output**: Exchange contract symbols (e.g., `BTCUSDT_UMCBL`)
- **Process**:
  1. Clean symbol (remove `cmt_` prefix, uppercase)
  2. Check contract map cache (refresh if expired or use override)
  3. Return mapped symbol or fallback to `{symbol}_UMCBL`
  4. Log resolution with warning for fallbacks

### 3. Scoped 521 Cooldown
- **Per-Route Scoping**: Includes path + query params + symbol
- **Isolation**: 521 on BTCUSDT doesn't block ETHUSDT or balance
- **Auto-Clear**: Cooldown cleared on successful 200 response
- **Example Keys**:
  ```
  /capi/v2/market/candles?symbol=BTCUSDT&limit=10:BTCUSDT
  /capi/v2/market/candles?symbol=ETHUSDT&limit=10:ETHUSDT
  /capi/v2/account/getAccounts
  ```

### 4. Internal Key Extraction (`_extract_internal_key()`)
Helper method to parse contract data:
- **Primary**: Use `baseCoin` + `quoteCoin` (e.g., BTC + USDT = BTCUSDT)
- **Tolerant**: Try all field name variations
- **Fallback**: Extract from exchange symbol by removing suffixes (`_UMCBL`, `-PERP`, etc.)

## Endpoints Updated

### Market Data (5 endpoints)
1. `get_market_klines()` - K-lines/candlestick data
2. `get_ticker()` - 24h ticker stats
3. `get_order_book()` - Market depth
4. `get_funding_rate()` - Funding rate data
5. `get_market_price()` - Current market price

### Trading (4 endpoints)
1. `place_market_order()` - Order placement
2. `cancel_all_orders()` - Order cancellation
3. `set_leverage()` - Leverage configuration
4. `has_open_position()` - Position checking

## Testing

### Test Coverage
- **Tolerant Discovery Tests**: 5 tests in `test_tolerant_discovery.py`
  - Field variation tolerance (symbol, base, quote)
  - Override support
  - Fallback creation
  - Invalid JSON handling
- **Symbol Resolution Tests**: 2 tests
  - Fallback behavior
  - Warning logs
- **API Integration Tests**: 2 tests
  - Klines query params
  - Order body params
- **Cooldown Tests**: 3 tests
  - Scoped isolation
  - Auto-clearing
  - Key generation
- **Existing Tests**: 8 tests in `test_symbol_resolution.py`
- **Legacy Tests**: 27 tests in `test_weex_v2_api_alignment.py`

**Total**: 47 tests passing

### CI-Friendly Testing

Set override to skip live network calls:
```bash
export WEEX_CONTRACT_MAP_OVERRIDE='{"BTCUSDT":"BTCUSDT_UMCBL","ETHUSDT":"ETHUSDT_UMCBL"}'
```

### Integration Test
Created `test_integration_symbol_resolution.py`:
```bash
python test_integration_symbol_resolution.py
```

Features:
- Tests contract override
- Verifies symbol resolution
- Tests scoped cooldowns
- Validates tolerant parsing
- Runs without network access

## Security

### CodeQL Scan
- **Result**: 0 vulnerabilities found
- **Analysis**: No security issues introduced

### Code Review
All feedback addressed:
- ✅ Tolerant field parsing
- ✅ CI override mechanism
- ✅ Warning logs for fallbacks
- ✅ Scoped cooldown keys
- ✅ Comprehensive test coverage

## Environment Variables

In `.env.example`:
```bash
# Cloudflare 521 Hardening
WEEX_API_DELAY=0.5
WEEX_521_BASE_BACKOFF=8
WEEX_521_MAX_BACKOFF=45

# Skip leverage initialization to reduce 404 noise
WEEX_DISABLE_LEVERAGE_INIT=true

# Contract Symbol Resolution Override (for CI/testing)
# Example: WEEX_CONTRACT_MAP_OVERRIDE='{"BTCUSDT":"BTCUSDT_UMCBL","ETHUSDT":"ETHUSDT_UMCBL"}'
# Leave empty for production (uses live API discovery)
WEEX_CONTRACT_MAP_OVERRIDE=
```

## Backwards Compatibility

### Preserved Functionality
- `clean_symbol()` unchanged - still used internally for symbol normalization
- All existing tests pass (47 total)
- No breaking changes to public API
- Graceful degradation if contract discovery fails

### Migration Path
No action required - changes are backwards compatible:
- Symbol resolution is transparent to callers
- Existing code continues to work
- Automatic fallback ensures robustness

## Key Benefits

1. **Fixes HTTP 400 Errors**: Resolves "Parameter symbol is invalid" errors
2. **Tolerant Parsing**: Handles field name variations from API
3. **Automatic Discovery**: Learns correct symbols from WEEX API
4. **CI-Friendly**: Override support for testing without network
5. **Cached Performance**: 60-minute cache minimizes overhead
6. **Robust Fallback**: Works even if discovery fails
7. **Scoped Cooldowns**: 521 on one symbol doesn't block others
8. **Transparent**: No changes needed in calling code
9. **Well Tested**: 47 passing tests with comprehensive coverage
10. **Secure**: No vulnerabilities introduced

## Usage Example

```python
from core.weex_v2_client import WEEXv2Client

# Create client
client = WEEXv2Client(api_key, api_secret, api_password)

# Contract discovery happens automatically on first call
klines = client.get_market_klines("BTCUSDT", interval='1m')
# Internally: BTCUSDT → BTCUSDT_UMCBL

# Works with cmt_ prefix too
ticker = client.get_ticker("cmt_ethusdt")
# Internally: cmt_ethusdt → ETHUSDT → ETHUSDT_UMCBL

# Place order
order = client.place_market_order("SOLUSDT", "BUY", 0.1)
# Internally: SOLUSDT → SOLUSDT_UMCBL

# Fallback for unknown symbols
new_symbol_klines = client.get_market_klines("NEWCOINUSDT")
# Internally: NEWCOINUSDT → NEWCOINUSDT_UMCBL (fallback, logs warning)
```

## Monitoring

Check logs for symbol resolution:
```
INFO: 🔍 Loading contract discovery from WEEX V2 API...
INFO: ✅ Loaded 8 contract mappings from /capi/v2/market/contracts
DEBUG: Resolved symbol: BTCUSDT → BTCUSDT_UMCBL
WARNING: ⚠️ Symbol not in contract map, using fallback: NEWCOINUSDT → NEWCOINUSDT_UMCBL
```

Check logs for scoped cooldowns:
```
WARNING: 🔥 521 Error for /capi/v2/market/candles?symbol=BTCUSDT:BTCUSDT! Attempt 1/3, cooldown: 15.2s
INFO: Other symbols and routes continue normally
```

## Files Modified

| File | Changes | Description |
|------|---------|-------------|
| `core/weex_v2_client.py` | +60/-15 | Tolerant parsing, override support, scoped cooldowns |
| `tests/test_tolerant_discovery.py` | +290 (new) | Comprehensive tolerant discovery tests |
| `tests/test_symbol_resolution.py` | Existing | 8 tests for basic resolution |
| `tests/test_weex_v2_api_alignment.py` | Existing | 27 tests for API alignment |
| `.env.example` | +6 | Added override documentation |
| `test_integration_symbol_resolution.py` | +125 (new) | Integration test script |

## Conclusion

✅ Implementation finalized and tested  
✅ All 47 tests passing  
✅ CI-friendly with override support  
✅ Tolerant to field variations  
✅ Scoped 521 cooldowns  
✅ No security vulnerabilities  
✅ Backwards compatible  
✅ Ready for deployment

## Post-Deployment Verification

After deployment, verify:
1. Logs show "Resolved symbol: X → X_UMCBL"
2. No HTTP 40020 errors
3. 521 errors are scoped (other symbols continue)
4. Balance logs remain: "[LOG] Equity: $ | Available: $"
5. Orders execute successfully
