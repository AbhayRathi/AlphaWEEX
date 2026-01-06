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
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # 'openai', 'anthropic', or 'deepseek'
LLM_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')  # Optional: override default model
LLM_BASE_URL = os.getenv('LLM_BASE_URL')  # For DeepSeek: https://api.deepseek.com

# Multi-Symbol Support
SYMBOL_LIST = ["cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt"]

# Risk Management
TAKE_PROFIT_PCT = 2.0  # 2% TP
STOP_LOSS_PCT = 1.0    # 1% SL
EQUITY_SIZING_PCT = 10.0  # 10% of equity per trade
KILL_SWITCH_PCT = 10.0  # Kill switch if equity drops >10% in 24h

# Trading Parameters
POSITION_SIZE = 0.001  # Default position size (adjust based on capital)
MAIN_LOOP_INTERVAL = 30  # Check every 30 seconds


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
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize the trading bot
        
        Args:
            use_llm: If True, use LLM strategy. If False, fallback to RSI/SMA (default: True)
        """
        # Validate API credentials
        if not API_KEY or not API_SECRET or not API_PASSWORD:
            raise ValueError("Missing API credentials. Please set API_KEY, API_SECRET, and API_PASSWORD in .env")
        
        # Initialize WEEX v2 client
        self.client = WEEXv2Client(API_KEY, API_SECRET, API_PASSWORD)
        
        # Initialize AI logger
        self.ai_logger = AITradingLogger("ai_trading.log")
        
        # Initialize database manager
        self.db = DatabaseManager("trading_memory.db")
        
        # Initialize strategy engine (LLM or fallback)
        self.use_llm = use_llm
        self.strategy_engine = None
        self.behavioral_adversary = None
        
        if use_llm:
            if not LLM_API_KEY:
                logger.warning("⚠️ No LLM API key found. Falling back to RSI/SMA strategy.")
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
                    
                    # Initialize StrategyEngine with behavioral adversary
                    self.strategy_engine = StrategyEngine(
                        provider=LLM_PROVIDER,
                        api_key=LLM_API_KEY,
                        model=LLM_MODEL,
                        base_url=LLM_BASE_URL,
                        behavioral_adversary=self.behavioral_adversary
                    )
                    logger.info(f"✅ LLM Strategy Engine enabled: {LLM_PROVIDER}")
                except Exception as e:
                    logger.error(f"Failed to initialize LLM: {str(e)}")
                    logger.warning("⚠️ Falling back to RSI/SMA strategy")
                    self.use_llm = False
        
        # Kill Switch state
        self.emergency_stop = False
        self.initial_equity = None
        self.equity_history = []  # Track equity over time
        
        # Running flag
        self.running = False
        
        logger.info("=" * 60)
        logger.info("🚀 WEEX AI TRADING BOT - COMPETITION READY")
        logger.info("=" * 60)
        logger.info(f"📊 Multi-Symbol Support: {', '.join(SYMBOL_LIST)}")
        logger.info(f"🎯 Risk Management: TP={TAKE_PROFIT_PCT}%, SL={STOP_LOSS_PCT}%")
        logger.info(f"💰 Equity Sizing: {EQUITY_SIZING_PCT}% per trade")
        logger.info(f"🛑 Kill Switch: {KILL_SWITCH_PCT}% drawdown limit")
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
    
    def calculate_position_size(self, symbol: str, current_price: float, leverage: int = 20) -> float:
        """
        Calculate position size using 10% equity sizing
        Formula: qty = (Account_Balance * 0.10 * Leverage) / Current_Price
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            leverage: Trading leverage
            
        Returns:
            Position size rounded to correct precision
        """
        try:
            equity = self.get_current_equity()
            
            # Calculate position size
            qty = (equity * (EQUITY_SIZING_PCT / 100.0) * leverage) / current_price
            
            # Round to correct precision
            qty = self.client.round_qty(symbol, qty)
            
            logger.info(f"💰 Position size for {symbol}: {qty} (Equity: ${equity:.2f}, Price: ${current_price:.2f})")
            return qty
            
        except Exception as e:
            logger.error(f"Failed to calculate position size: {str(e)}")
            return POSITION_SIZE  # Fallback to default
    
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
                'rsi': self.calculate_rsi([float(k[4]) for k in klines]),
                'volume': float(klines[-1][5]) if len(klines[-1]) > 5 else 0.0,
                'price_change_pct': ((float(klines[-1][4]) - float(klines[0][4])) / float(klines[0][4]) * 100) if len(klines) > 1 else 0.0
            }
            
            psychology = self.behavioral_adversary.analyze_psychology(market_data)
            return psychology.get('detected_archetype', 'NEUTRAL')
            
        except Exception as e:
            logger.warning(f"Failed to get behavioral tag: {str(e)}")
            return "NEUTRAL"
    
    def calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """
        Calculate RSI indicator
        
        Args:
            closes: List of closing prices
            period: RSI period (default: 14)
            
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
        
        # Calculate indicators
        rsi = self.calculate_rsi(closes)
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
        Generate trading signal using LLM or fallback to RSI/SMA
        
        Args:
            klines: K-lines data
            symbol: Trading symbol
            
        Returns:
            Signal dictionary with action, confidence, and reasoning
        """
        # Get account balance (for LLM context)
        # In a real implementation, fetch this from the API
        balance = 1000.0  # Default balance
        
        if self.use_llm and self.strategy_engine:
            # Use LLM-based strategy
            try:
                # Get recent performance from database
                performance = self.db.get_recent_performance(limit=20)
                
                # Get LLM decision
                decision = self.strategy_engine.get_decision(
                    symbol=symbol,
                    klines=klines,
                    performance=performance,
                    balance=balance,
                    leverage=20
                )
                
                return {
                    "action": decision["action"],
                    "confidence": decision["confidence"],
                    "reason": decision["reasoning"]
                }
                
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
            confidence = 0.65
            reason = f"Strong overbought RSI ({rsi:.1f})"
        
        # Golden cross = BUY
        elif sma_20 > sma_50 and current_price > sma_20:
            action = "BUY"
            confidence = 0.60
            reason = "Golden cross with price above SMA20"
        
        return {
            "action": action,
            "confidence": confidence,
            "reason": reason
        }
    
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
        Check TP/SL triggers for all open positions
        """
        for symbol in SYMBOL_LIST:
            try:
                # Get current price
                klines = self.client.get_market_klines(symbol, interval='1m', limit=1)
                
                if not klines or len(klines) == 0:
                    continue
                
                current_price = float(klines[-1][4])
                
                # Check TP/SL
                trigger = self.client.check_tp_sl_triggers(symbol, current_price)
                
                if trigger:
                    # Get position details for logging
                    position = self.client.open_positions.get(symbol, {})
                    entry_price = float(position.get('entryPrice', 0))
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
                    
                    # Log trigger
                    self.ai_logger.log_tp_sl_trigger(symbol, trigger, entry_price, current_price, pnl_pct)
                    
                    # Record trade exit in database
                    self.db.record_trade_exit(symbol, current_price, pnl_pct)
                    
                    # Close position
                    success = self.client.close_position(symbol)
                    
                    if success:
                        self.ai_logger.log_order_execution(
                            symbol=symbol,
                            side="CLOSE",
                            size=abs(float(position.get('size', 0))),
                            price=current_price,
                            order_id=None
                        )
            
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
            
            # 5. Log decision with AI reasoning
            indicators = self.analyze_market(klines) if not self.use_llm else {"current_price": current_price}
            self.ai_logger.log_trade_decision(
                symbol=symbol,
                action=signal["action"],
                reason=signal["reason"],
                confidence=signal["confidence"],
                indicators=indicators
            )
            
            # 6. Execute trade if confidence is high enough
            if signal["action"] == "BUY" and signal["confidence"] >= 0.65:
                # Safety Guardrail: Check if position already exists
                if self.client.has_open_position(symbol):
                    logger.info(f"⚠️ Position already exists for {symbol}, skipping BUY")
                    return
                
                # Calculate position size dynamically
                position_size = self.calculate_position_size(symbol, current_price)
                
                # Place BUY order
                logger.info(f"🟢 BUY signal for {symbol}: {signal['reason'][:80]}... (Confidence: {signal['confidence']:.2%})")
                
                order = self.client.place_market_order(symbol, "BUY", position_size, check_spread=True)
                
                if order:
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
                        order_id=order.get('orderId')
                    )
            
            elif signal["action"] == "SELL" and signal["confidence"] >= 0.65:
                # Only SELL if we have a position
                if not self.client.has_open_position(symbol):
                    logger.debug(f"No position to sell for {symbol}")
                    return
                
                logger.info(f"🔴 SELL signal for {symbol}: {signal['reason'][:80]}... (Confidence: {signal['confidence']:.2%})")
                
                # Get position details for P&L calculation
                position = self.client.open_positions.get(symbol, {})
                entry_price = float(position.get('entryPrice', current_price))
                pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
                
                # Record trade exit in database
                self.db.record_trade_exit(symbol, current_price, pnl_pct)
                
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
            # Initialize leverage
            self.initialize_leverage()
            
            logger.info("🚀 Starting main trading loop...")
            
            iteration = 0
            
            while self.running:
                iteration += 1
                logger.info(f"\n{'=' * 60}")
                logger.info(f"📊 Iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'=' * 60}")
                
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
