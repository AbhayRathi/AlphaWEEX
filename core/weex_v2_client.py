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
import re
import random
from typing import Union, Dict, Any, Optional, List
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
    
    # Cloudflare 521 Hardening: Jitter bounds for backoff calculations
    JITTER_521_MIN = 5.0    # Minimum jitter for 521 errors (seconds)
    JITTER_521_MAX = 25.0   # Maximum jitter for 521 errors (seconds)
    JITTER_TIMEOUT_MIN = 0.5  # Minimum jitter for timeout errors (seconds)
    JITTER_TIMEOUT_MAX = 2.5  # Maximum jitter for timeout errors (seconds)
    
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
        
        # Cloudflare 521 Hardening: Persistent Session with browser-like defaults
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=8, pool_maxsize=16, max_retries=Retry(total=0))
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Connection": "keep-alive",
        })
        
        # Cloudflare 521 Hardening: Environment tunables
        self.api_delay = float(os.getenv("WEEX_API_DELAY", "0"))
        self._cooldown_base = int(os.getenv("WEEX_521_BASE_BACKOFF", "10"))
        self._cooldown_cap = int(os.getenv("WEEX_521_MAX_BACKOFF", "60"))
        
        # Cloudflare 521 Hardening: Per-route(+symbol) cooldown tracking
        self._cooldown_by_key: Dict[str, float] = {}
        self._last_521_by_key: Dict[str, float] = {}
        
        # Track open positions for TP/SL management
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        
        # AI Wars: Multi-trade state tracking
        self.active_order_ids: Dict[str, str] = {}  # {symbol: order_id}
        self.active_symbols: set = set()  # Set of symbols with active positions/orders
        self.last_heartbeat_time = 0  # Track last heartbeat log time
        
        # Alpha-Apex: Track position scaling state
        # {symbol: {"partial_taken": bool, "breakeven_set": bool, "reinvested": bool, "original_size": float}}
        self.position_scaling_state: Dict[str, Dict[str, Any]] = {}
        
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
        
        # Contract discovery: Cache for symbol resolution
        self._contract_map: Dict[str, str] = {}
        self._contract_map_timestamp: float = 0
        self._contract_map_ttl: int = 3600  # Cache for 60 minutes
        
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
        Clean symbol for API calls: remove 'cmt_' prefix (case-insensitive) and convert to UPPERCASE
        """
        if not symbol:
            return ""
        # Remove cmt_ prefix (case-insensitive) and convert to uppercase
        cleaned = symbol.lower().replace('cmt_', '').upper()
        return cleaned
    
    def _extract_internal_key(self, contract: Dict[str, Any]) -> Optional[str]:
        """
        Extract internal symbol key from contract data with tolerant field parsing
        
        Args:
            contract: Contract data dict from API response
            
        Returns:
            Internal symbol key (e.g., BTCUSDT) or None if extraction fails
            
        Extraction strategy:
        1. If baseCoin and quoteCoin exist, use them (e.g., BTC + USDT = BTCUSDT)
        2. Otherwise, extract from exchange symbol by removing suffixes:
           - BTCUSDT_UMCBL -> BTCUSDT
           - BTCUSDT-PERP -> BTCUSDT
        
        Tolerates field variations:
        - Base: baseCoin, base, baseCurrency
        - Quote: quoteCoin, quote, quoteCurrency
        - Symbol: symbol, contractSymbol, symbolName, productId
        """
        # Try to extract base and quote coins (most reliable)
        # Tolerate field variations
        base = contract.get('baseCoin') or contract.get('base') or contract.get('baseCurrency') or ''
        quote = contract.get('quoteCoin') or contract.get('quote') or contract.get('quoteCurrency') or ''
        
        if base and quote:
            # Normalize to uppercase and concatenate
            return f"{base.upper()}{quote.upper()}"
        
        # Fallback: extract from exchange symbol
        # Tolerate multiple field names for the exchange symbol
        exchange_symbol = (contract.get('symbol') or 
                          contract.get('contractSymbol') or 
                          contract.get('symbolName') or
                          contract.get('productId') or '')
        
        if not exchange_symbol:
            return None
        
        # Remove common suffixes to get internal key
        # Order matters: try specific suffixes first
        for suffix in ['_UMCBL', '-PERP', '_PERP']:
            if suffix in exchange_symbol:
                return exchange_symbol.replace(suffix, '').upper()
        
        # If no suffix found, check if it contains USDT (common base pattern)
        # e.g., "BTCUSDT" -> "BTCUSDT"
        if 'USDT' in exchange_symbol.upper():
            return exchange_symbol.split('_')[0].split('-')[0].upper()
        
        return None
    
    def load_contracts(self) -> Dict[str, str]:
        """
        Load contract discovery data from WEEX V2 API with tolerant parsing
        
        Tries endpoints in order:
        1. /capi/v2/market/contracts?productType=umcbl
        2. /capi/v2/public/contracts?productType=umcbl
        
        Builds mapping: internal symbol (BTCUSDT) -> exchange symbol (BTCUSDT_UMCBL)
        Caches result for 60 minutes.
        
        Supports WEEX_CONTRACT_MAP_OVERRIDE env var for CI/testing:
        Set to JSON string like: {"BTCUSDT":"BTCUSDT_UMCBL","ETHUSDT":"ETHUSDT_UMCBL"}
        
        Returns:
            Dict mapping internal symbols to exchange symbols
        """
        # Check for CI override first
        override = os.getenv("WEEX_CONTRACT_MAP_OVERRIDE")
        if override:
            try:
                override_map = json.loads(override)
                self._contract_map = override_map
                self._contract_map_timestamp = time.time()
                logger.info(f"✅ Using contract map override ({len(override_map)} symbols)")
                return override_map
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse WEEX_CONTRACT_MAP_OVERRIDE: {e}")
        
        # Check if cache is still fresh
        now = time.time()
        if self._contract_map and (now - self._contract_map_timestamp) < self._contract_map_ttl:
            logger.debug(f"Using cached contract map ({len(self._contract_map)} symbols)")
            return self._contract_map
        
        logger.info("🔍 Loading contract discovery from WEEX V2 API...")
        
        endpoints = [
            "/capi/v2/market/contracts?productType=umcbl",
            "/capi/v2/public/contracts?productType=umcbl"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.send_weex_request("GET", endpoint.split('?')[0], f"?{endpoint.split('?')[1]}")
                
                if response and response.status_code == 200:
                    data = response.json()
                    
                    # Parse response - handle both direct list and nested data
                    contracts = []
                    if isinstance(data, list):
                        contracts = data
                    elif isinstance(data, dict):
                        contracts = data.get('data', [])
                    
                    if not contracts:
                        logger.warning(f"⚠️ No contracts returned from {endpoint}")
                        continue
                    
                    # Build mapping with tolerant field parsing
                    contract_map = {}
                    for contract in contracts:
                        internal_key = self._extract_internal_key(contract)
                        if internal_key:
                            # Extract exchange symbol with field name tolerance
                            exchange_symbol = (contract.get('symbol') or 
                                              contract.get('contractSymbol') or 
                                              contract.get('symbolName') or
                                              contract.get('productId'))
                            if exchange_symbol:
                                contract_map[internal_key] = exchange_symbol
                            else:
                                # If no exchange symbol found, use fallback
                                contract_map[internal_key] = f"{internal_key}_UMCBL"
                    
                    if contract_map:
                        self._contract_map = contract_map
                        self._contract_map_timestamp = now
                        logger.info(f"✅ Loaded {len(contract_map)} contract mappings from {endpoint}")
                        return contract_map
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to load contracts from {endpoint}: {str(e)}")
                continue
        
        # If all endpoints failed, log warning but don't fail
        logger.warning("⚠️ Contract discovery failed on all endpoints; will use fallback resolution")
        return {}
    
    def resolve_contract_symbol(self, symbol: str) -> str:
        """
        Resolve internal symbol (BTCUSDT) to exchange contract symbol (BTCUSDT_UMCBL)
        
        Args:
            symbol: Internal symbol (e.g., BTCUSDT, cmt_btcusdt)
        
        Returns:
            Exchange contract symbol (e.g., BTCUSDT_UMCBL)
        """
        # Clean the symbol first
        clean_sym = self.clean_symbol(symbol)
        
        # Ensure contract map is loaded
        if not self._contract_map or (time.time() - self._contract_map_timestamp) >= self._contract_map_ttl:
            self.load_contracts()
        
        # Try to find in map
        if clean_sym in self._contract_map:
            exchange_sym = self._contract_map[clean_sym]
            logger.info(f"Resolved symbol: {clean_sym} → {exchange_sym}")
            return exchange_sym
        
        # Fallback: use _UMCBL suffix (most common for WEEX V2 perpetual contracts)
        # Note: WEEX V2 uses BTCUSDT_UMCBL format for USDT-margined perpetual contracts
        exchange_sym = f"{clean_sym}_UMCBL"
        logger.warning(f"⚠️ Symbol not in contract map, using fallback: {clean_sym} → {exchange_sym}")
        return exchange_sym
    
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
    
    def _cooldown_key(self, path: str, query_params: str = "", payload: Optional[dict] = None) -> str:
        """
        Cloudflare 521 Hardening: Generate cooldown key from path, query params, and symbol.
        
        Args:
            path: API endpoint path
            query_params: Query parameters string
            payload: Request payload (dict or None)
            
        Returns:
            str: Cooldown key in format "path?query" or "path?query:SYMBOL"
        """
        # Include query params in the key for more specific scoping
        key = f"{path}{query_params}" if query_params else path
        
        try:
            # Add symbol from payload if present for even finer scoping
            if isinstance(payload, dict) and payload.get("symbol"):
                key = f"{key}:{str(payload['symbol']).upper()}"
        except (KeyError, AttributeError, TypeError) as e:
            # Log but don't fail - just use path+query without symbol
            logger.debug(f"Could not extract symbol from payload for cooldown key: {e}")
        
        return key
    
    def _cooldown_remaining(self, key: str) -> float:
        """
        Cloudflare 521 Hardening: Calculate remaining cooldown time for a key.
        
        Args:
            key: Cooldown key (from _cooldown_key)
            
        Returns:
            float: Remaining cooldown time in seconds (0.0 if no cooldown active)
        """
        last = self._last_521_by_key.get(key, 0.0)
        dur = self._cooldown_by_key.get(key, 0.0)
        return max(0.0, (last + dur) - time.time())
    
    def _calculate_backoff(self, attempt: int, jitter_min: float, jitter_max: float) -> float:
        """
        Cloudflare 521 Hardening: Calculate backoff time with jittered exponential backoff.
        
        Args:
            attempt: Current retry attempt number (0-indexed)
            jitter_min: Minimum jitter to add (seconds)
            jitter_max: Maximum jitter to add (seconds)
            
        Returns:
            float: Backoff time in seconds
        """
        base_backoff = min(self._cooldown_base * (2 ** attempt), self._cooldown_cap)
        jitter = random.uniform(jitter_min, jitter_max)
        return base_backoff + jitter
    
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
                            body: Union[Dict, str, None] = None, 
                            timeout: tuple = (5, 15), max_retries: int = 3) -> requests.Response:
        """
        Send authenticated request to WEEX API with per-route(+symbol) cooldown.
        
        Cloudflare 521 Hardening:
        - Per-route(+symbol) cooldown tracking
        - Jittered exponential backoff for 521 errors
        - Different handling for timeout errors (408, 522, 524)
        - Clears cooldown on successful 200 response
        
        Args:
            method: HTTP method (GET, POST)
            path: API endpoint path
            query_params: Query parameters string
            body: Request body (dict or string)
            timeout: Request timeout tuple (connect, read)
            max_retries: Maximum number of retry attempts
            
        Returns:
            requests.Response: Successful response
            
        Raises:
            Exception: If cooldown is active or max retries exceeded
        """
        # Prepare payload for cooldown key generation
        payload = body if isinstance(body, dict) else None
        key = self._cooldown_key(path, query_params, payload)
        
        for attempt in range(max_retries):
            # Check per-route cooldown
            rem = self._cooldown_remaining(key)
            if rem > 0:
                raise Exception(f"Cooldown active for {key}: {rem:.1f}s remaining")
            
            # Apply API delay if configured
            if self.api_delay > 0:
                time.sleep(self.api_delay)
            
            timestamp = str(int(time.time() * 1000))
            
            # Strip cmt_ prefix from symbols in payload
            if body and isinstance(body, dict):
                if 'symbol' in body:
                    body['symbol'] = body['symbol'].replace('cmt_', '').upper()
            
            # Strip cmt_ prefix from symbols in query parameters
            if query_params and 'symbol=' in query_params:
                query_params = re.sub(r'symbol=cmt_([^&]+)', lambda m: f'symbol={m.group(1).upper()}', query_params, flags=re.IGNORECASE)
                query_params = re.sub(r'symbol=([^&]+)', lambda m: f'symbol={m.group(1).upper()}', query_params)
            
            # Handle body stringification
            if body:
                if isinstance(body, dict):
                    body_str = json.dumps(body, separators=(',', ':'))
                else:
                    body_str = body
            else:
                body_str = ""
            
            # Generate signature
            signature = self.generate_signature(timestamp, method, path, query_params, body_str)
            
            headers = {
                "ACCESS-KEY": self.api_key,
                "ACCESS-SIGN": signature,
                "ACCESS-PASSPHRASE": self.api_password,
                "ACCESS-TIMESTAMP": timestamp,
                "Content-Type": "application/json",
                "locale": "en-US"
            }
            
            url = f"{self.BASE_URL}{path}{query_params}"
            
            try:
                # Make the request using the session
                if method.upper() == "GET":
                    response = self.session.get(url, headers=headers, timeout=timeout)
                else:
                    response = self.session.post(url, headers=headers, data=body_str, timeout=timeout)
                
                # Handle successful response
                if response.status_code == 200:
                    # Clear cooldown for this key on success
                    self._last_521_by_key.pop(key, None)
                    self._cooldown_by_key.pop(key, None)
                    return response
                
                # Handle 521 errors with per-key cooldown
                if response.status_code == 521:
                    backoff = self._calculate_backoff(attempt, self.JITTER_521_MIN, self.JITTER_521_MAX)
                    self._last_521_by_key[key] = time.time()
                    self._cooldown_by_key[key] = backoff
                    logger.warning(f"🔥 521 Error for {key}! Attempt {attempt + 1}/{max_retries}, cooldown: {backoff:.1f}s")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise Exception(f"Request to {key} exhausted retries after 521 errors")
                
                # Handle timeout errors (408, 522, 524) with immediate backoff
                if response.status_code in (408, 522, 524):
                    backoff = self._calculate_backoff(attempt, self.JITTER_TIMEOUT_MIN, self.JITTER_TIMEOUT_MAX)
                    logger.warning(f"⏱️ Timeout {response.status_code} for {key}! Attempt {attempt + 1}/{max_retries}, backoff: {backoff:.1f}s")
                    time.sleep(backoff)
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise Exception(f"Request to {key} exhausted retries after timeout errors")
                
                # For other status codes, return the response (let caller handle)
                return response
                
            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                # Handle transport errors like RemoteDisconnected
                if "RemoteDisconnected" in str(e) or "Connection" in str(e):
                    backoff = self._calculate_backoff(attempt, self.JITTER_521_MIN, self.JITTER_521_MAX)
                    self._last_521_by_key[key] = time.time()
                    self._cooldown_by_key[key] = backoff
                    logger.warning(f"🔌 Connection error for {key}! Attempt {attempt + 1}/{max_retries}, cooldown: {backoff:.1f}s")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise Exception(f"Request to {key} exhausted retries after connection errors")
                else:
                    raise
            except Exception as e:
                # For unexpected errors, raise immediately
                logger.error(f"❌ Request to {key} failed: {str(e)}")
                raise
        
        # Should not reach here due to retry loop logic
        raise Exception(f"Request to {key} exhausted retries")

    # -------------------------------------------------------------------------
    # CRITICAL FIX 1: Market K-Lines (Returns Numbers, not Strings)
    # -------------------------------------------------------------------------
    def get_market_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> List[List[float]]:
        """
        Get K-lines (candlestick) data from WEEX
        Endpoint: GET /capi/v2/market/candles
        """
        try:
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            
            path = "/capi/v2/market/candles"
            
            query_params = f"?symbol={urllib.parse.quote(exchange_symbol)}&granularity={interval}&limit={limit}"
            
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
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            
            path = "/capi/v2/market/funding-rate"
            query_params = f"?symbol={urllib.parse.quote(exchange_symbol)}"
            
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
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            
            # We use the ticker endpoint for the latest price
            path = "/capi/v2/market/ticker"
            query_params = f"?symbol={exchange_symbol}"
            
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
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            
            path = "/capi/v2/market/depth"
            query_params = f"?symbol={urllib.parse.quote(exchange_symbol)}&depth={depth}"
            
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
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            
            path = "/capi/v2/market/ticker"
            query_params = f"?symbol={urllib.parse.quote(exchange_symbol)}"
            
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
            path = "/capi/v2/account/getAccounts"
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
                                   str(item.get('coin', '')).upper() == "USDT" or str(item.get('coinName', '')).upper() == "USDT")
                        if is_usdt:
                            # Comprehensive equity key checking: try totalEquity, equity, accountEquity, available
                            equity = 0.0  # Default to 0.0 if no valid value found
                            found_value = False  # Track if we found any valid value
                            for key in ['totalEquity', 'equity', 'accountEquity', 'available', 'amount', 'legacy_amount']:
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
                
                logger.error(f"❌ No balance data found after {retry_count} retries (max: {max_retries})")
                return None
                
            # Handle 521/403 errors - should be handled by send_weex_request, but add extra safety
            if response.status_code in [521, 403]:
                if retry_count < max_retries:
                    logger.warning(f"🛑 Firewall active ({response.status_code}). Waiting 60s for a clear window... (Retry {retry_count + 1}/{max_retries})")
                    time.sleep(60)
                    return self.get_account_balance(retry_count=retry_count + 1, max_retries=max_retries)
                
                raise ConnectionError(f"Failed to retrieve balance after {max_retries} retries due to {response.status_code} error. Please check your IP whitelist and network connectivity.")
                    
            # Handle other non-200 status codes
            if response.status_code != 200:
                raise ConnectionError(f"Failed to retrieve balance: HTTP {response.status_code}. Response: {response.text}")
            
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
    
    def get_account_assets(self) -> float:
        """
        Get account USDT balance from WEEX V2 Contract API.
        This method specifically uses the /capi/v2/account/getAccounts endpoint
        to retrieve asset data in the V2 response format (Futures Vault).
        
        Returns:
            float: USDT equity (total value including unrealized PnL), or 0.0 if not found
        """
        try:
            # Use the official WEEX V2 Contract API endpoint
            res = self.send_weex_request("GET", "/capi/v2/account/getAccounts")
            
            if res and res.status_code == 200:
                response_data = res.json()
                
                
                # WEEX V2: Check collateral format first
                if isinstance(response_data, dict) and "collateral" in response_data:
                    for item in response_data.get("collateral", []):
                        if item.get("coin") == "USDT":
                            equity = float(item.get("amount") or item.get("legacy_amount") or "0")
                            logger.info(f"💰 USDT Equity: ${equity:.2f}")
                            return equity
                    return 0.0
                
                    # WEEX V2: Check collateral format
                    if isinstance(response_data, dict) and "collateral" in response_data:
                        for item in response_data.get("collateral", []):
                            if item.get("coin") == "USDT":
                                equity = float(item.get("amount") or item.get("legacy_amount") or "0")
                                return {"totalEquity": equity, "equity": equity}
                        logger.warning("No USDT in collateral")
                        return None
                    
                # Handle both response formats: raw list or dict with "data" key
                accounts_list = []
                if isinstance(response_data, list):
                    # Direct list response: [{...}, {...}]
                    accounts_list = response_data
                    logger.debug("Response format: raw list")
                elif isinstance(response_data, dict):
                    # Dict response: {"code": "00000", "data": [{...}]}
                    if response_data.get("code") == "00000":
                        accounts_list = response_data.get("data", [])
                        logger.debug("Response format: dict with 'data' key")
                    else:
                        error_code = response_data.get('code')
                        error_msg = response_data.get('msg', 'No error message provided')
                        logger.error(f"API returned error code: {error_code}, message: {error_msg}")
                        return 0.0
                
                # Parse USDT equity from accounts
                for account in accounts_list:
                    if account.get("coinName") == "USDT":
                        equity = float(account.get("equity", 0.0))
                        logger.info(f"💰 USDT Equity: ${equity:.2f}")
                        return equity
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get account assets: {str(e)}")
            return 0.0
    
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
                margin_mode: DEPRECATED - Parameter kept for backward compatibility but is ignored. 
                            Always uses "isolated" as required by WEEX V2 API.
            
            Returns:
                bool: True if leverage was set successfully, False otherwise
            """
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            
            # Primary endpoint: /capi/v2/account/setLeverage (POST)
            path = "/capi/v2/account/setLeverage"
            
            # WEEX V2 API requires string format for all parameters
            body = {
                "symbol": exchange_symbol,
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
        # Resolve symbol to exchange contract symbol
        exchange_symbol = self.resolve_contract_symbol(symbol)
        
        try:
            path = "/capi/v2/account/position/allPosition"
            # Include symbol in query params for filtered results
            query_params = f"?symbol={urllib.parse.quote(exchange_symbol)}" if exchange_symbol else "" 
            
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
                        
                        if pos_symbol == exchange_symbol and size > 0:
                            logger.info(f"📊 Open position found for {exchange_symbol}: {size} units")
                            self.open_positions[exchange_symbol] = pos
                            return True
                    except (ValueError, TypeError):
                        continue
                
                if exchange_symbol in self.open_positions:
                    del self.open_positions[exchange_symbol]
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
            
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            
            side_map = {
                "BUY": "1", "SELL": "2",
                "CLOSE_LONG": "3", "CLOSE_SHORT": "4"
            }
            
            path = "/capi/v2/order/placeOrder"
            body_dict = {
                "symbol": exchange_symbol,
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
        # Alpha-Evo Final: Use clean_symbol helper for consistency
        symbol = self.clean_symbol(symbol)
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
        # Alpha-Evo Final: Use clean_symbol helper instead of inline replace
        symbol = self.clean_symbol(symbol)
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
            
            # AI Wars: Remove from active tracking (use internal symbol format: lowercase)
            symbol_internal = symbol.lower()
            self.active_symbols.discard(symbol_internal)
            if symbol_internal in self.active_order_ids:
                del self.active_order_ids[symbol_internal]
            
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
            # Resolve symbol to exchange contract symbol
            exchange_symbol = self.resolve_contract_symbol(symbol)
            path = "/capi/v2/order/cancelAllOrders"
            
            body_dict = {
                "symbol": exchange_symbol.lower()
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
        # Alpha-Evo Final: Use clean_symbol helper for consistency
        symbol = self.clean_symbol(symbol)
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
