"""
WEEX AI Trading Bot - Competition-Ready Implementation with LLM Brain

Requirements:
1. Working Auth - WEEX v2 API with proper signature
2. Multi-Symbol Flexibility - Loop through multiple symbols
3. Data Retrieval - K-lines from /capi/v2/market/candles
4. Risk Management - 2% TP, 1% SL
5. Enhanced AI Logging - JSON format with 10-min heartbeat
6. Safety Guardrails - 20x leverage, position check, 521 cooldown
7. LLM-Based Strategy - Autonomous AI decision making
8. Persistent Memory - SQLite database for learning
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
from core.strategy_engine import LLMStrategy

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

# Multi-Symbol Support
SYMBOL_LIST = ["cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt"]

# Risk Management
TAKE_PROFIT_PCT = 2.0  # 2% TP
STOP_LOSS_PCT = 1.0    # 1% SL

# Trading Parameters
POSITION_SIZE = 0.001  # Default position size (adjust based on capital)
MAIN_LOOP_INTERVAL = 30  # Check every 30 seconds

# LLM Strategy Toggle (set to False to use traditional indicators)
USE_LLM_STRATEGY = os.getenv('USE_LLM_STRATEGY', 'true').lower() == 'true'


class CompetitionTradingBot:
    """
    Competition-Ready WEEX AI Trading Bot with LLM Brain
    
    Features:
    - Multi-symbol trading
    - LLM-based decision engine with fallback to indicators
    - Persistent memory with SQLite
    - TP/SL risk management
    - Enhanced AI logging
    - Safety guardrails
    """
    
    def __init__(self):
        """Initialize the trading bot"""
        # Validate API credentials
        if not API_KEY or not API_SECRET or not API_PASSWORD:
            raise ValueError("Missing API credentials. Please set API_KEY, API_SECRET, and API_PASSWORD in .env")
        
        # Initialize WEEX v2 client
        self.client = WEEXv2Client(API_KEY, API_SECRET, API_PASSWORD)
        
        # Initialize AI logger
        self.ai_logger = AITradingLogger("ai_trading.log")
        
        # Initialize database for persistent memory
        self.db = DatabaseManager("data/trading_memory.db")
        
        # Initialize LLM strategy (if enabled)
        self.use_llm = USE_LLM_STRATEGY
        if self.use_llm:
            try:
                self.llm_strategy = LLMStrategy()
                logger.info("🧠 LLM Strategy enabled")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize LLM strategy: {e}")
                logger.warning("⚠️ Falling back to indicator-based strategy")
                self.use_llm = False
                self.llm_strategy = None
        else:
            self.llm_strategy = None
            logger.info("📊 Using traditional indicator-based strategy")
        
        # Running flag
        self.running = False
        
        logger.info("=" * 60)
        logger.info("🚀 WEEX AI TRADING BOT - COMPETITION READY")
        logger.info("=" * 60)
        logger.info(f"📊 Multi-Symbol Support: {', '.join(SYMBOL_LIST)}")
        logger.info(f"🎯 Risk Management: TP={TAKE_PROFIT_PCT}%, SL={STOP_LOSS_PCT}%")
        logger.info(f"🧠 Strategy: {'LLM-Based' if self.use_llm else 'Indicator-Based'}")
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
    
    def generate_signal(self, klines: List[List], symbol: str, 
                       indicators: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate trading signal using LLM or fallback to indicators
        
        Args:
            klines: K-lines data
            symbol: Trading symbol
            indicators: Market indicators (optional, for fallback)
            
        Returns:
            Signal dictionary with action, confidence, and reason
        """
        # Try LLM strategy first if enabled
        if self.use_llm and self.llm_strategy:
            try:
                # Get recent performance from database
                past_trades = self.db.get_recent_performance(limit=5)
                
                # Generate signal using LLM
                signal = self.llm_strategy.generate_signal(symbol, klines, past_trades)
                
                # Normalize confidence to 0-1 range for backward compatibility
                if signal.get('confidence', 0) > 1:
                    signal['confidence_pct'] = signal['confidence']
                    signal['confidence'] = signal['confidence'] / 100.0
                else:
                    signal['confidence_pct'] = signal['confidence'] * 100
                
                return signal
                
            except Exception as e:
                logger.warning(f"⚠️ LLM strategy failed for {symbol}: {e}")
                logger.info(f"ℹ️ Falling back to indicator-based strategy")
        
        # Fallback to indicator-based strategy
        if not indicators or not indicators.get("valid"):
            return {
                "action": "HOLD",
                "confidence": 0.0,
                "confidence_pct": 0.0,
                "reason": "Invalid data",
                "executable": False
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
        
        confidence_pct = confidence * 100
        executable = (action in ['BUY', 'SELL']) and (confidence >= 0.65)
        
        return {
            "action": action,
            "confidence": confidence,
            "confidence_pct": confidence_pct,
            "reason": reason,
            "executable": executable
        }
    
    def generate_sentiment(self, klines: List[List], 
                          indicators: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate AI Market Sentiment for heartbeat logging
        
        Args:
            klines: K-lines data
            indicators: Market indicators (optional)
            
        Returns:
            Sentiment string (e.g., "RSI is 50, Neutral stance")
        """
        # Try LLM sentiment if enabled
        if self.use_llm and self.llm_strategy:
            try:
                past_trades = self.db.get_recent_performance(limit=5)
                sentiment = self.llm_strategy.get_market_sentiment(klines, past_trades)
                return sentiment
            except Exception as e:
                logger.warning(f"⚠️ LLM sentiment failed: {e}")
        
        # Fallback to indicator-based sentiment
        if not indicators or not indicators.get("valid"):
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
                    
                    # Record in database
                    self.db.record_trade(
                        symbol=symbol,
                        side="CLOSE",
                        price=current_price,
                        pnl=pnl_pct,
                        reasoning=f"{trigger} triggered at {pnl_pct:+.2f}%",
                        confidence=100.0  # TP/SL are automatic
                    )
                    
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
            # 1. Get K-lines data
            klines = self.client.get_market_klines(symbol, interval='1m', limit=100)
            
            if not klines or len(klines) == 0:
                logger.debug(f"No data for {symbol}, skipping...")
                return
            
            # 2. Analyze market (for fallback strategy)
            indicators = self.analyze_market(klines)
            
            if not indicators.get("valid"):
                logger.debug(f"Invalid indicators for {symbol}: {indicators.get('reason')}")
                return
            
            # 3. Generate signal (uses LLM if enabled, otherwise indicators)
            signal = self.generate_signal(klines, symbol, indicators)
            
            # 4. Log decision
            confidence = signal.get("confidence_pct", signal.get("confidence", 0))
            self.ai_logger.log_trade_decision(
                symbol=symbol,
                action=signal["action"],
                reason=signal["reason"],
                confidence=confidence,
                indicators=indicators
            )
            
            # 5. Execute trade if signal is executable
            executable = signal.get("executable", False)
            if not executable and signal["action"] in ["BUY", "SELL"]:
                # Check using old threshold for backward compatibility
                conf_value = signal.get("confidence", 0)
                if conf_value <= 1.0:
                    executable = conf_value >= 0.65
                else:
                    executable = conf_value >= 65
            
            if signal["action"] == "BUY" and executable:
                # Safety Guardrail: Check if position already exists
                if self.client.has_open_position(symbol):
                    logger.info(f"⚠️ Position already exists for {symbol}, skipping BUY")
                    return
                
                # Place BUY order
                conf_display = signal.get("confidence_pct", signal.get("confidence") * 100)
                logger.info(f"🟢 BUY signal for {symbol}: {signal['reason']} (Confidence: {conf_display:.1f}%)")
                
                order = self.client.place_market_order(symbol, "BUY", POSITION_SIZE)
                
                if order:
                    self.ai_logger.log_order_execution(
                        symbol=symbol,
                        side="BUY",
                        size=POSITION_SIZE,
                        price=indicators["current_price"],
                        order_id=order.get('orderId'),
                        ai_reasoning=signal["reason"],
                        confidence=confidence
                    )
                    
                    # Record in database
                    self.db.record_trade(
                        symbol=symbol,
                        side="BUY",
                        price=indicators["current_price"],
                        pnl=0.0,  # PnL calculated on close
                        reasoning=signal["reason"],
                        confidence=confidence
                    )
            
            elif signal["action"] == "SELL" and executable:
                # Only SELL if we have a position
                if not self.client.has_open_position(symbol):
                    logger.debug(f"No position to sell for {symbol}")
                    return
                
                conf_display = signal.get("confidence_pct", signal.get("confidence") * 100)
                logger.info(f"🔴 SELL signal for {symbol}: {signal['reason']} (Confidence: {conf_display:.1f}%)")
                
                # Get position for PnL calculation
                position = self.client.open_positions.get(symbol, {})
                entry_price = float(position.get('entryPrice', 0))
                current_price = indicators["current_price"]
                pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0
                
                success = self.client.close_position(symbol)
                
                if success:
                    self.ai_logger.log_order_execution(
                        symbol=symbol,
                        side="SELL",
                        size=POSITION_SIZE,
                        price=current_price,
                        order_id=None,
                        ai_reasoning=signal["reason"],
                        confidence=confidence
                    )
                    
                    # Record in database
                    self.db.record_trade(
                        symbol=symbol,
                        side="SELL",
                        price=current_price,
                        pnl=pnl_pct,
                        reasoning=signal["reason"],
                        confidence=confidence
                    )
            
            # 6. Heartbeat logging (10-minute intervals)
            sentiment = self.generate_sentiment(klines, indicators)
            self.ai_logger.log_heartbeat(
                market_data={
                    "symbol": symbol,
                    "price": indicators["current_price"],
                    "rsi": indicators["rsi"],
                    "sma_20": indicators["sma_20"]
                },
                sentiment=sentiment
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
                
                # Display log stats every 10 iterations
                if iteration % 10 == 0:
                    stats = self.ai_logger.get_log_stats()
                    logger.info(f"\n📈 Log Stats: {stats}")
                
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
        logger.info(f"📊 Final Stats: {stats}")
        
        logger.info("✅ Shutdown complete")


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
