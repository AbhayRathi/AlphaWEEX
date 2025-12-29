"""
TradFi Oracle - Connects to Alpaca Market Data API
Monitors traditional finance markets (SPY, QQQ) to set global risk levels
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from data.shared_state import get_shared_state, RiskLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import alpaca-trade-api
try:
    from alpaca_trade_api.rest import REST, TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logger.warning("alpaca-trade-api not installed. Oracle will use fallback mode.")


class TradFiOracle:
    """
    TradFi Oracle: Monitors traditional finance markets
    
    Features:
    - Connect to Alpaca Market Data API
    - Fetch 1-hour bars for SPY and QQQ
    - Calculate percentage changes
    - Set global risk level based on SPY performance
    - Resilient with fallback mode
    """
    
    def __init__(
        self,
        alpaca_api_key: Optional[str] = None,
        alpaca_secret_key: Optional[str] = None,
        spy_threshold: float = -0.01  # -1% threshold
    ):
        """
        Initialize TradFi Oracle
        
        Args:
            alpaca_api_key: Alpaca API key (or from env ALPACA_API_KEY)
            alpaca_secret_key: Alpaca secret key (or from env ALPACA_SECRET_KEY)
            spy_threshold: SPY percentage change threshold for HIGH risk (default: -1%)
        """
        self.alpaca_api_key = alpaca_api_key or os.getenv("ALPACA_API_KEY", "")
        self.alpaca_secret_key = alpaca_secret_key or os.getenv("ALPACA_SECRET_KEY", "")
        self.spy_threshold = spy_threshold
        self.shared_state = get_shared_state()
        
        # Initialize Alpaca client if available
        self.alpaca_client = None
        if ALPACA_AVAILABLE and self.alpaca_api_key and self.alpaca_secret_key:
            try:
                self.alpaca_client = REST(
                    key_id=self.alpaca_api_key,
                    secret_key=self.alpaca_secret_key,
                    base_url='https://paper-api.alpaca.markets'  # Use paper trading for safety
                )
                logger.info("✅ TradFi Oracle initialized with Alpaca API")
            except Exception as e:
                logger.error(f"Failed to initialize Alpaca client: {str(e)}")
                self.alpaca_client = None
        else:
            logger.warning("⚠️  TradFi Oracle running in fallback mode (no Alpaca API)")
    
    def fetch_market_data(self) -> Dict[str, Any]:
        """
        Fetch 1-hour market data for SPY and QQQ
        
        Returns:
            Dictionary with market data and percentage changes
        """
        try:
            if self.alpaca_client is None:
                # Fallback mode: return mock data
                return self._get_fallback_data()
            
            # Fetch 1-hour bars for SPY and QQQ
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=2)  # Get last 2 hours
            
            spy_bars = self.alpaca_client.get_bars(
                "SPY",
                TimeFrame.Hour,
                start=start_time.isoformat(),
                end=end_time.isoformat()
            )
            
            qqq_bars = self.alpaca_client.get_bars(
                "QQQ",
                TimeFrame.Hour,
                start=start_time.isoformat(),
                end=end_time.isoformat()
            )
            
            # Convert to list
            spy_bars_list = [bar for bar in spy_bars]
            qqq_bars_list = [bar for bar in qqq_bars]
            
            if len(spy_bars_list) < 2:
                logger.warning("Insufficient SPY data, using fallback")
                return self._get_fallback_data()
            
            if len(qqq_bars_list) < 2:
                logger.warning("Insufficient QQQ data, using fallback")
                return self._get_fallback_data()
            
            # Calculate 1-hour percentage changes
            spy_prev_close = spy_bars_list[-2].c
            spy_current_close = spy_bars_list[-1].c
            spy_change_pct = ((spy_current_close - spy_prev_close) / spy_prev_close) * 100
            
            qqq_prev_close = qqq_bars_list[-2].c
            qqq_current_close = qqq_bars_list[-1].c
            qqq_change_pct = ((qqq_current_close - qqq_prev_close) / qqq_prev_close) * 100
            
            market_data = {
                'timestamp': datetime.now().isoformat(),
                'spy': {
                    'price': spy_current_close,
                    'change_pct': spy_change_pct,
                    'prev_price': spy_prev_close
                },
                'qqq': {
                    'price': qqq_current_close,
                    'change_pct': qqq_change_pct,
                    'prev_price': qqq_prev_close
                },
                'source': 'alpaca'
            }
            
            logger.info(
                f"📊 Market Data: SPY {spy_change_pct:+.2f}%, QQQ {qqq_change_pct:+.2f}%"
            )
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            logger.warning("Falling back to default data")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """
        Get fallback market data when API is unavailable
        Returns neutral/slightly positive market conditions
        
        Returns:
            Mock market data
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'spy': {
                'price': 450.0,
                'change_pct': 0.2,  # Slightly positive
                'prev_price': 449.1
            },
            'qqq': {
                'price': 380.0,
                'change_pct': 0.3,
                'prev_price': 378.86
            },
            'source': 'fallback'
        }
    
    def update_global_risk(self) -> RiskLevel:
        """
        Update global risk level based on market data
        
        Logic:
        - If SPY < -1%: Set global_risk_level = HIGH
        - If SPY >= -1%: Set global_risk_level = NORMAL
        
        Returns:
            Updated risk level
        """
        try:
            # Fetch market data
            market_data = self.fetch_market_data()
            
            # Get SPY change percentage
            spy_change_pct = market_data['spy']['change_pct']
            
            # Determine risk level based on threshold
            if spy_change_pct < (self.spy_threshold * 100):
                risk_level = RiskLevel.HIGH
                logger.warning(
                    f"🚨 HIGH RISK: SPY down {spy_change_pct:.2f}% "
                    f"(threshold: {self.spy_threshold * 100:.1f}%)"
                )
            else:
                risk_level = RiskLevel.NORMAL
                logger.info(
                    f"✅ NORMAL RISK: SPY {spy_change_pct:+.2f}% "
                    f"(threshold: {self.spy_threshold * 100:.1f}%)"
                )
            
            # Update shared state
            self.shared_state.set_global_risk_level(risk_level, market_data)
            
            return risk_level
            
        except Exception as e:
            logger.error(f"Error updating global risk: {str(e)}")
            logger.warning("Defaulting to NORMAL risk level")
            
            # Default to NORMAL on error (safe fallback)
            self.shared_state.set_global_risk_level(
                RiskLevel.NORMAL,
                {
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'source': 'error_fallback'
                }
            )
            
            return RiskLevel.NORMAL
    
    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get current market summary with risk assessment
        
        Returns:
            Dictionary with market summary
        """
        market_data = self.fetch_market_data()
        risk_level = self.shared_state.get_global_risk_level()
        
        return {
            'risk_level': risk_level,
            'market_data': market_data,
            'threshold': self.spy_threshold,
            'status': 'operational' if self.alpaca_client else 'fallback'
        }
