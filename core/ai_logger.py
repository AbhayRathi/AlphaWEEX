"""
Enhanced AI Trading Logger
Requirements:
- Single-line JSON format
- 10-minute heartbeat logging
- Market sentiment tracking
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AITradingLogger:
    """
    Enhanced AI Trading Logger with JSON format and heartbeat
    
    Features:
    - Single-line JSON entries
    - 10-minute heartbeat (600 seconds)
    - Market sentiment logging
    - Trade decision tracking
    """
    
    def __init__(self, log_file: str = "ai_trading.log"):
        """
        Initialize AI Trading Logger
        
        Args:
            log_file: Path to log file (default: ai_trading.log)
        """
        self.log_file = log_file
        self.last_heartbeat_time = time.time()
        self.heartbeat_interval = 600  # 10 minutes in seconds
        self.max_log_size = 50 * 1024 * 1024  # 50MB
        
        # Ensure log file exists
        Path(self.log_file).touch(exist_ok=True)
        
        # Check and rotate if needed on init
        self._check_and_rotate_log()
        
        logger.info(f"✅ AI Trading Logger initialized: {self.log_file}")
    
    def _write_json_log(self, log_data: Dict[str, Any]) -> None:
        """
        Write a single-line JSON log entry
        
        Args:
            log_data: Dictionary containing log data
        """
        try:
            # Check and rotate if needed before writing
            self._check_and_rotate_log()
            
            # Add timestamp if not present
            if 'timestamp' not in log_data:
                log_data['timestamp'] = datetime.now().isoformat()
            
            # Write as single-line JSON
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_data) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write AI log: {str(e)}")
    
    def _check_and_rotate_log(self) -> None:
        """
        Check log file size and rotate if necessary
        If log file exceeds 50MB, rename to .old and start fresh
        """
        try:
            log_path = Path(self.log_file)
            if log_path.exists() and log_path.stat().st_size > self.max_log_size:
                old_log = f"{self.log_file}.old"
                
                # Remove old backup if exists
                if Path(old_log).exists():
                    Path(old_log).unlink()
                
                # Rename current log to .old
                log_path.rename(old_log)
                
                logger.info(f"📦 Log rotated: {self.log_file} -> {old_log} (size: {log_path.stat().st_size / 1024 / 1024:.1f}MB)")
                
                # Create new log file
                log_path.touch()
        except Exception as e:
            logger.error(f"Failed to rotate log: {str(e)}")
    
    def log_heartbeat(self, market_data: Dict[str, Any], sentiment: str,
                     current_equity: Optional[float] = None,
                     behavioral_state: Optional[str] = None) -> bool:
        """
        Log 10-minute heartbeat with AI Market Sentiment
        
        Args:
            market_data: Current market data (price, RSI, etc.)
            sentiment: AI sentiment analysis (e.g., "RSI is 50, Neutral stance")
            current_equity: Current total equity in USDT
            behavioral_state: Predominant market psychology detected
            
        Returns:
            True if heartbeat was logged, False if skipped
        """
        current_time = time.time()
        
        # Check if heartbeat is due
        if current_time - self.last_heartbeat_time < self.heartbeat_interval:
            return False  # Not time for heartbeat yet
        
        log_entry = {
            "type": "HEARTBEAT",
            "timestamp": datetime.now().isoformat(),
            "market_sentiment": sentiment,
            "current_equity": current_equity,
            "behavioral_state": behavioral_state or "UNKNOWN",
            "market_data": market_data,
            "interval_seconds": self.heartbeat_interval
        }
        
        self._write_json_log(log_entry)
        self.last_heartbeat_time = current_time
        
        logger.info(f"💓 HEARTBEAT: {sentiment} | Equity: ${current_equity:.2f} | Psychology: {behavioral_state}")
        return True
    
    def log_trade_decision(self, symbol: str, action: str, reason: str, 
                          confidence: float, indicators: Dict[str, Any]) -> None:
        """
        Log a trading decision
        
        Args:
            symbol: Trading symbol
            action: Trade action (BUY, SELL, HOLD)
            reason: Reason for decision
            confidence: Confidence level (0.0 to 1.0)
            indicators: Technical indicators used
        """
        log_entry = {
            "type": "TRADE_DECISION",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "action": action,
            "reason": reason,
            "confidence": confidence,
            "indicators": indicators
        }
        
        self._write_json_log(log_entry)
        logger.info(f"📊 Decision: {action} {symbol} (Confidence: {confidence:.2%})")
    
    def log_order_execution(self, symbol: str, side: str, size: float, 
                           price: Optional[float] = None, order_id: Optional[str] = None) -> None:
        """
        Log order execution
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            size: Order size
            price: Execution price (if known)
            order_id: Order ID (if available)
        """
        log_entry = {
            "type": "ORDER_EXECUTION",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price,
            "order_id": order_id
        }
        
        self._write_json_log(log_entry)
        logger.info(f"✅ Order Executed: {side} {size} {symbol} @ {price}")
    
    def log_tp_sl_trigger(self, symbol: str, trigger_type: str, entry_price: float, 
                         exit_price: float, pnl_pct: float) -> None:
        """
        Log TP/SL trigger
        
        Args:
            symbol: Trading symbol
            trigger_type: "TP" or "SL"
            entry_price: Position entry price
            exit_price: Exit price
            pnl_pct: P&L percentage
        """
        log_entry = {
            "type": f"{trigger_type}_TRIGGER",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "trigger": trigger_type,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl_pct": pnl_pct
        }
        
        self._write_json_log(log_entry)
        
        emoji = "🎯" if trigger_type == "TP" else "🛑"
        logger.info(f"{emoji} {trigger_type} Triggered: {symbol} P&L: {pnl_pct:+.2f}%")
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict] = None) -> None:
        """
        Log an error event
        
        Args:
            error_type: Type of error (e.g., "521_ERROR", "API_ERROR")
            error_message: Error message
            context: Additional context data
        """
        log_entry = {
            "type": "ERROR",
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self._write_json_log(log_entry)
        logger.error(f"❌ Error: {error_type} - {error_message}")
    
    def log_cooldown(self, cooldown_type: str, duration_seconds: int, reason: str) -> None:
        """
        Log a cooldown period
        
        Args:
            cooldown_type: Type of cooldown (e.g., "521_FIREWALL")
            duration_seconds: Cooldown duration
            reason: Reason for cooldown
        """
        log_entry = {
            "type": "COOLDOWN",
            "timestamp": datetime.now().isoformat(),
            "cooldown_type": cooldown_type,
            "duration_seconds": duration_seconds,
            "reason": reason
        }
        
        self._write_json_log(log_entry)
        logger.warning(f"⏸️ Cooldown: {cooldown_type} for {duration_seconds}s - {reason}")
    
    def log_leverage_set(self, symbol: str, leverage: int, success: bool) -> None:
        """
        Log leverage configuration
        
        Args:
            symbol: Trading symbol
            leverage: Leverage value
            success: Whether operation succeeded
        """
        log_entry = {
            "type": "LEVERAGE_SET",
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "leverage": leverage,
            "success": success
        }
        
        self._write_json_log(log_entry)
        
        if success:
            logger.info(f"⚙️ Leverage set: {symbol} @ {leverage}x")
        else:
            logger.error(f"❌ Failed to set leverage: {symbol} @ {leverage}x")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged events
        
        Returns:
            Dictionary with log statistics
        """
        try:
            stats = {
                "total_lines": 0,
                "heartbeats": 0,
                "trade_decisions": 0,
                "order_executions": 0,
                "tp_triggers": 0,
                "sl_triggers": 0,
                "errors": 0
            }
            
            # Use streaming to handle large files efficiently
            with open(self.log_file, 'r') as f:
                for line in f:
                    stats["total_lines"] += 1
                    try:
                        entry = json.loads(line.strip())
                        entry_type = entry.get("type", "")
                        
                        if entry_type == "HEARTBEAT":
                            stats["heartbeats"] += 1
                        elif entry_type == "TRADE_DECISION":
                            stats["trade_decisions"] += 1
                        elif entry_type == "ORDER_EXECUTION":
                            stats["order_executions"] += 1
                        elif entry_type == "TP_TRIGGER":
                            stats["tp_triggers"] += 1
                        elif entry_type == "SL_TRIGGER":
                            stats["sl_triggers"] += 1
                        elif entry_type == "ERROR":
                            stats["errors"] += 1
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
            
            return stats
            
        except FileNotFoundError:
            logger.warning(f"Log file not found: {self.log_file}")
            return {
                "total_lines": 0,
                "heartbeats": 0,
                "trade_decisions": 0,
                "order_executions": 0,
                "tp_triggers": 0,
                "sl_triggers": 0,
                "errors": 0
            }
        except Exception as e:
            logger.error(f"Failed to get log stats: {str(e)}")
            return {}
    
    def force_heartbeat(self, market_data: Dict[str, Any], sentiment: str,
                       current_equity: Optional[float] = None,
                       behavioral_state: Optional[str] = None) -> None:
        """
        Force a heartbeat log immediately (bypass interval check)
        
        Args:
            market_data: Current market data
            sentiment: AI sentiment analysis
            current_equity: Current total equity in USDT
            behavioral_state: Predominant market psychology detected
        """
        log_entry = {
            "type": "HEARTBEAT",
            "timestamp": datetime.now().isoformat(),
            "market_sentiment": sentiment,
            "current_equity": current_equity,
            "behavioral_state": behavioral_state or "UNKNOWN",
            "market_data": market_data,
            "forced": True
        }
        
        self._write_json_log(log_entry)
        logger.info(f"💓 FORCED HEARTBEAT: {sentiment} | Equity: ${current_equity:.2f} | Psychology: {behavioral_state}")
