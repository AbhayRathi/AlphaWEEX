"""
WEEX Native Client - Native Python client using aiohttp
Implements direct API access to WEEX exchange with precision enforcement
"""
import aiohttp
import hmac
import hashlib
import json
import time
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, ROUND_DOWN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WEEXClient:
    """
    Native WEEX Exchange Client using aiohttp
    
    Features:
    - Direct API access via aiohttp
    - Precision enforcement (tick_size, size_increment)
    - Market info discovery
    - Order placement with validation
    """
    
    BASE_URL = "https://api.weex.com"
    
    def __init__(self, api_key: str, api_secret: str, api_password: str = ""):
        """
        Initialize WEEX Native Client
        
        Args:
            api_key: WEEX API key
            api_secret: WEEX API secret
            api_password: WEEX API password (if required)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_password = api_password
        self.session: Optional[aiohttp.ClientSession] = None
        self.market_info_cache: Dict[str, Dict[str, Any]] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, timestamp: str, method: str, endpoint: str, body: str = "") -> str:
        """
        Generate HMAC SHA256 signature for WEEX API
        
        Args:
            timestamp: Request timestamp in milliseconds
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            body: Request body (for POST requests)
            
        Returns:
            HMAC signature
        """
        message = f"{timestamp}{method}{endpoint}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, timestamp: str, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        """
        Generate request headers with authentication
        
        Args:
            timestamp: Request timestamp
            method: HTTP method
            endpoint: API endpoint
            body: Request body
            
        Returns:
            Headers dictionary
        """
        signature = self._generate_signature(timestamp, method, endpoint, body)
        
        headers = {
            "Content-Type": "application/json",
            "WEEX-ACCESS-KEY": self.api_key,
            "WEEX-ACCESS-SIGN": signature,
            "WEEX-ACCESS-TIMESTAMP": timestamp,
        }
        
        if self.api_password:
            headers["WEEX-ACCESS-PASSPHRASE"] = self.api_password
        
        return headers
    
    async def get_market_contracts(self) -> List[Dict[str, Any]]:
        """
        Fetch market contracts information
        Endpoint: GET /capi/v2/market/contracts
        
        Returns:
            List of market contracts with tick_size and size_increment
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use 'async with' context manager.")
        
        endpoint = "/capi/v2/market/contracts"
        timestamp = str(int(time.time() * 1000))
        headers = self._get_headers(timestamp, "GET", endpoint)
        
        try:
            async with self.session.get(
                f"{self.BASE_URL}{endpoint}",
                headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Cache market info for precision enforcement
                if data.get('code') == 200 and data.get('data'):
                    contracts = data['data']
                    for contract in contracts:
                        symbol = contract.get('symbol')
                        if symbol:
                            self.market_info_cache[symbol] = {
                                'tick_size': Decimal(str(contract.get('tickSize', '0.01'))),
                                'size_increment': Decimal(str(contract.get('sizeIncrement', '0.001'))),
                                'min_order_size': Decimal(str(contract.get('minOrderSize', '0'))),
                                'max_order_size': Decimal(str(contract.get('maxOrderSize', '0'))),
                                'contract_type': contract.get('contractType'),
                                'status': contract.get('status')
                            }
                    
                    logger.info(f"Fetched {len(contracts)} market contracts")
                    return contracts
                else:
                    logger.error(f"Failed to fetch contracts: {data}")
                    return []
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error fetching contracts: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching contracts: {str(e)}")
            raise
    
    def _enforce_precision(self, symbol: str, price: float, size: float) -> tuple[Decimal, Decimal]:
        """
        Enforce tick_size and size_increment precision from Discovery Agent
        
        Args:
            symbol: Trading symbol
            price: Order price
            size: Order size
            
        Returns:
            (adjusted_price, adjusted_size) with proper precision
        """
        if symbol not in self.market_info_cache:
            logger.warning(f"No market info cached for {symbol}. Using defaults.")
            return Decimal(str(price)), Decimal(str(size))
        
        market_info = self.market_info_cache[symbol]
        tick_size = market_info['tick_size']
        size_increment = market_info['size_increment']
        
        # Adjust price to tick_size precision
        price_decimal = Decimal(str(price))
        adjusted_price = (price_decimal / tick_size).quantize(Decimal('1'), rounding=ROUND_DOWN) * tick_size
        
        # Adjust size to size_increment precision
        size_decimal = Decimal(str(size))
        adjusted_size = (size_decimal / size_increment).quantize(Decimal('1'), rounding=ROUND_DOWN) * size_increment
        
        # Validate against min/max order sizes
        min_size = market_info.get('min_order_size', Decimal('0'))
        max_size = market_info.get('max_order_size', Decimal('0'))
        
        if adjusted_size < min_size:
            logger.warning(f"Order size {adjusted_size} below minimum {min_size}")
            adjusted_size = min_size
        
        if max_size > 0 and adjusted_size > max_size:
            logger.warning(f"Order size {adjusted_size} above maximum {max_size}")
            adjusted_size = max_size
        
        logger.info(f"Precision adjusted: price {price} -> {adjusted_price}, size {size} -> {adjusted_size}")
        return adjusted_price, adjusted_size
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        size: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Place an order on WEEX exchange
        Endpoint: POST /capi/v2/order/placeOrder
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USDT')
            side: Order side ('buy' or 'sell')
            order_type: Order type ('limit', 'market')
            size: Order size
            price: Order price (required for limit orders)
            **kwargs: Additional order parameters
            
        Returns:
            Order response from exchange
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use 'async with' context manager.")
        
        # Enforce precision before sending order
        if price is not None:
            adjusted_price, adjusted_size = self._enforce_precision(symbol, price, size)
        else:
            # For market orders, only adjust size
            _, adjusted_size = self._enforce_precision(symbol, 0, size)
            adjusted_price = None
        
        endpoint = "/capi/v2/order/placeOrder"
        timestamp = str(int(time.time() * 1000))
        
        # Build order payload
        order_data = {
            "symbol": symbol,
            "side": side.lower(),
            "type": order_type.lower(),
            "size": str(adjusted_size),
        }
        
        if adjusted_price is not None:
            order_data["price"] = str(adjusted_price)
        
        # Add any additional parameters
        order_data.update(kwargs)
        
        body = json.dumps(order_data)
        headers = self._get_headers(timestamp, "POST", endpoint, body)
        
        try:
            async with self.session.post(
                f"{self.BASE_URL}{endpoint}",
                headers=headers,
                data=body
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get('code') == 200:
                    logger.info(f"Order placed successfully: {data.get('data')}")
                    return data
                else:
                    logger.error(f"Order placement failed: {data}")
                    return data
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error placing order: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise
    
    def get_market_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached market information for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Market info dict or None if not cached
        """
        return self.market_info_cache.get(symbol)
    
    async def validate_order_precision(self, symbol: str, price: float, size: float) -> bool:
        """
        Validate if order parameters meet precision requirements
        
        Args:
            symbol: Trading symbol
            price: Order price
            size: Order size
            
        Returns:
            True if valid, False otherwise
        """
        if symbol not in self.market_info_cache:
            logger.warning(f"Cannot validate precision - no market info for {symbol}")
            return False
        
        adjusted_price, adjusted_size = self._enforce_precision(symbol, price, size)
        
        # Check if adjustment was needed
        price_matches = abs(float(adjusted_price) - price) < 1e-10
        size_matches = abs(float(adjusted_size) - size) < 1e-10
        
        if not price_matches or not size_matches:
            logger.warning(
                f"Order parameters need adjustment:\n"
                f"  Price: {price} -> {adjusted_price} (match: {price_matches})\n"
                f"  Size: {size} -> {adjusted_size} (match: {size_matches})"
            )
            return False
        
        return True
