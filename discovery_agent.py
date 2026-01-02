"""
Discovery Agent - Dynamic API mapping for WEEX exchange
Updated: Added Binance.us fallback and Mock Safety Net to bypass 451 Regional Blocks.
"""
import ccxt
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscoveryAgent:
    """
    Discovery Agent: Dynamically maps WEEX API capabilities.
    US-COMPATIBLE: Uses binanceus as a fallback to avoid 451 errors on US servers.
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, api_password: str = None, exchange_id: str = 'binanceus'):
        """
        Initialize Discovery Agent.
        Defaults to 'binanceus' for US-based server compatibility (DigitalOcean).
        """
        try:
            # Dynamically load the exchange class from CCXT
            exchange_class = getattr(ccxt, exchange_id.lower(), None)
            
            if exchange_class is None:
                logger.warning(f"Exchange '{exchange_id}' not found, defaulting to 'binanceus'")
                exchange_class = ccxt.binanceus

            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            # Add credentials only if provided
            if api_key and api_secret:
                config.update({'apiKey': api_key, 'secret': api_secret})
                if api_password:
                    config['password'] = api_password

            self.exchange = exchange_class(config)
            logger.info(f"✅ Exchange initialized: {self.exchange.id}")

        except Exception as e:
            logger.error(f"Failed to initialize exchange: {str(e)}")
            # Ultimate fallback to binanceus in public mode
            self.exchange = ccxt.binanceus({'enableRateLimit': True})

        self.capabilities: Dict[str, Any] = {}

    async def discover_capabilities(self) -> Dict[str, Any]:
        """
        Discover exchange capabilities. 
        Includes a Mock Fallback to ensure the engine NEVER crashes due to API blocks.
        """
        logger.info(f"🔍 [Aether-Evo] Starting discovery on {self.exchange.id}...")
        
        try:
            # Attempt to fetch real market data
            markets = await asyncio.to_thread(self.exchange.load_markets)
            symbols = list(markets.keys())
            logger.info(f"✅ Live Connection Successful: {len(symbols)} symbols found.")
            
        except Exception as e:
            logger.warning(f"⚠️ API Connection Blocked ({e}). ACTIVATING SHADOW MOCK MODE.")
            # MOCK DATA: Provides valid structure so the rest of the bot doesn't crash
            markets = {
                'BTC/USDT': {'symbol': 'BTC/USDT', 'base': 'BTC', 'quote': 'USDT', 'active': True},
                'ETH/USDT': {'symbol': 'ETH/USDT', 'base': 'ETH', 'quote': 'USDT', 'active': True},
                'SOL/USDT': {'symbol': 'SOL/USDT', 'base': 'SOL', 'quote': 'USDT', 'active': True}
            }
            symbols = list(markets.keys())

        # Map capabilities for the Perception and Evolution agents
        self.capabilities = {
            'symbols': symbols,
            'timeframes': getattr(self.exchange, 'timeframes', {'1m': '1m', '5m': '5m', '15m': '15m'}),
            'features': self.exchange.has,
            'markets': markets,
            'last_discovery': datetime.now().isoformat(),
            'mode': 'MOCK' if 'BTC/USDT' in markets and len(markets) < 10 else 'LIVE'
        }
        
        return self.capabilities

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> List[List]:
        """Fetch OHLCV data with error handling for regional blocks"""
        try:
            return await asyncio.to_thread(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {str(e)}")
            # Return empty list to prevent crash; the perception agent will handle the 'None' state
            return []

    def get_market_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached market information"""
        return self.capabilities.get('markets', {}).get(symbol)
