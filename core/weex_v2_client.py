"""
WEEX v2 API Client - Competition-Ready Implementation
Uses the verified authentication logic for WEEX contract trading API
Base URL: https://api-contract.weex.com
"""
import os
import time
import hmac
import hashlib
import base64
import requests
import json
import logging
import urllib.parse
import uuid
from typing import Union, Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# WEEX API Error Codes
ERROR_CODE_SUCCESS = '00000'
ERROR_CODE_INSUFFICIENT_BALANCE = '40015'

class WEEXv2Client:
    """
    WEEX v2 API Client with verified authentication
    
    Features:
    - Proper signature generation (HMAC SHA256 + Base64)
    - Multi-symbol support
    - K-lines data retrieval
    - Position management
    - Risk management (TP/SL)
    """
    
    BASE_URL = "https://api-contract.weex.com"
    
    # Alpha-Apex Profit Target and Stop Loss Thresholds
    FIRST_TARGET_PCT = 0.25  # First partial at +0.25%
    SECOND_TARGET_PCT = 0.50  # Reinvestment trigger at +0.50%
    INITIAL_SL_LONG_PCT = 0.50  # Initial stop loss for longs (0.50%)
    INITIAL_SL_SHORT_PCT = 0.40  # Initial stop loss for shorts (0.40% - tighter)
    BREAKEVEN_SL_PCT = 0.0  # Break-even stop after first partial
    
    # Emergency startup balance - used if first balance check returns 0.0
    # Based on last known good balance from production logs
    EMERGENCY_STARTUP_BALANCE = 719.0
    
    def __init__(self, api_key: str, api_secret: str, api_password: str):
        """
        Initialize WEEX v2 Client
        
        Args:
            api_key: WEEX API key
            api_secret: WEEX API secret
            api_password: WEEX API password
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_password = api_password
        
        # Track last 521 error for cooldown
        self.last_521_error_time = 0
        self.cooldown_seconds = 60
        
        # Track open positions for TP/SL management
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        
        # AI Wars: Multi-trade state tracking
        self.active_order_ids: Dict[str, str] = {}  # {symbol: order_id}
        self.active_symbols: set = set()  # Set of symbols with active positions/orders
        self.last_heartbeat_time = 0  # Track last heartbeat log time
        
        # Alpha-Apex: Track position scaling state
        # {symbol: {"partial_taken": bool, "breakeven_set": bool, "reinvested": bool, "original_size": float}}
        self.position_scaling_state: Dict[str, Dict[str, Any]] = {}
        
        # Alpha-Apex: Persistent HTTP session for better performance and rate limiting
        self.session = requests.Session()
        
        # Balance safety tracking: prevent ghost negative values
        self.last_known_positive_balance = 1000.0  # Default starting balance
        self.is_first_balance_check = True  # Flag to detect first balance check
        
        # Precision settings for different symbols (lowercase keys)
        # Note: Internal symbol keys are lowercase, but API calls convert to uppercase
        self.precision_map = {
            "cmt_btcusdt": 4,   # BTC: 4 decimals
            "btcusdt": 4,       # BTC: 4 decimals (clean format)
            "cmt_ethusdt": 3,   # ETH: 3 decimals
            "ethusdt": 3,       # ETH: 3 decimals (clean format)
            "cmt_solusdt": 2,   # SOL: 2 decimals
            "solusdt": 2,       # SOL: 2 decimals (clean format)
            "cmt_adausdt": 1,   # ADA: 1 decimal
            "adausdt": 1,       # ADA: 1 decimal (clean format)
            "cmt_dogeusdt": 0,  # DOGE: 0 decimals (whole numbers)
            "dogeusdt": 0,      # DOGE: 0 decimals (clean format)
            "cmt_xrpusdt": 1,   # XRP: 1 decimal
            "xrpusdt": 1,       # XRP: 1 decimal (clean format)
            "cmt_bnbusdt": 3,   # BNB: 3 decimals
            "bnbusdt": 3,       # BNB: 3 decimals (clean format)
            "cmt_ltcusdt": 2,   # LTC: 2 decimals
            "ltcusdt": 2,       # LTC: 2 decimals (clean format)
        }
        
        # AI Wars Audit: Step size compliance (hardcoded constants per exchange specs)
        self.step_size_map = {
            "cmt_btcusdt": 0.0001,   # BTC: 0.0001 step size (4 decimals)
            "btcusdt": 0.0001,
            "cmt_ethusdt": 0.001,    # ETH: 0.001 step size (3 decimals)
            "ethusdt": 0.001,
            "cmt_solusdt": 0.01,    # SOL: 0.01 step size (2 decimals)
            "solusdt": 0.01,
            "cmt_adausdt": 0.1,    # ADA: 0.1 step size (1 decimal)
            "adausdt": 0.1,
            "cmt_dogeusdt": 1.0,   # DOGE: 1.0 step size (whole numbers)
            "dogeusdt": 1.0,
            "cmt_xrpusdt": 0.1,    # XRP: 0.1 step size (1 decimal)
            "xrpusdt": 0.1,
            "cmt_bnbusdt": 0.001,    # BNB: 0.001 step size (3 decimals)
            "bnbusdt": 0.001,
            "cmt_ltcusdt": 0.01,    # LTC: 0.01 step size (2 decimals)
            "ltcusdt": 0.01,
        }
        
        # AI Wars Audit: Load persisted state if exists
        self._load_state_from_file()
    
    def _load_state_from_file(self) -> None:
        """
        AI Wars Audit: Load persisted state from session.json
        Ensures script restart remembers open positions
        """
        try:
            if os.path.exists("session.json"):
                with open("session.json", "r") as f:
                    state = json.load(f)
                    self.active_symbols = set(state.get("active_symbols", []))
                    self.active_order_ids = state.get("active_order_ids", {})
                    logger.info(f"✅ Loaded persisted state: {len(self.active_symbols)} active symbols")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load state from session.json: {str(e)}")
    
    def _save_state_to_file(self) -> None:
        """
        AI Wars Audit: Save current state to session.json
        """
        try:
            state = {
                "active_symbols": list(self.active_symbols),
                "active_order_ids": self.active_order_ids,
                "timestamp": time.time()
            }
            with open("session.json", "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state to session.json: {str(e)}")
    
    def clean_symbol(self, symbol: Optional[str]) -> str:
        """
        Clean symbol for API calls: remove 'cmt_' prefix and convert to UPPERCASE
        """
        if not symbol:
            return ""
        return symbol.replace('cmt_', '').upper()
    
    def round_qty(self, symbol: str, qty: float) -> float:
        """
        Round quantity to the correct precision for the symbol
        """
        if not symbol:
            logger.warning(f"⚠️ Invalid symbol: {symbol}, using default 2 decimals")
            precision = 2
        else:
            precision = self.precision_map.get(symbol.lower())
            if precision is None:
                # logger.warning(f"⚠️ Precision not defined for {symbol}, using default 2 decimals")
                precision = 2
        return round(qty, precision)
    
    def round_step_size(self, symbol: str, qty: float) -> float:
        """
        AI Wars Audit: Round quantity to exchange step size compliance
        Uses hardcoded step sizes: 0.01 for BTC, 0.1 for ETH, etc.
        """
        if not symbol:
            logger.warning(f"⚠️ Invalid symbol: {symbol}, using default step size 0.01")
            step_size = 0.01
        else:
            step_size = self.step_size_map.get(symbol.lower(), 0.01)
        
        # Round to nearest step size
        rounded = round(qty / step_size) * step_size
        
        # Also apply precision rounding for display
        precision = self.precision_map.get(symbol.lower(), 2)
        return round(rounded, precision)
    
    def generate_signature(self, timestamp: str, method: str, request_path: str, 
                           query_string: str, body_str: str) -> str:
        # Ensure method is UPPERCASE
        # body_str MUST be compact (no spaces) before it gets here
        message = timestamp + method.upper() + request_path + query_string + body_str
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'), 
            message.encode('utf-8'), 
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode()
        
    def send_weex_request(self, method: str, path: str, query_params: str = "", 
                            body: Union[Dict, str, None] = None) -> requests.Response:
        """
        Send authenticated request to WEEX API using compact JSON for signatures.
        
        Alpha-Evo V3: Implements Exponential Backoff for 521 errors
        AI Wars: Adds 1.5s delay between all API calls to avoid firewall
        """
        # AI Wars: Add delay to avoid triggering firewall
        time.sleep(1.5)
        
        # Alpha-Evo V3: Exponential Backoff for 521 errors
        max_retries = 3
        base_backoff = 60  # Start at 60 seconds
        
        for retry in range(max_retries):
            # 1. Cooldown check
            if time.time() - self.last_521_error_time < self.cooldown_seconds:
                remaining = self.cooldown_seconds - (time.time() - self.last_521_error_time)
                logger.warning(f"🛑 521 Error cooldown active: {remaining:.1f}s remaining")
                raise Exception(f"Cooldown active: {remaining:.1f}s remaining")
        
            timestamp = str(int(time.time() * 1000))
        
            # 2. CRITICAL: Handle body stringification once and keep it compact
            if body:
                if isinstance(body, dict):
                    # Use separators to ensure NO whitespace (e.g., {"a":"b"} not {"a": "b"})
                    body_str = json.dumps(body, separators=(',', ':'))
                else:
                    body_str = body
            else:
                body_str = ""
        
            # 3. Generate signature using the same body_str that will be sent
            signature = self.generate_signature(timestamp, method, path, query_params, body_str)
            
            headers = {
                "ACCESS-KEY": self.api_key,
                "ACCESS-SIGN": signature,
                "ACCESS-PASSPHRASE": self.api_password,
                "ACCESS-TIMESTAMP": timestamp,
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "locale": "en-US"
            }
            
            url = f"{self.BASE_URL}{path}{query_params}"
            
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, headers=headers, timeout=30)
                else:
                    # Send the EXACT body_str used for the signature
                    response = self.session.post(url, headers=headers, data=body_str, timeout=30)
                
                # AI Wars: Handle both 521 and 403 firewall errors
                if response.status_code in [521, 403]:
                    # Alpha-Evo V3: Exponential Backoff
                    backoff_time = base_backoff * (2 ** retry)  # 60s, 120s, 240s
                    logger.error(f"🔥 {response.status_code} Error: Firewall block! Retry {retry + 1}/{max_retries}, backing off {backoff_time}s...")
                    self.last_521_error_time = time.time()
                    self.cooldown_seconds = backoff_time
                    
                    if retry < max_retries - 1:
                        time.sleep(backoff_time)
                        continue  # Retry
                    else:
                        raise Exception(f"{response.status_code} Firewall Error - Max retries ({max_retries}) exceeded")
                    
                # Success - reset cooldown to base
                self.cooldown_seconds = 60
                return response
                
            except Exception as e:
                if ("521" not in str(e) and "403" not in str(e)) or retry >= max_retries - 1:
                    logger.error(f"❌ Request failed: {str(e)}")
                    raise
                # For firewall errors, continue to retry
                continue
        
        # Defensive fallback - should not reach here due to retry loop logic
        raise Exception(f"Request failed after {max_retries} retries with exponential backoff (60s, 120s, 240s)")

    # -------------------------------------------------------------------------
    # CRITICAL FIX 1: Market K-Lines (Returns Numbers, not Strings)
    # -------------------------------------------------------------------------
    def get_market_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> List[List[float]]:
        """
        Get K-lines (candlestick) data from WEEX
        Endpoint: GET /capi/v2/market/candles
        """
        try:
            # Clean symbol for API call but preserve granularity param
            clean_symbol_value = self.clean_symbol(symbol)
            
            path = "/capi/v2/market/candles"
            
            query_params = f"?symbol={urllib.parse.quote(clean_symbol_value)}&granularity={interval}&limit={limit}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                
                raw_list = []
                if isinstance(data, list):
                    raw_list = data
                elif isinstance(data, dict) and data.get('code') == '00000':
                    raw_list = data.get('data', [])
                
                # CRITICAL FIX: Convert Strings to Floats
                formatted_candles = []
                for candle in raw_list:
                    if len(candle) >= 6: 
                        try:
                            formatted_candles.append([
                                int(candle[0]),     # 0: Timestamp
                                float(candle[1]),   # 1: Open
                                float(candle[2]),   # 2: High
                                float(candle[3]),   # 3: Low
                                float(candle[4]),   # 4: Close
                                float(candle[5])    # 5: Volume
                            ])
                        except (ValueError, IndexError):
                            continue # Skip bad candles
                            
                if formatted_candles:
                    return formatted_candles
                else:
                    return []
            else:
                logger.error(f"❌ HTTP {response.status_code} for {symbol}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get K-lines for {symbol}: {str(e)}")
            return []

    # -------------------------------------------------------------------------
    # CRITICAL FIX 2: Funding Rate (Returns Float, not String)
    # -------------------------------------------------------------------------
    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Get current funding rate for a symbol from WEEX
        Returns a dictionary with 'rate' and 'sentiment' fields
        
        Sentiment labels:
        - > 0.03% = 'High/Long-Heavy' (restrict long trades)
        - < 0.00% = 'Negative/Short-Heavy' (prioritize long trades)
        - Otherwise = 'Neutral'
        """
        try:
            # Clean symbol for API call
            clean_symbol_value = self.clean_symbol(symbol)
            
            path = "/capi/v2/market/funding-rate"
            query_params = f"?symbol={urllib.parse.quote(clean_symbol_value)}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '00000' or data.get('success') is True:
                    funding_data = data.get('data', {})
                    
                    # Extract funding rate - handle likely field names
                    funding_rate = funding_data.get('fundingRate') or funding_data.get('funding_rate')
                    
                    if funding_rate is not None:
                        rate = float(funding_rate)
                        
                        # Classify sentiment based on rate
                        if rate > 0.03:
                            sentiment = "High/Long-Heavy"
                        elif rate < 0.00:
                            sentiment = "Negative/Short-Heavy"
                        else:
                            sentiment = "Neutral"
                        
                        return {'rate': rate, 'sentiment': sentiment}
                    
            # Default fallback
            return {'rate': 0.0, 'sentiment': 'Neutral'}
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get funding rate for {symbol}: {str(e)}, using default fallback")
            return {'rate': 0.0, 'sentiment': 'Neutral'}

    # -------------------------------------------------------------------------
    # CRITICAL FIX 3: Market Price (Fixes "Shadow Mode" / BTC $90k issue)
    # -------------------------------------------------------------------------
    def get_market_price(self, symbol: str) -> float:
        """
        Get current market price from WEEX ticker endpoint
        """
        try:
            # Clean symbol for API call
            clean_symbol_value = self.clean_symbol(symbol)
            
            # We use the ticker endpoint for the latest price
            path = "/capi/v2/market/ticker"
            query_params = f"?symbol={clean_symbol_value}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                # Check for successful code '00000'
                if data.get('code') == '00000' and 'data' in data:
                    # FIX: Force convert string to float. 
                    price_data = data['data']
                    price = price_data.get('close') or price_data.get('last') or 0.0
                    return float(price)
                    
                # Fallback for different API structure
                elif isinstance(data, dict) and 'close' in data:
                    return float(data['close'])
                    
            logger.warning(f"⚠️ Could not fetch price for {symbol}")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return 0.0

    def get_order_book(self, symbol: str, depth: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get order book (market depth) from WEEX
        """
        try:
            # Clean symbol: remove 'cmt_' prefix and convert to UPPERCASE
            symbol_clean = self.clean_symbol(symbol)
            
            path = "/capi/v2/market/depth"
            query_params = f"?symbol={urllib.parse.quote(symbol_clean)}&depth={depth}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 or data.get('success'):
                    order_book = data.get('data', {})
                    return order_book
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {str(e)}")
            return None
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker (24h stats) from WEEX
        """
        try:
            # Clean symbol for API call
            clean_symbol_value = self.clean_symbol(symbol)
            
            path = "/capi/v2/market/ticker"
            query_params = f"?symbol={urllib.parse.quote(clean_symbol_value)}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '00000' or data.get('success') is True:
                    ticker_data = data.get('data', {})
                    return ticker_data
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {str(e)}")
            return None
    
    def _extract_price_from_order(self, order: Any) -> float:
        """
        Extract price from order book entry (handles both list and dict formats)
        """
        try:
            if isinstance(order, list):
                return float(order[0])
            elif isinstance(order, dict):
                return float(order.get('price', 0))
            return 0.0
        except (ValueError, TypeError, IndexError):
            return 0.0
    
    def check_spread(self, symbol: str, max_spread_pct: float = 0.1) -> bool:
        """
        Check if spread is acceptable (Spread Guard)
        """
        try:
            order_book = self.get_order_book(symbol, depth=1)
            
            if not order_book:
                logger.warning(f"⚠️ Could not fetch order book for {symbol}, skipping spread check")
                return True  # Allow trade if we can't check (failsafe)
            
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            if not bids or not asks:
                logger.warning(f"⚠️ Empty order book for {symbol}")
                return False
            
            # Get best bid and ask using helper method
            best_bid = self._extract_price_from_order(bids[0])
            best_ask = self._extract_price_from_order(asks[0])
            
            if best_bid == 0:
                return False
            
            # Calculate spread percentage
            spread_pct = ((best_ask - best_bid) / best_bid) * 100
            
            if spread_pct > max_spread_pct:
                logger.warning(f"🛑 Spread too wide for {symbol}: {spread_pct:.3f}% > {max_spread_pct}%")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check spread for {symbol}: {str(e)}")
            return True  # Allow trade on error (failsafe)
    
    def get_account_balance(self, retry_count: int = 0, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Get account balance with 521 error handling.
        
        Args:
            retry_count: Current retry attempt (internal use)
            max_retries: Maximum number of retries for 521 errors
            
        Returns:
            Account balance data or None
        """
        try:
            path = "/capi/v2/account/accounts?productType=umcbl"
            response = self.send_weex_request("GET", path)
            
            if response.status_code == 200:
                data = response.json()
                # Handle both formats: dict with 'data' or 'collateral' key, or direct list
                # Log which format is received for monitoring
                if isinstance(data, list):
                    logger.debug("Account balance response is a list (direct format)")
                    collateral_list = data
                else:
                    logger.debug("Account balance response is a dict (nested format)")
                    # V2 API may use 'data' key for the list
                    collateral_list = data.get('data', data.get('collateral', []))
                
                if collateral_list:
                    for item in collateral_list:
                        # Ensure we are looking at the USDT wallet
                        # Check both coin_id (value "2") and coinName (value "USDT")
                        is_usdt = (str(item.get('coin_id')) == "2" or 
                                   str(item.get('coinName', '')).upper() == "USDT")
                        if is_usdt:
                            # Comprehensive equity key checking: try totalEquity, equity, accountEquity, available
                            equity = 0.0  # Default to 0.0 if no valid value found
                            found_value = False  # Track if we found any valid value
                            for key in ['totalEquity', 'equity', 'accountEquity', 'available']:
                                if key in item and item[key] is not None:
                                    try:
                                        value = float(item[key])
                                        if value != 0.0:  # Found a non-zero value, use it
                                            equity = value
                                            found_value = True
                                            break
                                        elif not found_value:  # First valid value is 0.0, store it but keep looking
                                            equity = value
                                            found_value = True
                                    except (ValueError, TypeError):
                                        continue
                            
                            # Handle zero balance - retry instead of using fallback
                            if equity == 0.0 and retry_count < max_retries:
                                logger.warning(f"🛑 Zero balance detected. Waiting 60s for a clear window... (Retry {retry_count + 1}/{max_retries})")
                                time.sleep(60)
                                return self.get_account_balance(retry_count=retry_count + 1, max_retries=max_retries)
                            
                            # If still 0 after retries, stop trading
                            if equity == 0.0:
                                logger.error("❌ Balance is still 0.0 after retries. Bot cannot trade without balance.")
                                # Return None to indicate failure - don't use hardcoded fallback
                                return None
                            
                            # Safety check: if balance < 0, use last known positive balance
                            if equity < 0:
                                logger.warning(f"⚠️ Negative balance detected ({equity}), using last known positive balance: {self.last_known_positive_balance}")
                                equity = self.last_known_positive_balance
                                # Don't update last_known_positive_balance since this is a fallback
                            elif equity > 0:
                                # Update last known positive balance and mark we've had a successful check
                                self.last_known_positive_balance = equity
                                self.is_first_balance_check = False
                            
                            # Add equity to the item for backwards compatibility
                            item['equity'] = equity
                            item['totalEquity'] = equity
                            
                            # AI Wars: Extract available balance for precise logging
                            available = 0.0
                            for key in ['availableBalance', 'available', 'availableFunds']:
                                if key in item and item[key] is not None:
                                    try:
                                        available = float(item[key])
                                        if available != 0.0:
                                            break
                                    except (ValueError, TypeError):
                                        continue
                            
                            # AI Wars: Log both Equity and Available
                            logger.info(f"[LOG] Equity: ${equity:.2f} | Available: ${available:.2f}")
                            
                            # AI Wars Audit: Calculate truly liquid capital by subtracting initial margin
                            item['availableBalance'] = available
                            item['liquidCapital'] = self._calculate_liquid_capital(available)
                            
                            return item
                    
                # If no list found, retry or fail
                if retry_count < max_retries:
                    logger.warning(f"🛑 No collateral data found. Waiting 60s for a clear window... (Retry {retry_count + 1}/{max_retries})")
                    time.sleep(60)
                    return self.get_account_balance(retry_count=retry_count + 1, max_retries=max_retries)
                return None
                
            # Handle 521 errors - should be handled by send_weex_request, but add extra safety
            if response.status_code in [521, 403]:
                if retry_count < max_retries:
                    logger.warning(f"🛑 Firewall active ({response.status_code}). Waiting 60s for a clear window... (Retry {retry_count + 1}/{max_retries})")
                    time.sleep(60)
                    return self.get_account_balance(retry_count=retry_count + 1, max_retries=max_retries)
                    
            return None
        except Exception as e:
            # Check if this is a 521/403 firewall error that escaped send_weex_request
            # These specific error patterns are raised by send_weex_request
            error_msg = str(e).lower()
            is_firewall_error = (
                "521" in error_msg or 
                "403" in error_msg or 
                "firewall" in error_msg or
                "cloudflare" in error_msg
            )
            
            if is_firewall_error and retry_count < max_retries:
                logger.warning(f"🛑 Firewall error detected: {str(e)}. Waiting 60s for a clear window... (Retry {retry_count + 1}/{max_retries})")
                time.sleep(60)
                return self.get_account_balance(retry_count=retry_count + 1, max_retries=max_retries)
            
            logger.error(f"Balance parsing error: {str(e)}")
            return None
    
    def _calculate_liquid_capital(self, available: float) -> float:
        """
        AI Wars Audit: Calculate truly liquid capital by subtracting initial margin
        of all active trades from available balance
        
        Args:
            available: Available balance from exchange
            
        Returns:
            Liquid capital available for new trades
        """
        try:
            # Query all open positions to get their initial margin
            path = "/capi/v2/positions/pending-orders?productType=umcbl"
            response = self.send_weex_request("GET", path)
            
            if response and response.status_code == 200:
                data = response.json()
                positions = data.get('data', {}).get('positions', [])
                
                total_initial_margin = 0.0
                for pos in positions:
                    try:
                        # Extract initial margin for each active position
                        initial_margin = float(pos.get('initialMargin', 0) or pos.get('margin', 0) or 0)
                        total_initial_margin += initial_margin
                    except (ValueError, TypeError):
                        continue
                
                liquid = available - total_initial_margin
                logger.info(f"💧 Liquid Capital: ${liquid:.2f} (Available: ${available:.2f} - Initial Margin: ${total_initial_margin:.2f})")
                return max(0.0, liquid)  # Never return negative
            
            # If API call fails, return available as-is
            return available
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate liquid capital: {str(e)}, using available balance")
            return available
        
    def set_leverage(self, symbol: str, leverage: int = 20, margin_mode: str = "isolated") -> bool:
            """
            Sets the leverage for a specific symbol.
            Uses V2 endpoint: /capi/v2/account/setLeverage
            
            Args:
                symbol: Trading symbol (e.g., "cmt_btcusdt" or "BTCUSDT")
                leverage: Leverage multiplier (will be converted to string for API)
                margin_mode: Kept for API compatibility but always uses "isolated" as required by WEEX V2 API
            
            Returns:
                bool: True if leverage was set successfully, False otherwise
            """
            # Clean symbol for API call: remove 'cmt_' prefix and convert to UPPERCASE
            clean_symbol = self.clean_symbol(symbol)
            
            # Primary endpoint: /capi/v2/account/setLeverage (POST)
            path = "/capi/v2/account/setLeverage"
            
            # WEEX V2 API requires string format for all parameters
            body = {
                "symbol": clean_symbol,
                "leverage": str(leverage),
                "marginMode": "isolated"  # Always use isolated mode as required by WEEX V2 API
            }
            
            try:
                response = self.send_weex_request("POST", path, body=body)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == '00000' or data.get('success') is True:
                        logger.info(f"✅ Leverage confirmed at {leverage}x for {symbol}")
                        return True
                    
                    # Check if it says "already set" (check both 'msg' and 'message' fields)
                    msg = str(data.get('msg', data.get('message', ''))).lower()
                    if "already" in msg or "no change" in msg:
                        return True
                        
                    logger.warning(f"⚠️ Leverage API response {symbol}: {data}")
                    return False
                    
                logger.warning(f"⚠️ Leverage Status {response.status_code}: {response.text}")
                return False
                
            except Exception as e:
                logger.warning(f"⚠️ Leverage Exception: {str(e)}")
                return False
    
    def has_open_position(self, symbol: str) -> bool:
        # 1. Clean symbol using the clean_symbol method for consistency
        clean_symbol_value = self.clean_symbol(symbol)
        
        try:
            path = "/capi/v2/account/position/allPosition"
            # Include symbol in query params for filtered results
            query_params = f"?symbol={urllib.parse.quote(clean_symbol_value)}" if clean_symbol_value else "" 
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # FIX: Handle the case where WEEX returns a raw list [] instead of a data dict
                if isinstance(response_data, list):
                    positions = response_data
                elif isinstance(response_data, dict):
                    positions = response_data.get('data', [])
                else:
                    positions = []
                
                for pos in positions:
                    try:
                        # Extract and compare
                        pos_symbol = str(pos.get('symbol', '')).upper()
                        size = float(pos.get('size', 0))
                        
                        if pos_symbol == clean_symbol_value and size > 0:
                            logger.info(f"📊 Open position found for {clean_symbol_value}: {size} units")
                            self.open_positions[clean_symbol_value] = pos
                            return True
                    except (ValueError, TypeError):
                        continue
                
                if clean_symbol_value in self.open_positions:
                    del self.open_positions[clean_symbol_value]
                return False
            else:
                logger.error(f"❌ Position Check Failed (HTTP {response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception in has_open_position: {str(e)}")
            return False
    
    def place_market_order(self, symbol: str, side: str, size: float,
                           check_spread: bool = True, 
                           stop_loss_price: Optional[float] = None,
                           take_profit_price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Place a market order with optional TP/SL parameters
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY, SELL, CLOSE_LONG, CLOSE_SHORT)
            size: Order size
            check_spread: Whether to check spread before placing order
            stop_loss_price: Optional stop loss trigger price for exchange-side safety
            take_profit_price: Optional take profit trigger price for exchange-side safety
        
        Returns:
            Order response dict or None
        """
        # Store original symbol for internal tracking
        symbol_internal = symbol.lower()
        
        # AI Wars: Prevent opening new position if active position/order exists
        if side in ["BUY", "SELL"] and symbol_internal in self.active_symbols:
            logger.warning(f"🚫 AI Wars: Cannot open new position on {symbol} - active position/order already exists")
            return None
        
        try:
            # AI Wars Audit: Use step size rounding for exchange compliance
            size = self.round_step_size(symbol_internal, size)
            client_oid = str(uuid.uuid4()).replace("-", "")[:30]
            
            # Clean symbol for API call: BTCUSDT format (no cmt_ prefix, uppercase)
            clean_symbol_value = self.clean_symbol(symbol)
            
            side_map = {
                "BUY": "1", "SELL": "2",
                "CLOSE_LONG": "3", "CLOSE_SHORT": "4"
            }
            
            path = "/capi/v2/order/placeOrder"
            body_dict = {
                "symbol": clean_symbol_value,
                "client_oid": client_oid,
                "side": side_map.get(side.upper(), "1"),
                "type": "1",         # Market Order
                "order_type": "0",
                "size": str(float(size)),  # AI Wars: Ensure string conversion via float to avoid scientific notation
                "match_price": "1"
            }
            
            # AI Wars Audit: Add exchange-side TP/SL parameters with reduceOnly flag
            if stop_loss_price is not None:
                body_dict["stopLossTriggerPrice"] = str(float(stop_loss_price))
                body_dict["stopLossReduceOnly"] = "true"  # Prevent accidental new position opening
            
            if take_profit_price is not None:
                body_dict["takeProfitTriggerPrice"] = str(float(take_profit_price))
                body_dict["takeProfitReduceOnly"] = "true"  # Prevent accidental new position opening
            
            # Pass the dict body to send_weex_request, which will handle minification
            # Note: send_weex_request already handles delays and firewall errors (403/521)
            response = self.send_weex_request("POST", path, body=body_dict)
            
            # ... (Rest of your response handling) ...
            if response and response.status_code == 200:
                data = response.json()
                
                # Tournament Compliance: Self-Healing for Error 40015 (Insufficient Balance)
                error_code = str(data.get('code', ''))
                if error_code == ERROR_CODE_INSUFFICIENT_BALANCE:
                    logger.error(f"🚨 Error {ERROR_CODE_INSUFFICIENT_BALANCE}: Insufficient Balance detected for {symbol}")
                    logger.info("🔧 Self-healing: Triggering closePositions...")
                    # Close all positions to release margin
                    try:
                        self.close_all_positions()
                        logger.info("✅ Self-healing: All positions closed")
                    except Exception as heal_error:
                        logger.error(f"Failed to self-heal: {str(heal_error)}")
                    return None
                
                # Check for success - handle multiple response formats:
                # - code: "00000" (string success code from WEEX V2)
                # - code: 0 (numeric success code from some endpoints)
                # - success: true (boolean success flag)
                is_success = (error_code == ERROR_CODE_SUCCESS or 
                              error_code == "0" or 
                              data.get('success') is True)
                if data.get('order_id') or data.get('data', {}).get('orderId') or is_success:
                    order_id = data.get('order_id') or data.get('orderId') or data.get('data', {}).get('orderId')
                    logger.info(f"✅ Success! ID: {order_id}")
                    
                    # AI Wars: Track active order and symbol (use internal symbol format)
                    if side in ["BUY", "SELL"]:
                        if order_id:
                            self.active_order_ids[symbol_internal] = order_id
                        self.active_symbols.add(symbol_internal)
                        
                        # AI Wars Audit: Save state to file for persistence
                        self._save_state_to_file()
                    
                    return data
            return None

        except Exception as e:
            logger.error(f"❌ Failed to place order for {symbol}: {str(e)}")
            return None
    
    def check_tp_sl_triggers(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Alpha-Apex: Check multi-tier profit targets and dynamic stop loss
        """
        symbol = symbol.replace('cmt_', '').upper()
        if symbol not in self.open_positions:
            return None
        
        position = self.open_positions[symbol]
        entry_price = float(position.get('entryPrice', 0))
        position_side = position.get('side', '').upper()
        
        if entry_price == 0:
            return None
        
        # Initialize scaling state if needed
        if symbol not in self.position_scaling_state:
            original_size = abs(float(position.get('size', 0)))
            self.position_scaling_state[symbol] = {
                "partial_taken": False,
                "breakeven_set": False,
                "reinvested": False,
                "original_size": original_size,
                "realized_profit": 0.0
            }
        
        state = self.position_scaling_state[symbol]
        
        # Alpha-Apex targets (fee-adjusted)
        FIRST_TARGET_PCT = self.FIRST_TARGET_PCT
        SECOND_TARGET_PCT = self.SECOND_TARGET_PCT
        INITIAL_SL_LONG_PCT = self.INITIAL_SL_LONG_PCT
        INITIAL_SL_SHORT_PCT = self.INITIAL_SL_SHORT_PCT
        BREAKEVEN_SL_PCT = self.BREAKEVEN_SL_PCT
        
        # Alpha-Evo: Trailing stop thresholds
        BREAKEVEN_THRESHOLD_PCT = 2.0  # Move to breakeven at +2%
        TRAILING_ACTIVATION_PCT = 4.0  # Activate 1% trailing stop at +4%
        TRAILING_STOP_PCT = 1.0  # 1% trailing distance
        
        # Track highest price for trailing stop
        if 'highest_price' not in state:
            state['highest_price'] = entry_price
        
        # Calculate price change percentage
        price_change_pct = ((current_price - entry_price) / entry_price) * 100
        
        # For LONG positions
        if position_side == "LONG":
            # Update highest price for trailing stop
            if current_price > state['highest_price']:
                state['highest_price'] = current_price
            
            # Alpha-Evo: Trailing stop logic
            if price_change_pct >= TRAILING_ACTIVATION_PCT:
                # Activated 1% trailing stop
                trailing_sl_price = state['highest_price'] * (1 - TRAILING_STOP_PCT / 100.0)
                trailing_pct_from_entry = ((trailing_sl_price - entry_price) / entry_price) * 100
                
                if current_price <= trailing_sl_price:
                    logger.warning(f"🛑 Trailing Stop Loss triggered for {symbol}: Price {current_price:.4f} <= Trailing SL {trailing_sl_price:.4f} (Peak: {state['highest_price']:.4f})")
                    return "SL"
                    
                # Log trailing stop status periodically
                if not state.get('trailing_logged', False):
                    logger.info(f"📈 Trailing stop active for {symbol}: Peak {state['highest_price']:.4f}, Trail SL {trailing_sl_price:.4f}")
                    state['trailing_logged'] = True
                    
            elif price_change_pct >= BREAKEVEN_THRESHOLD_PCT:
                # Alpha-Evo: Move to breakeven at +2%
                if not state.get("breakeven_evo_set", False):
                    logger.info(f"🎯 Alpha-Evo: Moving stop to breakeven for {symbol} at +{price_change_pct:.2f}%")
                    state["breakeven_evo_set"] = True
                
                # Check breakeven stop
                if price_change_pct <= BREAKEVEN_SL_PCT:
                    logger.warning(f"🛑 Break-even Stop Loss triggered for {symbol}: {price_change_pct:.2f}%")
                    return "SL"
            else:
                # Initial stop loss (ATR-based, 1.0-2.0%)
                if price_change_pct <= -INITIAL_SL_LONG_PCT:
                    logger.warning(f"🛑 LONG Stop Loss triggered for {symbol}: {price_change_pct:.2f}% loss (threshold: {INITIAL_SL_LONG_PCT:.2f}%)")
                    return "SL"
            
            # Check profit targets (Alpha-Apex partial profit system)
            if not state["reinvested"] and state["partial_taken"] and price_change_pct >= SECOND_TARGET_PCT:
                logger.info(f"🎯 Alpha-Apex: Second target hit for {symbol}: {price_change_pct:.2f}% (re-investment)")
                return "PARTIAL_2"
            elif not state["partial_taken"] and price_change_pct >= FIRST_TARGET_PCT:
                logger.info(f"🎯 Alpha-Apex: First target hit for {symbol}: {price_change_pct:.2f}% (partial profit)")
                return "PARTIAL_1"
        
        # For SHORT positions
        elif position_side == "SHORT":
            # Invert price change for shorts
            short_pnl_pct = -price_change_pct
            
            # Track lowest price for trailing stop (inverse for shorts)
            if 'lowest_price' not in state:
                state['lowest_price'] = entry_price
            
            if current_price < state['lowest_price']:
                state['lowest_price'] = current_price
            
            # Alpha-Evo: Trailing stop logic for shorts
            if short_pnl_pct >= TRAILING_ACTIVATION_PCT:
                # Activated 1% trailing stop (upward for shorts)
                trailing_sl_price = state['lowest_price'] * (1 + TRAILING_STOP_PCT / 100.0)
                trailing_pct_from_entry = -((trailing_sl_price - entry_price) / entry_price) * 100
                
                if current_price >= trailing_sl_price:
                    logger.warning(f"🛑 Trailing Stop Loss triggered for SHORT {symbol}: Price {current_price:.4f} >= Trailing SL {trailing_sl_price:.4f} (Low: {state['lowest_price']:.4f})")
                    return "SL"
                    
                # Log trailing stop status periodically
                if not state.get('trailing_logged', False):
                    logger.info(f"📉 Trailing stop active for SHORT {symbol}: Low {state['lowest_price']:.4f}, Trail SL {trailing_sl_price:.4f}")
                    state['trailing_logged'] = True
                    
            elif short_pnl_pct >= BREAKEVEN_THRESHOLD_PCT:
                # Alpha-Evo: Move to breakeven at +2%
                if not state.get("breakeven_evo_set", False):
                    logger.info(f"🎯 Alpha-Evo: Moving stop to breakeven for SHORT {symbol} at +{short_pnl_pct:.2f}%")
                    state["breakeven_evo_set"] = True
                
                # Check breakeven stop
                if short_pnl_pct <= BREAKEVEN_SL_PCT:
                    logger.warning(f"🛑 Break-even Stop Loss triggered for SHORT {symbol}: {short_pnl_pct:.2f}%")
                    return "SL"
            else:
                # Initial stop loss (ATR-based, tighter for shorts: 0.40%)
                if short_pnl_pct <= -INITIAL_SL_SHORT_PCT:
                    logger.warning(f"🛑 SHORT Stop Loss triggered for {symbol}: {short_pnl_pct:.2f}% loss (threshold: {INITIAL_SL_SHORT_PCT:.2f}%)")
                    return "SL"
            
            # Check profit targets (Alpha-Apex partial profit system)
            if not state["reinvested"] and state["partial_taken"] and short_pnl_pct >= SECOND_TARGET_PCT:
                logger.info(f"🎯 Alpha-Apex: Second target hit for {symbol}: {short_pnl_pct:.2f}% (re-investment)")
                return "PARTIAL_2"
            elif not state["partial_taken"] and short_pnl_pct >= FIRST_TARGET_PCT:
                logger.info(f"🎯 Alpha-Apex: First target hit for {symbol}: {short_pnl_pct:.2f}% (partial profit)")
                return "PARTIAL_1"
        
        return None
    
    def close_position(self, symbol: str) -> bool:
        """
        Close an open position (market order)
        """
        symbol = symbol.replace('cmt_', '').upper()
        if symbol not in self.open_positions:
            logger.warning(f"⚠️ No position to close for {symbol}")
            return False
        
        position = self.open_positions[symbol]
        size = abs(float(position.get('size', 0)))
        side = "CLOSE_LONG" if position.get('side', '').upper() == "LONG" else "CLOSE_SHORT"
        
        result = self.place_market_order(symbol, side, size)
        
        if result:
            logger.info(f"✅ Position closed for {symbol}")
            del self.open_positions[symbol]
            # Clean up scaling state
            if symbol in self.position_scaling_state:
                del self.position_scaling_state[symbol]
            
            # AI Wars: Remove from active tracking
            symbol_lower = symbol.lower()
            if not symbol_lower.startswith('cmt_'):
                symbol_lower = f'cmt_{symbol_lower}'
            
            self.active_symbols.discard(symbol_lower)
            if symbol_lower in self.active_order_ids:
                del self.active_order_ids[symbol_lower]
            
            # AI Wars Audit: Save state after closing position
            self._save_state_to_file()
            
            return True
        else:
            logger.error(f"❌ Failed to close position for {symbol}")
            return False
    
    def close_all_positions(self) -> None:
        """
        Tournament Compliance: Close all open positions
        Used for auto-initialization and self-healing
        """
        logger.info("🔄 Closing all open positions...")
        positions_to_close = list(self.open_positions.keys())
        
        for symbol in positions_to_close:
            try:
                self.close_position(symbol)
                time.sleep(0.5)  # Small delay between closes
            except Exception as e:
                logger.error(f"Failed to close position for {symbol}: {str(e)}")
        
        logger.info(f"✅ Closed {len(positions_to_close)} positions")
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """
        Tournament Compliance: Cancel all pending orders for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            clean_symbol = self.clean_symbol(symbol)
            path = "/capi/v2/order/cancelAllOrders"
            
            body_dict = {
                "symbol": clean_symbol.lower()
            }
            
            body_json = json.dumps(body_dict, separators=(',', ':'))
            response = self.send_weex_request("POST", path, body=body_json)
            
            if response and response.status_code == 200:
                data = response.json()
                if str(data.get('code')) == '00000':
                    logger.info(f"✅ All orders cancelled for {symbol}")
                    return True
            
            logger.warning(f"⚠️ Failed to cancel orders for {symbol}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel orders for {symbol}: {str(e)}")
            return False
    
    def close_partial_position(self, symbol: str, percentage: float) -> Optional[Dict[str, Any]]:
        """
        Alpha-Apex: Close a partial position (e.g., 50% at first target)
        """
        symbol = symbol.replace('cmt_', '').upper()
        if symbol not in self.open_positions:
            return None
        
        position = self.open_positions[symbol]
        current_size = abs(float(position.get('size', 0)))
        
        # Calculate size to close
        close_size = current_size * (percentage / 100.0)
        close_size = self.round_qty(symbol, close_size)
        
        # Determine side (opposite of position)
        side = "CLOSE_LONG" if position.get('side', '').upper() == "LONG" else "CLOSE_SHORT"
        
        logger.info(f"✂️ Closing {percentage}% of {symbol} ({close_size} units)")
        
        result = self.place_market_order(symbol, side, close_size)
        
        if result:
            # Update internal state
            if symbol in self.position_scaling_state:
                self.position_scaling_state[symbol]["partial_taken"] = True
                self.position_scaling_state[symbol]["breakeven_set"] = True
            return result
        
        return None
    
    def upload_ai_log(self, order_id: str, symbol: str, signal_data: Dict[str, Any], 
                      indicators: Dict[str, Any], historical_pnl: str) -> bool:
        """
        Alpha-Evo: Upload AI log to WEEX after successful order placement
        Alpha-Evo V3: Save failed logs to disk for retry
        
        Args:
            order_id: Order ID from placeOrder response
            symbol: Trading symbol
            signal_data: Signal information (action, confidence, reasoning, tp, sl)
            indicators: Market indicators (rsi, ema, current_price, etc.)
            historical_pnl: Summary of last 5 trades
            
        Returns:
            True if successful, False otherwise
        """
        try:
            clean_symbol = self.clean_symbol(symbol)
            path = "/capi/v2/order/uploadAiLog"
            
            # Build AI log payload according to WEEX specification
            payload = {
                "orderId": order_id,
                "stage": "Decision Making",
                "model": "GPT-4o-Alpha-Evo-V3",
                "input": {
                    "market_data": {
                        "symbol": clean_symbol,
                        "rsi_14": round(indicators.get("rsi", 50.0), 2),
                        "ema_20": round(indicators.get("ema_20", indicators.get("current_price", 0.0)), 2),
                        "historical_pnl": historical_pnl
                    },
                    "prompt": "Analyze market trend and past performance to execute next trade."
                },
                "output": {
                    "signal": signal_data.get("action", "LONG").upper(),
                    "confidence": round(signal_data.get("confidence", 0.0), 2),
                    "tp": round(signal_data.get("tp_price", 0.0), 2),
                    "sl": round(signal_data.get("sl_price", 0.0), 2)
                },
                "explanation": signal_data.get("reasoning", "Market analysis indicates favorable conditions for this trade.")
            }
            
            # Send AI log to WEEX
            body_json = json.dumps(payload, separators=(',', ':'))
            response = self.send_weex_request("POST", path, body=body_json)
            
            if response and response.status_code == 200:
                data = response.json()
                if str(data.get('code')) == '00000':
                    logger.info(f"✅ AI Log uploaded successfully for order {order_id}")
                    return True
                else:
                    logger.warning(f"⚠️ AI Log upload returned code {data.get('code')}: {data.get('msg')}")
                    # Alpha-Evo V3: Save failed log
                    self._save_failed_log(order_id, payload)
                    return False
            else:
                logger.warning(f"⚠️ AI Log upload failed (HTTP {response.status_code if response else 'No response'})")
                # Alpha-Evo V3: Save failed log
                self._save_failed_log(order_id, payload)
                return False
                
        except Exception as e:
            logger.error(f"Failed to upload AI log: {str(e)}")
            # Alpha-Evo V3: Save failed log
            try:
                self._save_failed_log(order_id, payload)
            except:
                pass
            return False
    
    def _save_failed_log(self, order_id: str, payload: Dict[str, Any]) -> None:
        """
        Alpha-Evo V3: Save failed AI log to disk for retry
        
        Args:
            order_id: Order ID
            payload: AI log payload
        """
        try:
            import os
            failed_logs_dir = "failed_logs"
            os.makedirs(failed_logs_dir, exist_ok=True)
            
            log_file = os.path.join(failed_logs_dir, f"log_{order_id}.json")
            
            # Add timestamp for retry tracking
            payload["_retry_metadata"] = {
                "failed_at": time.time(),
                "retry_count": 0
            }
            
            with open(log_file, 'w') as f:
                json.dump(payload, f, indent=2)
            
            logger.info(f"💾 Failed log saved to {log_file} for retry")
            
        except Exception as e:
            logger.error(f"Failed to save failed log: {str(e)}")
    
    def log_heartbeat(self) -> None:
        """
        AI Wars: Log heartbeat every 10 minutes showing active trades and unrealized PnL
        """
        current_time = time.time()
        
        # Only log heartbeat every 10 minutes (600 seconds)
        if current_time - self.last_heartbeat_time < 600:
            return
        
        try:
            # Get active symbols from open positions
            active_trades = list(self.active_symbols)
            
            # Calculate total unrealized PnL
            total_unrealized_pnl = 0.0
            
            for symbol in active_trades:
                if symbol in self.open_positions:
                    position = self.open_positions[symbol]
                    # Get current price
                    klines = self.get_market_klines(symbol, interval='1m', limit=1)
                    if klines and len(klines) > 0:
                        current_price = float(klines[-1][4])
                        entry_price = float(position.get('entryPrice', 0))
                        size = float(position.get('size', 0))
                        side = position.get('side', '').upper()
                        
                        if entry_price > 0:
                            # Calculate unrealized PnL
                            if side == "LONG":
                                pnl = (current_price - entry_price) * abs(size)
                            else:  # SHORT
                                pnl = (entry_price - current_price) * abs(size)
                            
                            total_unrealized_pnl += pnl
            
            # Format active trades list
            active_trades_str = ', '.join([s.upper().replace('CMT_', '') for s in active_trades]) if active_trades else 'None'
            
            # Get equity and available balance for CSV logging
            equity = 0.0
            available = 0.0
            try:
                balance_data = self.get_account_balance()
                if balance_data:
                    equity = float(balance_data.get('equity', 0) or balance_data.get('totalEquity', 0) or 0)
                    available = float(balance_data.get('availableBalance', 0) or balance_data.get('available', 0) or 0)
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch balance for heartbeat: {str(e)}")
            
            # AI Wars: Heartbeat log format
            logger.info(f"💓 Heartbeat | Active Trades: [{active_trades_str}] | Total Unrealized PnL: {total_unrealized_pnl:+.2f} USDT")
            
            # AI Wars Audit: Append to performance.csv for monitoring
            try:
                import csv
                from datetime import datetime
                
                csv_exists = os.path.exists("performance.csv")
                with open("performance.csv", "a", newline='') as csvfile:
                    fieldnames = ['timestamp', 'equity', 'available', 'unrealized_pnl', 'active_trades_count']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    # Write header if file is new
                    if not csv_exists:
                        writer.writeheader()
                    
                    # Write performance row
                    writer.writerow({
                        'timestamp': datetime.now().isoformat(),
                        'equity': f"{equity:.2f}",
                        'available': f"{available:.2f}",
                        'unrealized_pnl': f"{total_unrealized_pnl:+.2f}",
                        'active_trades_count': len(active_trades)
                    })
            except Exception as e:
                logger.error(f"Failed to write to performance.csv: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to log heartbeat: {str(e)}")
        finally:
            # Update timestamp to reflect actual completion time
            self.last_heartbeat_time = time.time()
