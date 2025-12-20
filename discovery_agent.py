"""
Discovery Agent - Dynamic API mapping for WEEX exchange
"""
import ccxt
import asyncio
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscoveryAgent:
    """
    Discovery Agent: Dynamically maps WEEX API capabilities
    Discovers available trading pairs, timeframes, and features
    """
    
    def __init__(self, api_key: str, api_secret: str, api_password: str):
        """Initialize Discovery Agent with WEEX credentials"""
        self.exchange = ccxt.weex({
            'apiKey': api_key,
            'secret': api_secret,
            'password': api_password,
            'enableRateLimit': True,
        })
        self.capabilities: Dict[str, Any] = {}
        
    async def discover_capabilities(self) -> Dict[str, Any]:
        """Discover exchange capabilities and API features"""
        logger.info("Starting discovery of WEEX exchange capabilities...")
        
        try:
            # Load markets
            markets = await asyncio.to_thread(self.exchange.load_markets)
            
            # Discover available symbols
            symbols = list(markets.keys())
            
            # Discover timeframes
            timeframes = self.exchange.timeframes if hasattr(self.exchange, 'timeframes') else {}
            
            # Discover trading features
            has_features = {
                'fetchOHLCV': self.exchange.has.get('fetchOHLCV', False),
                'fetchTicker': self.exchange.has.get('fetchTicker', False),
                'fetchBalance': self.exchange.has.get('fetchBalance', False),
                'createOrder': self.exchange.has.get('createOrder', False),
                'fetchOpenOrders': self.exchange.has.get('fetchOpenOrders', False),
                'cancelOrder': self.exchange.has.get('cancelOrder', False),
            }
            
            self.capabilities = {
                'symbols': symbols,
                'timeframes': timeframes,
                'features': has_features,
                'markets': markets,
            }
            
            logger.info(f"Discovery complete: {len(symbols)} symbols, {len(timeframes)} timeframes")
            return self.capabilities
            
        except Exception as e:
            logger.error(f"Discovery failed: {str(e)}")
            raise
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> List[List]:
        """Fetch OHLCV data for a symbol"""
        try:
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                symbol,
                timeframe,
                limit=limit
            )
            return ohlcv
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {str(e)}")
            raise
    
    async def fetch_balance(self) -> Dict[str, Any]:
        """Fetch account balance"""
        try:
            balance = await asyncio.to_thread(self.exchange.fetch_balance)
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {str(e)}")
            raise
    
    async def get_market_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed market information for a symbol"""
        if symbol in self.capabilities.get('markets', {}):
            return self.capabilities['markets'][symbol]
        return None
