"""
Trade Journal - Persistent JSON-based trade history for AI context.

Provides a lightweight JSON journal for storing trade outcomes that can be
read by the LLM for decision-making context.
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)


class TradeJournal:
    """
    JSON-based trade journal for persistent trade history.
    
    Features:
    - Append-only journal for trade outcomes
    - Thread-safe writes
    - Efficient reading of recent trades
    - Automatic file creation
    """
    
    def __init__(self, journal_path: str = "data/trade_history.json"):
        """
        Initialize Trade Journal
        
        Args:
            journal_path: Path to the JSON journal file
        """
        self.journal_path = journal_path
        self.lock = Lock()
        self._ensure_journal_exists()
        logger.info(f"✅ TradeJournal initialized: {self.journal_path}")
    
    def _ensure_journal_exists(self) -> None:
        """Create journal file and directory if they don't exist"""
        try:
            # Create directory if needed
            journal_dir = os.path.dirname(self.journal_path)
            if journal_dir:
                os.makedirs(journal_dir, exist_ok=True)
            
            # Create empty journal file if it doesn't exist
            if not os.path.exists(self.journal_path):
                with open(self.journal_path, 'w') as f:
                    json.dump([], f)
                logger.info(f"📝 Created new trade journal: {self.journal_path}")
        except Exception as e:
            logger.error(f"Failed to create journal: {str(e)}")
            raise
    
    def append_trade(self, symbol: str, direction: str, profit_loss: float,
                    ai_reason: str, timestamp: Optional[str] = None,
                    entry_price: Optional[float] = None,
                    exit_price: Optional[float] = None,
                    trigger_type: Optional[str] = None) -> bool:
        """
        Append a closed trade to the journal
        
        Args:
            symbol: Trading symbol (e.g., "cmt_btcusdt")
            direction: Trade direction ("LONG" or "SHORT")
            profit_loss: Profit/Loss percentage
            ai_reason: AI reasoning for the trade
            timestamp: ISO timestamp (optional, defaults to now)
            entry_price: Entry price (optional)
            exit_price: Exit price (optional)
            trigger_type: Type of exit ("SL", "TP", "PARTIAL_1", "PARTIAL_2", etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            trade_entry = {
                "timestamp": timestamp,
                "symbol": symbol,
                "direction": direction.upper(),
                "profit_loss": round(profit_loss, 4),
                "ai_reason": ai_reason,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "trigger_type": trigger_type
            }
            
            with self.lock:
                # Read existing trades
                try:
                    with open(self.journal_path, 'r') as f:
                        trades = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    trades = []
                
                # Append new trade
                trades.append(trade_entry)
                
                # Write back to file
                with open(self.journal_path, 'w') as f:
                    json.dump(trades, f, indent=2)
            
            logger.info(f"📝 Trade recorded in journal: {direction} {symbol} {profit_loss:+.2f}% ({trigger_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to append trade to journal: {str(e)}")
            return False
    
    def get_recent_trades(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent N trades from the journal
        
        Args:
            limit: Number of recent trades to retrieve
            
        Returns:
            List of trade dictionaries (most recent first)
        """
        try:
            with self.lock:
                with open(self.journal_path, 'r') as f:
                    trades = json.load(f)
            
            # Return last N trades in reverse order (most recent first)
            return trades[-limit:][::-1] if trades else []
            
        except Exception as e:
            logger.error(f"Failed to read recent trades: {str(e)}")
            return []
    
    def get_all_trades(self) -> List[Dict[str, Any]]:
        """
        Get all trades from the journal
        
        Returns:
            List of all trade dictionaries
        """
        try:
            with self.lock:
                with open(self.journal_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read all trades: {str(e)}")
            return []
    
    def get_trade_count(self) -> int:
        """
        Get total number of trades in journal
        
        Returns:
            Number of trades
        """
        try:
            with self.lock:
                with open(self.journal_path, 'r') as f:
                    trades = json.load(f)
                return len(trades)
        except Exception as e:
            logger.error(f"Failed to get trade count: {str(e)}")
            return 0
    
    def clear_journal(self) -> bool:
        """
        Clear all trades from the journal (use with caution!)
        
        Returns:
            True if successful
        """
        try:
            with self.lock:
                with open(self.journal_path, 'w') as f:
                    json.dump([], f)
            logger.warning("⚠️ Trade journal cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear journal: {str(e)}")
            return False
