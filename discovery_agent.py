"""
Discovery Agent - Dynamic API mapping for WEEX exchange
Updated: Fixed missing fetch_balance and added Mock OHLCV generation.
"""
import ccxt
import asyncio
import time
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
        Initialize Discovery Agent with Binance.us fallback for US servers.
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
            
            if api_key and api_secret:
                config.update({'apiKey': api_key, 'secret': api_secret})
                if api_password:
                    config['password'] = api_password

            self.exchange = exchange_class(config)
            logger.info(f"✅ Exchange initialized: {self.exchange.id}")

        except Exception as e:
            logger.error(f"Failed to initialize exchange: {str(e)}")
            self.exchange = ccxt.binanceus({'enableRateLimit': True})

        self.capabilities: Dict[str, Any] = {}

    async def discover_capabilities(self) -> Dict[str, Any]:
        """
        Discover capabilities. Triggers MOCK MODE if blocked by regional 451 errors.
        """
        logger.info(f"🔍 [Aether-Evo] Starting discovery on {self.exchange.id}...")
        
        try:
            markets = await asyncio.to_thread(self.exchange.load_markets)
            symbols = list(markets.keys())
            logger.info(f"✅ Live Connection Successful: {len(symbols)} symbols found.")
            
        except Exception as e:
            logger.warning(f"⚠️ API Connection Blocked ({e}). ACTIVATING SHADOW MOCK MODE.")
            markets = {
                'BTC/USDT': {'symbol': 'BTC/USDT', 'base': 'BTC', 'quote': 'USDT', 'active': True},
                'ETH/USDT': {'symbol': 'ETH/USDT', 'base': 'ETH', 'quote': 'USDT', 'active': True},
                'SOL/USDT': {'symbol': 'SOL/USDT', 'base': 'SOL', 'quote': 'USDT', 'active': True}
            }
            symbols = list(markets.keys())

        self.capabilities = {
            'symbols': symbols,
            'timeframes': getattr(self.exchange, 'timeframes', {'1m': '1m', '5m': '5m', '15m': '15m'}),
            'features': self.exchange.has,
            'markets': markets,
            'last_discovery': datetime.now().isoformat(),
            'mode': 'MOCK' if len(symbols) <= 3 else 'LIVE'
        }
        
        return self.capabilities

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> List[List]:
        """
        Fetch OHLCV. If blocked by 451 error, generates MOCK data so the brain can keep working.
        """
        try:
            ohlcv = await asyncio.to_thread(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
            if not ohlcv:
                raise ValueError("Empty data received")
            return ohlcv
        except Exception as e:
            logger.debug(f"Live data failed ({e}), generating Shadow Mock candles for {symbol}...")
            # Generate dummy data: [timestamp, open, high, low, close, volume]
            # This allows the bot to 'simulate' trading at a $90,000 baseline.
            current_time = int(time.time() * 1000)
            mock_candles = []
            for i in range(limit):
                mock_candles.append([
                    current_time - (i * 900000), # 15m intervals
                    90000.0, 90150.0, 89850.0, 90000.0, 1.5
                ])
            return sorted(mock_candles, key=lambda x: x[0])

    async def fetch_balance(self) -> Dict[str, Any]:
        """
        Fetch balance. Returns 10,000 USDT Mock balance if blocked.
        """
        try:
            return await asyncio.to_thread(self.exchange.fetch_balance)
        except Exception as e:
            logger.warning(f"Balance fetch failed: {e}. Providing Shadow Portfolio (10k USDT).")
            return {
                'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0},
                'BTC': {'free': 0.0, 'used': 0.0, 'total': 0.0},
                'timestamp': int(time.time() * 1000),
                'datetime': datetime.now().isoformat()
            }

    def get_market_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached market information"""
        return self.capabilities.get('markets', {}).get(symbol)
