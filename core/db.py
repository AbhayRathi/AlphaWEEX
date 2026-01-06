"""
SQLite Memory Layer for AI Trading Bot

Provides persistent storage for trade history and performance metrics
that the LLM can use for decision-making.
"""
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite-based memory layer for trade history and performance tracking.
    
    Features:
    - Store trade executions with outcomes
    - Query recent performance metrics
    - Calculate success rates and P&L
    """
    
    def __init__(self, db_path: str = "trading_memory.db"):
        """
        Initialize DatabaseManager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
        logger.info(f"✅ DatabaseManager initialized: {self.db_path}")
    
    def _initialize_db(self) -> None:
        """Create database and tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            cursor = self.conn.cursor()
            
            # Create trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price REAL NOT NULL,
                    size REAL NOT NULL,
                    outcome REAL DEFAULT NULL,
                    exit_price REAL DEFAULT NULL,
                    exit_timestamp TEXT DEFAULT NULL,
                    reasoning TEXT DEFAULT NULL,
                    confidence REAL DEFAULT NULL,
                    ai_reasoning TEXT DEFAULT NULL,
                    behavioral_tag TEXT DEFAULT NULL,
                    confidence_score REAL DEFAULT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
                ON trades(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol 
                ON trades(symbol)
            """)
            
            # Add new columns if they don't exist (for migration from old schema)
            try:
                cursor.execute("ALTER TABLE trades ADD COLUMN ai_reasoning TEXT DEFAULT NULL")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE trades ADD COLUMN behavioral_tag TEXT DEFAULT NULL")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE trades ADD COLUMN confidence_score REAL DEFAULT NULL")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            self.conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def record_trade_entry(self, symbol: str, side: str, price: float, 
                          size: float, reasoning: Optional[str] = None,
                          confidence: Optional[float] = None,
                          ai_reasoning: Optional[str] = None,
                          behavioral_tag: Optional[str] = None,
                          confidence_score: Optional[float] = None) -> int:
        """
        Record a trade entry (BUY/SELL opened)
        
        Args:
            symbol: Trading symbol
            side: Trade side (BUY/SELL/LONG/SHORT)
            price: Entry price
            size: Position size
            reasoning: AI reasoning for the trade (legacy)
            confidence: Confidence level (0.0 to 1.0) (legacy)
            ai_reasoning: Detailed AI reasoning
            behavioral_tag: Behavioral psychology tag (FOMO, Panic, etc.)
            confidence_score: Confidence score (0.0 to 1.0)
            
        Returns:
            Trade ID
        """
        try:
            timestamp = datetime.now().isoformat()
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trades (timestamp, symbol, side, price, size, reasoning, confidence,
                                  ai_reasoning, behavioral_tag, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, symbol, side, price, size, reasoning, confidence,
                  ai_reasoning, behavioral_tag, confidence_score))
            
            self.conn.commit()
            trade_id = cursor.lastrowid
            
            logger.info(f"📝 Trade recorded: ID={trade_id}, {side} {symbol} @ {price}")
            return trade_id
            
        except Exception as e:
            logger.error(f"Failed to record trade: {str(e)}")
            return -1
    
    def record_trade_exit(self, symbol: str, exit_price: float, 
                         outcome: float) -> bool:
        """
        Record a trade exit and calculate outcome
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            outcome: Profit/Loss in percentage or absolute value
            
        Returns:
            True if successful
        """
        try:
            exit_timestamp = datetime.now().isoformat()
            
            cursor = self.conn.cursor()
            
            # Find the most recent open trade for this symbol
            cursor.execute("""
                SELECT id FROM trades 
                WHERE symbol = ? AND exit_price IS NULL
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"No open trade found for {symbol}")
                return False
            
            trade_id = row[0]
            
            # Update with exit information
            cursor.execute("""
                UPDATE trades 
                SET exit_price = ?, exit_timestamp = ?, outcome = ?
                WHERE id = ?
            """, (exit_price, exit_timestamp, outcome, trade_id))
            
            self.conn.commit()
            
            logger.info(f"📝 Trade exit recorded: {symbol} P&L={outcome:+.2f}%")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record trade exit: {str(e)}")
            return False
    
    def get_recent_performance(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get recent trading performance metrics for AI decision-making
        
        Args:
            limit: Number of recent trades to analyze
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            cursor = self.conn.cursor()
            
            # Get recent closed trades (with outcomes)
            cursor.execute("""
                SELECT symbol, side, price, exit_price, outcome, timestamp, exit_timestamp
                FROM trades
                WHERE outcome IS NOT NULL
                ORDER BY exit_timestamp DESC
                LIMIT ?
            """, (limit,))
            
            trades = [dict(row) for row in cursor.fetchall()]
            
            if not trades:
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_profit": 0.0,
                    "total_pnl": 0.0,
                    "recent_trades": []
                }
            
            # Calculate metrics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t['outcome'] > 0]
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
            
            outcomes = [t['outcome'] for t in trades]
            avg_profit = sum(outcomes) / len(outcomes) if outcomes else 0.0
            total_pnl = sum(outcomes)
            
            # Get best and worst trades
            best_trade = max(trades, key=lambda t: t['outcome']) if trades else None
            worst_trade = min(trades, key=lambda t: t['outcome']) if trades else None
            
            return {
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": total_trades - len(winning_trades),
                "win_rate": win_rate,
                "avg_profit": avg_profit,
                "total_pnl": total_pnl,
                "best_trade": best_trade['outcome'] if best_trade else 0.0,
                "worst_trade": worst_trade['outcome'] if worst_trade else 0.0,
                "recent_trades": trades[:10]  # Last 10 trades for context
            }
            
        except Exception as e:
            logger.error(f"Failed to get recent performance: {str(e)}")
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "total_pnl": 0.0,
                "recent_trades": [],
                "error": str(e)
            }
    
    def get_symbol_performance(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get performance metrics for a specific symbol
        
        Args:
            symbol: Trading symbol
            limit: Number of recent trades to analyze
            
        Returns:
            Dictionary with symbol-specific metrics
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT side, price, exit_price, outcome, timestamp
                FROM trades
                WHERE symbol = ? AND outcome IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """, (symbol, limit))
            
            trades = [dict(row) for row in cursor.fetchall()]
            
            if not trades:
                return {
                    "symbol": symbol,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_profit": 0.0
                }
            
            total_trades = len(trades)
            winning_trades = [t for t in trades if t['outcome'] > 0]
            outcomes = [t['outcome'] for t in trades]
            
            return {
                "symbol": symbol,
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "win_rate": len(winning_trades) / total_trades if total_trades > 0 else 0.0,
                "avg_profit": sum(outcomes) / len(outcomes) if outcomes else 0.0,
                "total_pnl": sum(outcomes)
            }
            
        except Exception as e:
            logger.error(f"Failed to get symbol performance: {str(e)}")
            return {"symbol": symbol, "error": str(e)}
    
    def get_all_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all trades (for analysis/debugging)
        
        Args:
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Failed to get all trades: {str(e)}")
            return []
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
