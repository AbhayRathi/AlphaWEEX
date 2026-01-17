"""
WEEX AI Trading Bot - Competition-Ready Implementation with LLM Strategy

Requirements:
1. Working Auth - WEEX v2 API with proper signature
2. Multi-Symbol Flexibility - Loop through multiple symbols
3. Data Retrieval - K-lines from /capi/v2/market/candles
4. Risk Management - 2% TP, 1% SL
5. Enhanced AI Logging - JSON format with 10-min heartbeat
6. Safety Guardrails - 20x leverage, position check, 521 cooldown
7. LLM-Based Strategy - Autonomous reasoning with OpenAI/Anthropic
8. SQLite Persistence - Trade history and performance tracking
"""
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from core.weex_v2_client import WEEXv2Client
from core.ai_logger import AITradingLogger
from core.db import DatabaseManager
from core.strategy_engine import StrategyEngine
from core.funding_rate_analyzer import FundingRateAnalyzer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('API_KEY') or os.getenv('WEEX_API_KEY')
API_SECRET = os.getenv('API_SECRET') or os.getenv('WEEX_API_SECRET')
API_PASSWORD = os.getenv('API_PASSWORD') or os.getenv('WEEX_API_PASSWORD')

# LLM Configuration
# Priority: DeepSeek > OpenAI > Anthropic (auto-detected in StrategyEngine)
LLM_PROVIDER = os.getenv('LLM_PROVIDER')  # Optional: 'openai', 'anthropic', or 'deepseek'
LLM_API_KEY = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')  # Optional: override default model
LLM_BASE_URL = os.getenv('LLM_BASE_URL')  # For DeepSeek: https://api.deepseek.com

# Multi-Symbol Support
# Updated Competition Symbol List (8 Pairs)
SYMBOL_LIST = [
    "cmt_btcusdt",   # Bitcoin
    "cmt_ethusdt",   # Ethereum
    "cmt_solusdt",   # Solana
    "cmt_ltcusdt",   # Litecoin
    "cmt_adausdt",   # Cardano
    "cmt_dogeusdt",  # Dogecoin
    "cmt_xrpusdt",   # XRP
    "cmt_bnbusdt"    # Binance Coin
]

# Risk Management
TAKE_PROFIT_PCT = 2.0  # 2% TP
STOP_LOSS_PCT = 1.0    # 1% SL
SL_THRESHOLD_LONG_PCT = 0.50   # 0.50% stop-loss for longs (used in Alpha-Apex partial profit system)
SL_THRESHOLD_SHORT_PCT = 0.40  # 0.40% stop-loss for shorts (tighter due to unlimited upside risk)
EQUITY_SIZING_PCT = 10.0  # 10% of equity per trade
KILL_SWITCH_PCT = 10.0  # Kill switch if equity drops >10% in 24h
GLOBAL_MAX_EXPOSURE_PCT = 25.0  # Critical Fix 2: Max 25% of equity in active positions

# Enhancement 5: Fee calculation
TAKER_FEE_PCT = 0.06  # 0.06% taker fee on WEEX
EFFECTIVE_TP_PCT = TAKE_PROFIT_PCT - (2 * TAKER_FEE_PCT)  # 2% - 0.12% = 1.88%
EFFECTIVE_SL_PCT = STOP_LOSS_PCT + TAKER_FEE_PCT  # 1% + 0.06% = 1.06%

# Trading Parameters
POSITION_SIZE = 0.001  # Default position size (adjust based on capital)
MAIN_LOOP_INTERVAL = 10  # Check every 10 seconds (Alpha-Apex aggressive mode)
MIN_CONFIDENCE = 0.75  # Alpha-Apex: Minimum confidence threshold
RSI_PERIOD = 9  # Alpha-Apex: 9-period RSI for faster signals
VOLATILITY_BYPASS_THRESHOLD = 0.5  # Alpha-Apex: If 5-min price change > 0.5%, allow trade at lower confidence
VOLATILITY_BYPASS_CONFIDENCE = 0.65  # Alpha-Apex: Lower confidence threshold during high volatility
MIN_ORDER_VALUE_USDT = 5.0  # Alpha-Apex: Minimum order value to avoid exchange rejection
AUTO_FLIP_COOLDOWN_SECONDS = 60  # Alpha-Apex: Cooldown between auto-flips to prevent whipsaw

# Bi-Directional Trading Enhancements
SHORT_POSITION_SIZE_REDUCTION = 0.80  # 20% smaller position size for shorts (unlimited risk)
SELL_SIGNAL_HIGH_CONFIDENCE = 0.78  # Higher confidence required for shorts (was 0.65)
STRONG_UPTREND_THRESHOLD = 0.02  # 2% - block shorts when SMA50 > SMA200 * 1.02
MAX_SHORT_HOLD_HOURS = 48  # Maximum hold time for shorts to avoid funding fee erosion


class CompetitionTradingBot:
    """
    Competition-Ready WEEX AI Trading Bot with LLM Strategy
    
    Features:
    - Multi-symbol trading
    - LLM-based autonomous decision making (OpenAI/Anthropic/DeepSeek)
    - Behavioral psychology integration (FOMO, Panic, Revenge, Liquidity Hunter)
    - 10% equity sizing with kill switch
    - Spread guard (reject if spread > 0.1%)
    - TP/SL risk management
    - Enhanced AI logging with reasoning
    - SQLite trade history persistence
    - Safety guardrails
    """
    
    def __init__(self, use_llm: bool = True, test_mode: bool = False):
        """
        Initialize the trading bot
        
        Args:
            use_llm: If True, use LLM strategy. If False, fallback to RSI/SMA (default: True)
            test_mode: If True, skip API credential validation for testing (default: False)
        """
        # Validate API credentials (skip in test mode)
        if not test_mode and (not API_KEY or not API_SECRET or not API_PASSWORD):
            raise ValueError("Missing API credentials. Please set API_KEY, API_SECRET, and API_PASSWORD in .env")
        
        # Initialize WEEX v2 client
        self.client = WEEXv2Client(API_KEY, API_SECRET, API_PASSWORD)
        
        # Initialize AI logger
        self.ai_logger = AITradingLogger("ai_trading.log")
        
        # Initialize database manager
        self.db = DatabaseManager("trading_memory.db")
        
        # Initialize funding rate analyzer
        self.funding_analyzer = FundingRateAnalyzer()
        
        # Initialize strategy engine (LLM or fallback)
        self.use_llm = use_llm
        self.strategy_engine = None
        self.behavioral_adversary = None
        
        if use_llm:
            if not LLM_API_KEY:
                logger.warning("⚠️ No LLM API key found (DEEPSEEK_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY). Falling back to RSI/SMA strategy.")
                self.use_llm = False
            else:
                try:
                    # Initialize BehavioralAdversary first
                    from agents.adversary import BehavioralAdversary
                    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
                    if deepseek_key:
                        self.behavioral_adversary = BehavioralAdversary(
                            deepseek_api_key=deepseek_key,
                            use_shadow_mode=False
                        )
                        logger.info("✅ BehavioralAdversary enabled")
                    
                    # Initialize StrategyEngine with auto-detection (pass None to use env vars)
                    # StrategyEngine will auto-detect provider from environment if not specified
                    self.strategy_engine = StrategyEngine(
                        provider=LLM_PROVIDER,  # None means auto-detect
                        api_key=LLM_API_KEY,  # None means auto-detect
                        model=LLM_MODEL,
                        base_url=LLM_BASE_URL,
                        behavioral_adversary=self.behavioral_adversary
                    )
                    logger.info(f"✅ LLM Strategy Engine enabled: {self.strategy_engine.provider}")
                except Exception as e:
                    logger.error(f"Failed to initialize LLM: {str(e)}")
                    logger.warning("⚠️ Falling back to RSI/SMA strategy")
                    self.use_llm = False
        
        # Kill Switch state
        self.emergency_stop = False
        self.initial_equity = None
        self.equity_history = []  # Track equity over time
        
        # Enhancement 3: Stale order tracking
        self.pending_orders = {}  # {order_id: {"symbol": str, "timestamp": float, "side": str}}
        
        # Enhancement 7: Funding rate fetch monitoring
        self.funding_rate_fetch_success = 0
        self.funding_rate_fetch_total = 0
        self.last_funding_rate_log = time.time()
        
        # Enhancement 8: Position timeout tracking
        self.position_open_times = {}  # {symbol: timestamp}
        
        # Alpha-Apex: Auto-flip cooldown tracking
        self.last_flip_time = {}  # {symbol: timestamp}
        
        # NEW: Short entry time tracking for max hold time
        self.short_entry_times = {}  # Track when each short was opened
        
        # Running flag
        self.running = False
        
        logger.info("=" * 60)
        logger.info("🚀 WEEX AI TRADING BOT - COMPETITION READY")
        logger.info("=" * 60)
        logger.info(f"📊 Multi-Symbol Support: {', '.join(SYMBOL_LIST)}")
        logger.info(f"🎯 Risk Management: TP={TAKE_PROFIT_PCT}%, SL={STOP_LOSS_PCT}%")
        logger.info(f"💰 Equity Sizing: {EQUITY_SIZING_PCT}% per trade")
        logger.info(f"🛑 Kill Switch: {KILL_SWITCH_PCT}% drawdown limit")
        logger.info(f"🔄 Contrarian Sentiment: Funding Rate Analysis Enabled")
        logger.info("=" * 60)
    
    def initialize_leverage(self) -> None:
        """
        Force 20x leverage on startup for all symbols (Safety Guardrail)
        """
        logger.info("⚙️ Initializing leverage to 20x for all symbols...")
        
        for symbol in SYMBOL_LIST:
            success = self.client.set_leverage(symbol, leverage=20)
            self.ai_logger.log_leverage_set(symbol, 20, success)
            
            if not success:
                logger.warning(f"⚠️ Failed to set leverage for {symbol} (continuing anyway)")
        
        logger.info("✅ Leverage initialization complete")
    
    def get_current_equity(self) -> float:
        """
        Get current account equity in USDT
        
        Returns:
            Current equity
        """
        try:
            balance_data = self.client.get_account_balance()
            if balance_data:
                # Extract total equity from balance data
                # Check totalEquity first, then equity, handling 0.0 as valid
                total_equity = balance_data.get('totalEquity')
                if total_equity is not None:
                    return float(total_equity)
                
                equity = balance_data.get('equity')
                if equity is not None:
                    return float(equity)
            
            return 1000.0  # Default fallback only if no data
        except Exception as e:
            logger.error(f"Failed to get equity: {str(e)}")
            return 1000.0
    
    def calculate_position_size(self, symbol: str, current_price: float, leverage: int = 20, side: str = "BUY") -> float:
        """
        Calculate position size using 10% equity sizing
        Formula: qty = (Account_Balance * 0.10 * Leverage) / Current_Price
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            leverage: Trading leverage
            side: Trade side ("BUY" or "SELL")
            
        Returns:
            Position size rounded to correct precision
        """
        try:
            equity = self.get_current_equity()
            
            # Calculate position size
            position_value = equity * (EQUITY_SIZING_PCT / 100.0) * leverage
            
            # NEW: Smaller size for shorts to account for unlimited risk
            if side == "SELL":
                position_value *= SHORT_POSITION_SIZE_REDUCTION  # 20% smaller
                logger.info(f"📉 SHORT position sizing: Reduced by 20% for risk management")
            
            qty = position_value / current_price
            
            # Round to correct precision
            qty = self.client.round_qty(symbol, qty)
            
            logger.info(f"💰 Position size for {symbol}: {qty} (Equity: ${equity:.2f}, Price: ${current_price:.2f})")
            return qty
            
        except Exception as e:
            logger.error(f"Failed to calculate position size: {str(e)}")
            return POSITION_SIZE  # Fallback to default
    
    def calculate_total_exposure(self) -> float:
        """
        Critical Fix 2: Calculate current notional exposure as % of total equity
        
        Returns:
            Total exposure percentage
        """
        try:
            total_exposure = 0.0
            for symbol in SYMBOL_LIST:
                if self.client.has_open_position(symbol):
                    # Get position from client's tracking
                    pos = self.client.open_positions.get(symbol, {})
                    if pos:
                        # Calculate notional value = size * entry_price
                        size = abs(float(pos.get('size', 0)))
                        entry_price = float(pos.get('entryPrice', 0))
                        notional_value = size * entry_price
                        total_exposure += notional_value
            
            balance = self.client.get_account_balance()
            if balance and 'availableBalance' in balance:
                total_equity = float(balance['availableBalance'])
                return (total_exposure / total_equity) * 100 if total_equity > 0 else 0.0
            return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate total exposure: {str(e)}")
            return 0.0
    
    def check_kill_switch(self) -> bool:
        """
        Check if kill switch should be activated
        Kill switch activates if equity drops >10% in rolling 24-hour window
        
        Returns:
            True if kill switch activated, False otherwise
        """
        if self.emergency_stop:
            return True
        
        try:
            current_equity = self.get_current_equity()
            
            # Initialize baseline equity if first check
            if self.initial_equity is None:
                self.initial_equity = current_equity
                logger.info(f"📊 Initial equity baseline: ${self.initial_equity:.2f}")
                return False
            
            # Track equity history with timestamps
            from datetime import datetime, timedelta
            current_time = datetime.now()
            self.equity_history.append((current_time, current_equity))
            
            # Keep only last 24 hours of data
            cutoff_time = current_time - timedelta(hours=24)
            self.equity_history = [(t, e) for t, e in self.equity_history if t > cutoff_time]
            
            # Find highest equity in last 24 hours
            if len(self.equity_history) > 0:
                max_equity_24h = max(e for _, e in self.equity_history)
            else:
                max_equity_24h = self.initial_equity
            
            # Calculate drawdown from 24h high
            drawdown_pct = ((current_equity - max_equity_24h) / max_equity_24h) * 100
            
            # Activate kill switch if drawdown exceeds threshold
            if drawdown_pct < -KILL_SWITCH_PCT:
                logger.error(f"🚨 KILL SWITCH ACTIVATED! Drawdown: {drawdown_pct:.2f}% (Threshold: -{KILL_SWITCH_PCT}%)")
                logger.error(f"💰 Current: ${current_equity:.2f}, 24h High: ${max_equity_24h:.2f}")
                self.emergency_stop = True
                
                # Close all positions
                self.close_all_positions()
                
                # Log to AI logger
                self.ai_logger.log_error(
                    error_type="KILL_SWITCH",
                    error_message=f"Equity dropped {drawdown_pct:.2f}% in 24h",
                    context={"current_equity": current_equity, "max_equity_24h": max_equity_24h}
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Kill switch check failed: {str(e)}")
            return False
    
    def close_all_positions(self) -> None:
        """
        Emergency: Close all open positions
        """
        logger.warning("🛑 Closing all positions...")
        for symbol in SYMBOL_LIST:
            try:
                if self.client.has_open_position(symbol):
                    self.client.close_position(symbol)
                    logger.info(f"✅ Closed position for {symbol}")
            except Exception as e:
                logger.error(f"Failed to close position for {symbol}: {str(e)}")
    
    def cancel_stale_orders(self, max_age_seconds: int = 300) -> None:
        """
        Enhancement 3: Cancel orders that haven't filled after max_age_seconds (default 5 min)
        
        Args:
            max_age_seconds: Maximum age before canceling (default: 300 seconds = 5 minutes)
        """
        current_time = time.time()
        stale_orders = []
        
        for order_id, order_info in list(self.pending_orders.items()):
            age = current_time - order_info['timestamp']
            if age > max_age_seconds:
                try:
                    self.client.cancel_order(order_info['symbol'], order_id)
                    logger.warning(f"🗑️ Cancelled stale order {order_id} for {order_info['symbol']} (open for {age:.0f}s)")
                    stale_orders.append(order_id)
                except Exception as e:
                    logger.error(f"Failed to cancel stale order {order_id}: {str(e)}")
        
        for order_id in stale_orders:
            del self.pending_orders[order_id]
    
    def is_volume_spike(self, klines: List[List], threshold: float = 1.5) -> bool:
        """
        Enhancement 6: Check if recent volume is above average (prevents low-liquidity traps)
        
        Args:
            klines: K-lines data
            threshold: Volume multiplier threshold (default: 1.5)
            
        Returns:
            True if volume is acceptable, False if too low
        """
        if not klines or len(klines) < 2:
            return True  # Default to allowing trade if data insufficient
        
        volumes = [float(k[5]) for k in klines]  # Volume is index 5
        avg_volume = sum(volumes) / len(volumes)
        recent_volume = volumes[-1]
        
        is_spike = recent_volume > (avg_volume * threshold)
        if not is_spike:
            logger.info(f"Low volume detected: {recent_volume:.0f} vs avg {avg_volume:.0f} (threshold {threshold}x)")
        return is_spike
    
    def get_behavioral_tag(self, klines: List[List]) -> str:
        """
        Get behavioral psychology tag from BehavioralAdversary
        
        Args:
            klines: Market K-lines data
            
        Returns:
            Behavioral tag string
        """
        if not self.behavioral_adversary or not klines:
            return "NEUTRAL"
        
        try:
            current_price = float(klines[-1][4])
            market_data = {
                'price': current_price,
                'rsi': self.calculate_rsi([float(k[4]) for k in klines], RSI_PERIOD),
                'volume': float(klines[-1][5]) if len(klines[-1]) > 5 else 0.0,
                'price_change_pct': ((float(klines[-1][4]) - float(klines[0][4])) / float(klines[0][4]) * 100) if len(klines) > 1 else 0.0
            }
            
            psychology = self.behavioral_adversary.analyze_psychology(market_data)
            return psychology.get('detected_archetype', 'NEUTRAL')
            
        except Exception as e:
            logger.warning(f"Failed to get behavioral tag: {str(e)}")
            return "NEUTRAL"
    
    def calculate_rsi(self, closes: List[float], period: int = 9) -> float:
        """
        Calculate RSI indicator (Alpha-Apex: 9-period for faster signals)
        
        Args:
            closes: List of closing prices
            period: RSI period (default: 9)
            
        Returns:
            RSI value (0-100)
        """
        if len(closes) < period + 1:
            return 50.0  # Neutral if not enough data
        
        # Calculate price changes
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_sma(self, closes: List[float], period: int = 20) -> float:
        """
        Calculate Simple Moving Average
        
        Args:
            closes: List of closing prices
            period: SMA period (default: 20)
            
        Returns:
            SMA value
        """
        if len(closes) < period:
            return closes[-1] if closes else 0.0
        
        return sum(closes[-period:]) / period
    
    def analyze_market(self, klines: List[List]) -> Dict[str, Any]:
        """
        Analyze market data and generate indicators
        
        Args:
            klines: K-lines data [[timestamp, open, high, low, close, volume], ...]
            
        Returns:
            Dictionary with indicators and analysis
        """
        if not klines or len(klines) == 0:
            return {
                "valid": False,
                "reason": "No data available"
            }
        
        # Extract closing prices
        closes = [float(candle[4]) for candle in klines]
        volumes = [float(candle[5]) if len(candle) > 5 else 0.0 for candle in klines]
        
        current_price = closes[-1]
        
        # Calculate indicators (Alpha-Apex: 9-period RSI)
        rsi = self.calculate_rsi(closes, RSI_PERIOD)
        sma_20 = self.calculate_sma(closes, 20)
        sma_50 = self.calculate_sma(closes, 50)
        
        # Price change
        if len(closes) > 1 and closes[0] != 0:
            price_change_pct = ((current_price - closes[0]) / closes[0]) * 100
        else:
            price_change_pct = 0.0
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / min(20, len(volumes)) if volumes else 0.0
        current_volume = volumes[-1] if volumes else 0.0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return {
            "valid": True,
            "current_price": current_price,
            "rsi": rsi,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "price_change_pct": price_change_pct,
            "volume_ratio": volume_ratio,
            "avg_volume": avg_volume
        }
    
    def generate_signal(self, klines: List[List], symbol: str) -> Dict[str, Any]:
        """
        Generate trading signal using LLM or fallback to RSI/SMA, adjusted with funding rate analysis
        
        Args:
            klines: K-lines data
            symbol: Trading symbol
            
        Returns:
            Signal dictionary with action, confidence, and reasoning (adjusted with funding rate)
        """
        # Get account balance (for LLM context)
        # In a real implementation, fetch this from the API
        balance = 1000.0  # Default balance
        
        # Get funding rate for the symbol
        funding_rate = self.client.get_funding_rate(symbol)
        if funding_rate is None:
            logger.warning(f"⚠️ Could not fetch funding rate for {symbol}, proceeding without funding rate analysis")
            funding_rate = 0.0  # Default to neutral if unavailable
        
        if self.use_llm and self.strategy_engine:
            # Use LLM-based strategy
            try:
                # Get recent performance from database
                performance = self.db.get_recent_performance(limit=20)
                
                # Get LLM decision (it will include funding rate context)
                decision = self.strategy_engine.get_decision(
                    symbol=symbol,
                    klines=klines,
                    performance=performance,
                    balance=balance,
                    leverage=20,
                    funding_rate=funding_rate
                )
                
                # Apply funding rate adjustment to LLM decision
                llm_signal = {
                    "action": decision["action"],
                    "confidence": decision["confidence"],
                    "reason": decision["reasoning"]
                }
                
                adjusted_signal = self.funding_analyzer.adjust_signal_with_funding(llm_signal, funding_rate)
                
                return adjusted_signal
                
            except Exception as e:
                logger.error(f"LLM decision failed: {str(e)}, falling back to RSI/SMA")
                # Fall through to RSI/SMA logic
        
        # Fallback: Use traditional RSI/SMA indicators
        indicators = self.analyze_market(klines)
        
        if not indicators.get("valid"):
            return {
                "action": "HOLD",
                "confidence": 0.0,
                "reason": indicators.get("reason", "Invalid data")
            }
        
        rsi = indicators["rsi"]
        current_price = indicators["current_price"]
        sma_20 = indicators["sma_20"]
        sma_50 = indicators["sma_50"]
        volume_ratio = indicators["volume_ratio"]
        
        # Simple trading logic
        action = "HOLD"
        confidence = 0.5
        reason = "Neutral market conditions"
        
        # Oversold + uptrend = BUY
        if rsi < 30 and current_price > sma_20 and volume_ratio > 1.2:
            action = "BUY"
            confidence = 0.75
            reason = f"RSI oversold ({rsi:.1f}) with uptrend and strong volume"
        
        # Strong oversold = BUY
        elif rsi < 25:
            action = "BUY"
            confidence = 0.70
            reason = f"Strong oversold RSI ({rsi:.1f})"
        
        # Overbought + downtrend = SELL (if we have position)
        elif rsi > 70 and current_price < sma_20:
            action = "SELL"
            confidence = 0.70
            reason = f"RSI overbought ({rsi:.1f}) with downtrend"
        
        # Strong overbought = SELL
        elif rsi > 75:
            action = "SELL"
            confidence = SELL_SIGNAL_HIGH_CONFIDENCE  # Higher confidence for shorts (0.78)
            reason = f"Strong overbought RSI ({rsi:.1f}) - high confidence short"
        
        # Golden cross = BUY
        elif sma_20 > sma_50 and current_price > sma_20:
            action = "BUY"
            confidence = 0.60
            reason = "Golden cross with price above SMA20"
        
        # NEW: Calculate trend strength and block shorts in strong uptrends
        closes = [float(k[4]) for k in klines]
        sma_50_long = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1]
        sma_200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else sma_50_long
        
        # Block shorts in strong uptrends
        if action == "SELL":
            uptrend_strength = (sma_50_long - sma_200) / sma_200 if sma_200 > 0 else 0
            
            if uptrend_strength > STRONG_UPTREND_THRESHOLD:  # SMA50 is >2% above SMA200
                logger.info(f"🚫 Blocking SHORT: Strong uptrend detected (SMA50: {sma_50_long:.2f}, SMA200: {sma_200:.2f}, strength: {uptrend_strength:.2%})")
                action = "HOLD"
                confidence = 0.0
                reason = "Avoided counter-trend short in strong uptrend"
        
        # Create base technical signal
        technical_signal = {
            "action": action,
            "confidence": confidence,
            "reason": reason
        }
        
        # Adjust signal with funding rate analysis
        adjusted_signal = self.funding_analyzer.adjust_signal_with_funding(technical_signal, funding_rate)
        
        return adjusted_signal
    
    def generate_sentiment(self, indicators: Dict[str, Any]) -> str:
        """
        Generate AI Market Sentiment for heartbeat logging
        
        Args:
            indicators: Market indicators
            
        Returns:
            Sentiment string (e.g., "RSI is 50, Neutral stance")
        """
        if not indicators.get("valid"):
            return "No market data available"
        
        rsi = indicators["rsi"]
        current_price = indicators["current_price"]
        sma_20 = indicators["sma_20"]
        
        # Determine stance
        if rsi < 30:
            stance = "Bullish (Oversold)"
        elif rsi > 70:
            stance = "Bearish (Overbought)"
        elif current_price > sma_20:
            stance = "Bullish (Above MA)"
        elif current_price < sma_20:
            stance = "Bearish (Below MA)"
        else:
            stance = "Neutral"
        
        return f"RSI is {rsi:.1f}, {stance}, Price: ${current_price:.2f}"
    
    def check_tp_sl_all_symbols(self) -> None:
        """
        Alpha-Apex: Check multi-tier profit targets and dynamic stop loss for all open positions
        """
        for symbol in SYMBOL_LIST:
            try:
                # Get current price
                klines = self.client.get_market_klines(symbol, interval='1m', limit=1)
                
                if not klines or len(klines) == 0:
                    continue
                
                current_price = float(klines[-1][4])
                
                # NEW: Check hold duration for shorts (48-hour max hold)
                if self.client.has_open_position(symbol):
                    position = self.client.open_positions.get(symbol, {})
                    position_side = position.get('side', '').upper()
                    
                    if position_side == "SHORT" and symbol in self.short_entry_times:
                        entry_time = self.short_entry_times[symbol]
                        hold_duration_hours = (time.time() - entry_time) / 3600
                        
                        if hold_duration_hours > MAX_SHORT_HOLD_HOURS:  # 48-hour max hold
                            logger.info(f"⏰ Closing SHORT on {symbol}: Max hold time reached ({hold_duration_hours:.1f}h)")
                            success = self.client.close_position(symbol)
                            
                            if success:
                                # Clean up tracking
                                del self.short_entry_times[symbol]
                                
                                # Record exit
                                entry_price = float(position.get('entryPrice', current_price))
                                pnl_pct = -((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
                                self.db.record_trade_exit(symbol, current_price, pnl_pct)
                                
                                self.ai_logger.log_tp_sl_trigger(symbol, "MAX_HOLD_TIME", entry_price, current_price, pnl_pct)
                            continue
                
                # Check TP/SL (now returns PARTIAL_1, PARTIAL_2, SL, or None)
                trigger = self.client.check_tp_sl_triggers(symbol, current_price)
                
                if trigger:
                    position = self.client.open_positions.get(symbol, {})
                    entry_price = float(position.get('entryPrice', 0))
                    position_side = position.get('side', '').upper()
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
                    
                    # Handle Alpha-Apex partial profit taking
                    if trigger == "PARTIAL_1":
                        # First target: Take 50% profit, move SL to break-even
                        logger.info(f"🎯 Alpha-Apex: Taking 50% profit on {symbol} at +0.25%")
                        partial_result = self.client.close_partial_position(symbol, 0.5)
                        
                        if partial_result:
                            # Mark partial taken and set break-even SL
                            state = self.client.position_scaling_state[symbol]
                            state["partial_taken"] = True
                            state["breakeven_set"] = True
                            state["realized_profit"] = pnl_pct * 0.5  # 50% of position realized
                            
                            self.ai_logger.log_tp_sl_trigger(symbol, "PARTIAL_50%", entry_price, current_price, pnl_pct)
                            logger.info(f"✅ Break-even stop loss activated for {symbol}")
                    
                    elif trigger == "PARTIAL_2":
                        # Second target: Re-invest 10% of realized profit
                        state = self.client.position_scaling_state.get(symbol, {})
                        realized_profit_pct = state.get("realized_profit", 0)
                        
                        if realized_profit_pct > 0:
                            # Calculate re-investment size (10% of realized profit)
                            equity = self.get_current_equity()
                            realized_profit_value = equity * (realized_profit_pct / 100) * 0.5  # 50% of position
                            reinvest_value = realized_profit_value * 0.10  # 10% of realized profit
                            reinvest_size = reinvest_value / current_price
                            reinvest_size = self.client.round_qty(symbol, reinvest_size)
                            
                            # Check minimum order value before placing order
                            reinvest_value_usdt = reinvest_size * current_price
                            if reinvest_value_usdt < MIN_ORDER_VALUE_USDT:
                                logger.info(f"⚠️ Reinvest too small ({reinvest_value_usdt:.2f} USDT < {MIN_ORDER_VALUE_USDT}), skipping")
                                # Mark as done to prevent repeated attempts (no retry on small orders)
                                state["reinvested"] = True
                            elif reinvest_size > 0:
                                logger.info(f"📈 Alpha-Apex: Re-investing {reinvest_size} on {symbol} (House Money)")
                                side = "BUY" if position_side == "LONG" else "SELL"
                                reinvest_order = self.client.place_market_order(symbol, side, reinvest_size, check_spread=False)
                                
                                if reinvest_order:
                                    state["reinvested"] = True
                                    self.ai_logger.log_order_execution(
                                        symbol=symbol,
                                        side=side,
                                        size=reinvest_size,
                                        price=current_price,
                                        order_id=reinvest_order.get('orderId')
                                    )
                                    logger.info(f"✅ House Money re-investment successful for {symbol}")
                    
                    elif trigger == "SL":
                        # Stop loss hit
                        self.ai_logger.log_tp_sl_trigger(symbol, trigger, entry_price, current_price, pnl_pct)
                        self.db.record_trade_exit(symbol, current_price, pnl_pct)
                        
                        # Check for Auto-Flip (Trend Reversal)
                        # If stopped out at break-even and AI shows > 75% opposite confidence, flip
                        state = self.client.position_scaling_state.get(symbol, {})
                        is_breakeven = state.get("breakeven_set", False) and abs(pnl_pct) < 0.1
                        
                        # Close position
                        success = self.client.close_position(symbol)
                        
                        if success:
                            # NEW: Clean up short entry time tracking
                            if symbol in self.short_entry_times:
                                del self.short_entry_times[symbol]
                            
                            self.ai_logger.log_order_execution(
                                symbol=symbol,
                                side="CLOSE",
                                size=abs(float(position.get('size', 0))),
                                price=current_price,
                                order_id=None
                            )
                            
                            # Alpha-Apex Auto-Flip: Check for immediate reversal signal
                            if is_breakeven:
                                # Check cooldown to prevent whipsaw
                                current_time = time.time()
                                last_flip = self.last_flip_time.get(symbol, 0)
                                if current_time - last_flip < AUTO_FLIP_COOLDOWN_SECONDS:
                                    logger.info(f"⏱️ Auto-Flip cooldown active for {symbol} ({AUTO_FLIP_COOLDOWN_SECONDS - (current_time - last_flip):.0f}s remaining)")
                                else:
                                    logger.info(f"🔄 Alpha-Apex: Checking for Auto-Flip on {symbol} (stopped at break-even)")
                                    # Get fresh klines for signal
                                    flip_klines = self.client.get_market_klines(symbol, interval='1m', limit=100)
                                    if flip_klines:
                                        flip_signal = self.generate_signal(flip_klines, symbol)
                                        
                                        # Check for strong opposite signal
                                        opposite_action = "SELL" if position_side == "LONG" else "BUY"
                                        if flip_signal["action"] == opposite_action and flip_signal["confidence"] >= MIN_CONFIDENCE:
                                            logger.info(f"🎯 Alpha-Apex Auto-Flip: Entering {opposite_action} on {symbol} (Confidence: {flip_signal['confidence']:.2%})")
                                            
                                            # Calculate position size for flip
                                            flip_size = self.calculate_position_size(symbol, current_price, side=opposite_action)
                                            flip_order = self.client.place_market_order(symbol, opposite_action, flip_size, check_spread=True)
                                            
                                            if flip_order:
                                                # Record flip time
                                                self.last_flip_time[symbol] = current_time
                                                
                                                self.db.record_trade_entry(
                                                    symbol=symbol,
                                                    side=opposite_action,
                                                    price=current_price,
                                                    size=flip_size,
                                                    reasoning=f"Auto-Flip: {flip_signal['reason']}",
                                                    confidence=flip_signal["confidence"],
                                                    ai_reasoning=flip_signal["reason"],
                                                    behavioral_tag="AUTO_FLIP",
                                                    confidence_score=flip_signal["confidence"]
                                                )
                                                logger.info(f"✅ Auto-Flip executed successfully for {symbol}")
            
            except Exception as e:
                logger.error(f"Error checking TP/SL for {symbol}: {str(e)}")
    
    def process_symbol(self, symbol: str) -> None:
        """
        Process a single symbol (get data, analyze, trade)
        
        Args:
            symbol: Trading symbol to process
        """
        try:
            # Check kill switch first
            if self.check_kill_switch():
                logger.error("🚨 EMERGENCY_STOP mode active - no trading")
                return
            
            # 1. Get K-lines data
            klines = self.client.get_market_klines(symbol, interval='1m', limit=100)
            
            if not klines or len(klines) == 0:
                logger.debug(f"No data for {symbol}, skipping...")
                return
            
            # 2. Get current price for context
            current_price = float(klines[-1][4])
            
            # 3. Get behavioral tag
            behavioral_tag = self.get_behavioral_tag(klines)
            
            # 4. Generate signal (LLM or RSI/SMA)
            signal = self.generate_signal(klines, symbol)
            
            # Alpha-Apex: Volatility bypass check
            # If 5-minute price change > 0.5%, allow trade at confidence > 0.65
            volatility_bypass = False
            if len(klines) >= 5:
                price_5min_ago = float(klines[-5][4])
                price_change_5min_pct = abs((current_price - price_5min_ago) / price_5min_ago) * 100
                if price_change_5min_pct > VOLATILITY_BYPASS_THRESHOLD:
                    volatility_bypass = True
                    logger.info(f"⚡ Volatility bypass active for {symbol}: 5-min change {price_change_5min_pct:.2f}% > {VOLATILITY_BYPASS_THRESHOLD}%")
            
            # 5. Log decision with AI reasoning (for every scan, including HOLD)
            # First log with the new log_decision method for easy scannability
            self.ai_logger.log_decision(
                symbol=symbol,
                decision=signal["action"],
                confidence=signal["confidence"],
                reason=signal["reason"]
            )
            
            # Also log to the detailed trade decision log
            indicators = self.analyze_market(klines) if not self.use_llm else {"current_price": current_price}
            self.ai_logger.log_trade_decision(
                symbol=symbol,
                action=signal["action"],
                reason=signal["reason"],
                confidence=signal["confidence"],
                indicators=indicators
            )
            
            # Alpha-Apex: Determine effective confidence threshold
            confidence_threshold = VOLATILITY_BYPASS_CONFIDENCE if volatility_bypass else MIN_CONFIDENCE
            
            # 6. Execute trade if confidence is high enough
            # Alpha-Apex: Support both BUY (Long) and SELL (Short) with confidence >= threshold
            if signal["action"] == "BUY" and signal["confidence"] >= confidence_threshold:
                # Enhancement 9: Enhanced logging - Check if position already exists
                if self.client.has_open_position(symbol):
                    logger.info(f"🚫 Skipping {symbol}: Position already exists")
                    return
                
                # Critical Fix 2: Check global exposure limit BEFORE placing order
                current_exposure = self.calculate_total_exposure()
                new_position_pct = EQUITY_SIZING_PCT  # 10%
                if current_exposure + new_position_pct > GLOBAL_MAX_EXPOSURE_PCT:
                    logger.info(f"🛑 Skipping {symbol}: Max exposure reached ({current_exposure:.1f}% used, limit {GLOBAL_MAX_EXPOSURE_PCT}%)")
                    return
                
                # Enhancement 6: Check volume spike filter
                if not self.is_volume_spike(klines):
                    logger.info(f"🚫 Skipping {symbol}: Low volume (potential liquidity trap)")
                    return
                
                # Calculate position size dynamically
                position_size = self.calculate_position_size(symbol, current_price)
                
                # Place BUY order
                logger.info(f"🟢 BUY signal for {symbol}: {signal['reason'][:80]}... (Confidence: {signal['confidence']:.2%})")
                
                order = self.client.place_market_order(symbol, "BUY", position_size, check_spread=True)
                
                if order:
                    # Enhancement 3: Track pending order
                    order_id = order.get('orderId')
                    if order_id:
                        self.pending_orders[order_id] = {
                            "symbol": symbol,
                            "timestamp": time.time(),
                            "side": "BUY"
                        }
                    
                    # Enhancement 8: Track position open time
                    self.position_open_times[symbol] = time.time()
                    
                    # Record trade entry in database with new fields
                    self.db.record_trade_entry(
                        symbol=symbol,
                        side="BUY",
                        price=current_price,
                        size=position_size,
                        reasoning=signal["reason"],
                        confidence=signal["confidence"],
                        ai_reasoning=signal["reason"],
                        behavioral_tag=behavioral_tag,
                        confidence_score=signal["confidence"]
                    )
                    
                    self.ai_logger.log_order_execution(
                        symbol=symbol,
                        side="BUY",
                        size=position_size,
                        price=current_price,
                        order_id=order_id
                    )
            
            elif signal["action"] == "SELL" and signal["confidence"] >= confidence_threshold:
                # Alpha-Apex: Enable SHORTING (bi-directional trading)
                # If no position exists and confidence > threshold, open SHORT position
                # If LONG position exists, close it
                
                if not self.client.has_open_position(symbol):
                    # Alpha-Apex: Open SHORT position if confidence is high enough
                    logger.info(f"🔴 SHORT signal for {symbol}: {signal['reason'][:80]}... (Confidence: {signal['confidence']:.2%})")
                    
                    # Check global exposure limit
                    current_exposure = self.calculate_total_exposure()
                    new_position_pct = EQUITY_SIZING_PCT
                    if current_exposure + new_position_pct > GLOBAL_MAX_EXPOSURE_PCT:
                        logger.info(f"🛑 Skipping {symbol}: Max exposure reached ({current_exposure:.1f}% used, limit {GLOBAL_MAX_EXPOSURE_PCT}%)")
                        return
                    
                    # Check volume spike filter
                    if not self.is_volume_spike(klines):
                        logger.info(f"🚫 Skipping {symbol}: Low volume (potential liquidity trap)")
                        return
                    
                    # Calculate position size for SHORT
                    position_size = self.calculate_position_size(symbol, current_price, side="SELL")
                    
                    # Place SELL order to open SHORT
                    order = self.client.place_market_order(symbol, "SELL", position_size, check_spread=True)
                    
                    if order:
                        logger.info(f"✅ SHORT order placed successfully on {symbol}")
                        
                        # NEW: Verify position with brief wait
                        time.sleep(1.5)  # Give exchange time to update
                        
                        if self.client.has_open_position(symbol):
                            logger.info(f"✅ SHORT position confirmed on {symbol}")
                        else:
                            logger.warning(f"⚠️ SHORT order filled but position not visible yet on {symbol} (may appear next loop)")
                        
                        order_id = order.get('orderId')
                        if order_id:
                            self.pending_orders[order_id] = {
                                "symbol": symbol,
                                "timestamp": time.time(),
                                "side": "SELL"
                            }
                        
                        self.position_open_times[symbol] = time.time()
                        
                        # NEW: Track short entry time for max hold time
                        self.short_entry_times[symbol] = time.time()
                        
                        self.db.record_trade_entry(
                            symbol=symbol,
                            side="SELL",
                            price=current_price,
                            size=position_size,
                            reasoning=signal["reason"],
                            confidence=signal["confidence"],
                            ai_reasoning=signal["reason"],
                            behavioral_tag=behavioral_tag,
                            confidence_score=signal["confidence"]
                        )
                        
                        self.ai_logger.log_order_execution(
                            symbol=symbol,
                            side="SELL",
                            size=position_size,
                            price=current_price,
                            order_id=order_id
                        )
                else:
                    # Close existing LONG position
                    logger.info(f"🔴 SELL signal for {symbol}: Closing LONG position")
                    
                    position = self.client.open_positions.get(symbol, {})
                    entry_price = float(position.get('entryPrice', current_price))
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
                    
                    self.db.record_trade_exit(symbol, current_price, pnl_pct)
                    self.position_open_times.pop(symbol, None)
                    
                    success = self.client.close_position(symbol)
                    
                    if success:
                        position_size = abs(float(position.get('size', 0)))
                        self.ai_logger.log_order_execution(
                            symbol=symbol,
                            side="SELL",
                            size=position_size,
                            price=current_price,
                            order_id=None
                        )
            
            elif signal["action"] == "HOLD":
                # Enhancement 9: Enhanced logging - Low confidence
                if signal["confidence"] < confidence_threshold:
                    logger.debug(f"🚫 Skipping {symbol}: Confidence too low ({signal['confidence']:.1%} < {confidence_threshold:.0%})")
            
            # Enhancement 8: Check position timeout
            if symbol in self.position_open_times:
                time_open = time.time() - self.position_open_times[symbol]
                if time_open > 3600:  # 1 hour
                    logger.warning(f"⏰ {symbol} position held for {time_open/60:.1f}min (>1h) - TP/SL may not be working")
            
            # 7. Heartbeat logging (10-minute intervals) with enhanced data
            current_equity = self.get_current_equity()
            
            if self.use_llm and signal.get("reason"):
                # Use LLM reasoning as sentiment
                sentiment = f"AI: {signal['reason'][:150]}..."
            else:
                # Use traditional sentiment
                sentiment = self.generate_sentiment(indicators)
            
            self.ai_logger.log_heartbeat(
                market_data={
                    "symbol": symbol,
                    "price": current_price,
                    "action": signal["action"],
                    "confidence": signal["confidence"]
                },
                sentiment=sentiment,
                current_equity=current_equity,
                behavioral_state=behavioral_tag
            )
        
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")
            self.ai_logger.log_error(
                error_type="PROCESSING_ERROR",
                error_message=str(e),
                context={"symbol": symbol}
            )
    
    def run(self) -> None:
        """
        Main trading loop
        """
        self.running = True
        
        try:
            # Reset circuit breaker on startup to avoid persistent OPEN state
            if self.use_llm and self.strategy_engine:
                self.strategy_engine.reset_circuit_breaker()
                logger.info("✅ Circuit breaker reset on startup")
            
            # Initialize leverage
            self.initialize_leverage()
            
            logger.info("🚀 Starting main trading loop...")
            
            iteration = 0
            
            while self.running:
                # Enhancement 4: Check for emergency stop file
                if os.path.exists("EMERGENCY_STOP"):
                    logger.critical("🛑 EMERGENCY_STOP file detected - shutting down gracefully")
                    # Close all positions
                    for symbol in SYMBOL_LIST:
                        if self.client.has_open_position(symbol):
                            try:
                                self.client.close_position(symbol)
                                logger.info(f"✅ Closed {symbol} during emergency stop")
                            except Exception as e:
                                logger.error(f"Failed to close {symbol} during emergency: {e}")
                    break
                
                iteration += 1
                logger.info(f"\n{'=' * 60}")
                logger.info(f"📊 Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'=' * 60}")
                
                # Enhancement 3: Cancel stale orders
                self.cancel_stale_orders()
                
                # Check TP/SL for all positions
                self.check_tp_sl_all_symbols()
                
                # Process each symbol
                for symbol in SYMBOL_LIST:
                    logger.info(f"\n🔍 Processing {symbol}...")
                    self.process_symbol(symbol)
                    time.sleep(2)  # Small delay between symbols
                
                # Display log stats and database performance every 10 iterations
                if iteration % 10 == 0:
                    stats = self.ai_logger.get_log_stats()
                    performance = self.db.get_recent_performance(limit=10)
                    logger.info(f"\n📈 Log Stats: {stats}")
                    logger.info(f"💰 Performance: Win Rate={performance.get('win_rate', 0)*100:.1f}%, Total P&L={performance.get('total_pnl', 0):+.2f}%")
                
                # Wait before next iteration
                logger.info(f"\n⏸️ Waiting {MAIN_LOOP_INTERVAL}s before next iteration...\n")
                time.sleep(MAIN_LOOP_INTERVAL)
        
        except KeyboardInterrupt:
            logger.info("\n\n👋 Shutdown requested by user...")
        except Exception as e:
            logger.error(f"Fatal error in main loop: {str(e)}")
            self.ai_logger.log_error(
                error_type="FATAL_ERROR",
                error_message=str(e),
                context={}
            )
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """
        Gracefully shutdown the bot
        """
        logger.info("Shutting down bot...")
        self.running = False
        
        # Display final stats
        stats = self.ai_logger.get_log_stats()
        logger.info(f"📊 Final Log Stats: {stats}")
        
        # Display final performance
        performance = self.db.get_recent_performance(limit=50)
        logger.info(f"💰 Final Performance:")
        logger.info(f"   Total Trades: {performance.get('total_trades', 0)}")
        logger.info(f"   Win Rate: {performance.get('win_rate', 0)*100:.1f}%")
        logger.info(f"   Total P&L: {performance.get('total_pnl', 0):+.2f}%")
        
        # NEW: Display performance by direction (LONG vs SHORT)
        perf_by_dir = self.db.get_performance_by_direction()
        
        if "BUY" in perf_by_dir or "LONG" in perf_by_dir:
            # Handle both "BUY" and "LONG" naming
            long_stats = perf_by_dir.get("BUY") or perf_by_dir.get("LONG")
            if long_stats:
                logger.info(f"   📊 LONG Performance: {long_stats['win_rate']*100:.1f}% WR, {long_stats['avg_pnl']:+.2f}% avg, {long_stats['total_trades']} trades")
        
        if "SELL" in perf_by_dir or "SHORT" in perf_by_dir:
            # Handle both "SELL" and "SHORT" naming
            short_stats = perf_by_dir.get("SELL") or perf_by_dir.get("SHORT")
            if short_stats:
                logger.info(f"   📊 SHORT Performance: {short_stats['win_rate']*100:.1f}% WR, {short_stats['avg_pnl']:+.2f}% avg, {short_stats['total_trades']} trades")
        
        # Display LLM usage stats if available
        if self.use_llm and self.strategy_engine:
            llm_stats = self.strategy_engine.get_usage_stats()
            logger.info(f"🤖 LLM Usage:")
            logger.info(f"   Total Calls: {llm_stats['total_calls']}")
            logger.info(f"   Total Cost: ${llm_stats['total_cost_usd']:.4f}")
            logger.info(f"   Avg Cost/Call: ${llm_stats['avg_cost_per_call']:.4f}")
        
        # Close database connection
        self.db.close()
        
        logger.info("✅ Shutdown complete")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Get system health status for monitoring
        
        Returns:
            Dictionary with health metrics
        """
        import os
        from pathlib import Path
        
        health = {
            "timestamp": datetime.now().isoformat(),
            "bot_running": self.running,
            "llm_enabled": self.use_llm,
        }
        
        # Database health
        try:
            db_path = Path("trading_memory.db")
            health["database_available"] = db_path.exists()
            health["database_size_mb"] = db_path.stat().st_size / 1e6 if db_path.exists() else 0
            
            # Recent performance
            performance = self.db.get_recent_performance(limit=10)
            health["recent_trades"] = performance.get("total_trades", 0)
            health["win_rate"] = performance.get("win_rate", 0.0)
            health["total_pnl"] = performance.get("total_pnl", 0.0)
        except Exception as e:
            health["database_error"] = str(e)
        
        # LLM health
        if self.use_llm and self.strategy_engine:
            try:
                llm_stats = self.strategy_engine.get_usage_stats()
                health["llm_provider"] = llm_stats["provider"]
                health["llm_total_calls"] = llm_stats["total_calls"]
                health["llm_total_cost_usd"] = llm_stats["total_cost_usd"]
                health["llm_circuit_breaker_state"] = llm_stats["circuit_breaker_state"]
            except Exception as e:
                health["llm_error"] = str(e)
        
        # Log file health
        try:
            log_path = Path("ai_trading.log")
            health["log_file_exists"] = log_path.exists()
            health["log_file_size_mb"] = log_path.stat().st_size / 1e6 if log_path.exists() else 0
        except Exception as e:
            health["log_error"] = str(e)
        
        return health


def main():
    """Main entry point"""
    try:
        bot = CompetitionTradingBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise


if __name__ == "__main__":
    main()
