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
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


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
        
        # Precision settings for different symbols
        self.precision_map = {
            "cmt_btcusdt": 4,  # BTC: 4 decimals
            "cmt_ethusdt": 3,  # ETH: 3 decimals
            "cmt_solusdt": 2,  # SOL: 2 decimals
        }
    
    def round_qty(self, symbol: str, qty: float) -> float:
        """
        Round quantity to the correct precision for the symbol
        
        Args:
            symbol: Trading symbol
            qty: Quantity to round
            
        Returns:
            Rounded quantity
        """
        precision = self.precision_map.get(symbol, 2)  # Default to 2 decimals
        return round(qty, precision)
    
    def generate_signature(self, timestamp: str, method: str, request_path: str, 
                          query_string: str, body_str: str) -> str:
        """
        Generate HMAC SHA256 signature for WEEX API (Base64 encoded)
        
        Args:
            timestamp: Request timestamp in milliseconds
            method: HTTP method (GET, POST, etc.)
            request_path: API endpoint path
            query_string: Query parameters string
            body_str: Request body as JSON string
            
        Returns:
            Base64 encoded signature
        """
        message = timestamp + method.upper() + request_path + query_string + body_str
        signature = hmac.new(
            self.api_secret.encode('utf-8'), 
            message.encode('utf-8'), 
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def send_weex_request(self, method: str, path: str, query_params: str = "", 
                         body: Optional[Dict] = None) -> requests.Response:
        """
        Send authenticated request to WEEX API
        
        Args:
            method: HTTP method (GET, POST)
            path: API endpoint path
            query_params: Query parameters string (e.g., "?symbol=cmt_btcusdt")
            body: Request body dict (for POST requests)
            
        Returns:
            Response object
        """
        # Check for 521 cooldown
        if time.time() - self.last_521_error_time < self.cooldown_seconds:
            remaining = self.cooldown_seconds - (time.time() - self.last_521_error_time)
            logger.warning(f"🛑 521 Error cooldown active: {remaining:.1f}s remaining")
            raise Exception(f"Cooldown active: {remaining:.1f}s remaining")
        
        timestamp = str(int(time.time() * 1000))
        body_str = json.dumps(body) if body else ""
        signature = self.generate_signature(timestamp, method, path, query_params, body_str)
        
        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.api_password,
            "Content-Type": "application/json",
            "locale": "en-US"
        }
        
        url = f"{self.BASE_URL}{path}{query_params}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, data=body_str, timeout=10)
            
            # Check for 521 error (Firewall block)
            if response.status_code == 521:
                logger.error("🔥 521 Error: Firewall block detected! Starting 60s cooldown...")
                self.last_521_error_time = time.time()
                raise Exception("521 Firewall Error - Cooldown initiated")
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error("⏱️ Request timeout")
            raise
        except Exception as e:
            logger.error(f"❌ Request failed: {str(e)}")
            raise
    
    def get_market_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> List[List]:
        """
        Get K-lines (candlestick) data from WEEX
        Endpoint: GET /capi/v2/market/candles
        
        Args:
            symbol: Trading symbol (e.g., "cmt_btcusdt")
            interval: Time interval (1m, 5m, 15m, 1h, etc.)
            limit: Number of candles to retrieve (max 100)
            
        Returns:
            List of candles: [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            import urllib.parse
            path = "/capi/v2/market/candles"
            # URL encode parameters
            query_params = f"?symbol={urllib.parse.quote(symbol)}&granularity={urllib.parse.quote(interval)}&limit={limit}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 or data.get('success'):
                    klines = data.get('data', [])
                    logger.info(f"✅ Retrieved {len(klines)} candles for {symbol}")
                    return klines
                else:
                    logger.error(f"❌ K-lines error: {data.get('message', 'Unknown error')}")
                    return []
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get K-lines for {symbol}: {str(e)}")
            return []
    
    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        Get current funding rate for a symbol from WEEX
        Endpoint: GET /capi/v2/market/funding-rate
        
        Args:
            symbol: Trading symbol (e.g., "cmt_btcusdt")
            
        Returns:
            Funding rate as percentage (e.g., 0.01 for 0.01%), or None if failed
        """
        try:
            import urllib.parse
            path = "/capi/v2/market/funding-rate"
            query_params = f"?symbol={urllib.parse.quote(symbol)}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 or data.get('success'):
                    funding_data = data.get('data', {})
                    # Extract funding rate - try different field names
                    funding_rate = funding_data.get('fundingRate') or funding_data.get('funding_rate')
                    if funding_rate is not None:
                        # Convert to percentage if needed
                        funding_rate_pct = float(funding_rate) * 100 if abs(float(funding_rate)) < 1 else float(funding_rate)
                        logger.debug(f"✅ Retrieved funding rate for {symbol}: {funding_rate_pct:.4f}%")
                        return funding_rate_pct
                    else:
                        logger.warning(f"⚠️ Funding rate not found in response for {symbol}")
                        return None
                else:
                    logger.error(f"❌ Funding rate error: {data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get funding rate for {symbol}: {str(e)}")
            return None
    
    def get_order_book(self, symbol: str, depth: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get order book (market depth) from WEEX
        Endpoint: GET /capi/v2/market/depth
        
        Args:
            symbol: Trading symbol (e.g., "cmt_btcusdt")
            depth: Order book depth (default: 5)
            
        Returns:
            Dictionary with bids and asks, or None if failed
        """
        try:
            import urllib.parse
            path = "/capi/v2/market/depth"
            query_params = f"?symbol={urllib.parse.quote(symbol)}&depth={depth}"
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 or data.get('success'):
                    order_book = data.get('data', {})
                    logger.debug(f"✅ Retrieved order book for {symbol}")
                    return order_book
                else:
                    logger.error(f"❌ Order book error: {data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {str(e)}")
            return None
    
    def _extract_price_from_order(self, order: Any) -> float:
        """
        Extract price from order book entry (handles both list and dict formats)
        
        Args:
            order: Order entry (either [price, size] or {"price": x, "size": y})
            
        Returns:
            Price as float, or 0.0 if extraction fails
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
        
        Args:
            symbol: Trading symbol
            max_spread_pct: Maximum acceptable spread in percentage (default: 0.1%)
            
        Returns:
            True if spread is acceptable, False otherwise
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
            
            logger.debug(f"✅ Spread OK for {symbol}: {spread_pct:.3f}%")
            return True
            
        except Exception as e:
            logger.error(f"Failed to check spread for {symbol}: {str(e)}")
            return True  # Allow trade on error (failsafe)
    
    def get_account_balance(self) -> Optional[Dict[str, Any]]:
            try:
                path = "/capi/v2/account/accounts?productType=umcbl"
                response = self.send_weex_request("GET", path)
                
                if response.status_code == 200:
                    data = response.json()
                    collateral_list = data.get('collateral', [])
                    if collateral_list:
                        for item in collateral_list:
                            # Ensure we are looking at the USDT wallet (coin_id 2)
                            if str(item.get('coin_id')) == "2":
                                balance_value = item.get('amount')
                                logger.info(f"✅ Verified Competition Balance: {balance_value} USDT")
                                return item
                    
                    # If no list found, return a safe structure so .get('amount') doesn't crash
                    return {"amount": "0.00"} 
                return None
            except Exception as e:
                logger.error(f"Balance parsing error: {str(e)}")
                return None
    
    def set_leverage(self, symbol: str, leverage: int = 20) -> bool:
        """
        Set leverage for a symbol (Force 20x on startup as per requirements)
        Endpoint: POST /capi/v2/account/leverage
        
        Args:
            symbol: Trading symbol
            leverage: Leverage value (default: 20)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = "/capi/v2/account/leverage"
            body = {
                "symbol": symbol,
                "marginMode": "crossed",
                "leverage": str(leverage)
            }
            
            response = self.send_weex_request("POST", path, body=body)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 or data.get('success'):
                    logger.info(f"✅ Leverage set to {leverage}x for {symbol}")
                    return True
                elif "already set" in str(data.get('message', '')).lower():
                    logger.info(f"✅ Leverage already set to {leverage}x for {symbol}")
                    return True
                else:
                    logger.error(f"❌ Set leverage error: {data.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set leverage for {symbol}: {str(e)}")
            return False
    
    def has_open_position(self, symbol: str) -> bool:
        """
        Check if there's an open position for a symbol
        Endpoint: GET /capi/v2/account/positions
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if position exists, False otherwise
        """
        try:
            path = "/capi/v2/account/positions"
            query_params = f"?symbol={symbol}" if symbol else ""
            
            response = self.send_weex_request("GET", path, query_params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 or data.get('success'):
                    positions = data.get('data', [])
                    
                    # Check if any position has non-zero size
                    for pos in positions:
                        if pos.get('symbol') == symbol and float(pos.get('size', 0)) > 0:
                            logger.info(f"📊 Open position found for {symbol}: {pos.get('size')} @ {pos.get('entryPrice')}")
                            # Store position for TP/SL tracking
                            self.open_positions[symbol] = pos
                            return True
                    
                    # No position found
                    if symbol in self.open_positions:
                        del self.open_positions[symbol]
                    return False
                else:
                    logger.error(f"❌ Get positions error: {data.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to check position for {symbol}: {str(e)}")
            return False
    
    def place_market_order(self, symbol: str, side: str, size: float,
                          check_spread: bool = True) -> Optional[Dict[str, Any]]:
        """
        Place a market order with precision rounding and spread check
        Endpoint: POST /capi/v2/order/placeOrder
        
        Args:
            symbol: Trading symbol
            side: Order side ("BUY" or "SELL")
            size: Order size
            check_spread: Whether to check spread before placing order
            
        Returns:
            Order response dict or None if failed
        """
        try:
            # Spread guard
            if check_spread and not self.check_spread(symbol, max_spread_pct=0.1):
                logger.warning(f"🛑 Order rejected for {symbol} due to wide spread")
                return None
            
            # Round quantity to correct precision
            size = self.round_qty(symbol, size)
            
            path = "/capi/v2/order/placeOrder"
            body = {
                "symbol": symbol,
                "side": side.upper(),
                "type": "MARKET",
                "size": str(size)
            }
            
            response = self.send_weex_request("POST", path, body=body)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 or data.get('success'):
                    logger.info(f"✅ Market {side} order placed for {symbol}: {size}")
                    return data.get('data', {})
                else:
                    logger.error(f"❌ Place order error: {data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to place order for {symbol}: {str(e)}")
            return None
    
    def check_tp_sl_triggers(self, symbol: str, current_price: float) -> Optional[str]:
        """
        Check if TP (2%) or SL (1%) should be triggered for an open position
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            "TP" if take profit triggered, "SL" if stop loss triggered, None otherwise
        """
        if symbol not in self.open_positions:
            return None
        
        position = self.open_positions[symbol]
        entry_price = float(position.get('entryPrice', 0))
        position_side = position.get('side', '').upper()
        
        if entry_price == 0:
            return None
        
        # Calculate price change percentage
        price_change_pct = ((current_price - entry_price) / entry_price) * 100
        
        # For LONG positions
        if position_side == "LONG":
            if price_change_pct >= 2.0:
                logger.info(f"🎯 Take Profit triggered for {symbol}: {price_change_pct:.2f}% gain")
                return "TP"
            elif price_change_pct <= -1.0:
                logger.warning(f"🛑 Stop Loss triggered for {symbol}: {price_change_pct:.2f}% loss")
                return "SL"
        
        # For SHORT positions
        elif position_side == "SHORT":
            if price_change_pct <= -2.0:
                logger.info(f"🎯 Take Profit triggered for {symbol}: {abs(price_change_pct):.2f}% gain")
                return "TP"
            elif price_change_pct >= 1.0:
                logger.warning(f"🛑 Stop Loss triggered for {symbol}: {price_change_pct:.2f}% loss")
                return "SL"
        
        return None
    
    def close_position(self, symbol: str) -> bool:
        """
        Close an open position (market order)
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if successful, False otherwise
        """
        if symbol not in self.open_positions:
            logger.warning(f"⚠️ No position to close for {symbol}")
            return False
        
        position = self.open_positions[symbol]
        size = abs(float(position.get('size', 0)))
        side = "SELL" if position.get('side') == "LONG" else "BUY"
        
        result = self.place_market_order(symbol, side, size)
        
        if result:
            logger.info(f"✅ Position closed for {symbol}")
            del self.open_positions[symbol]
            return True
        else:
            logger.error(f"❌ Failed to close position for {symbol}")
            return False
