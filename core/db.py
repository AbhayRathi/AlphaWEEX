"""
Persistent Memory System using SQLite
Stores trade history and bot state for AI learning
"""
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite Database Manager for AI Trading Bot
    
    Features:
    - Trade history tracking with reasoning and confidence
    - Bot state persistence
    - Recent performance retrieval for AI learning
    """
    
    def __init__(self, db_path: str = "data/trading_memory.db"):
        """
        Initialize Database Manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"✅ Database initialized: {db_path}")
    
    def _init_database(self) -> None:
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create trade_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                pnl REAL DEFAULT 0.0,
                reasoning TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create bot_state table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_action_time TEXT,
                total_pnl REAL DEFAULT 0.0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize bot_state with default values if empty
        cursor.execute('SELECT COUNT(*) FROM bot_state')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO bot_state (id, last_action_time, total_pnl)
                VALUES (1, ?, 0.0)
            ''', (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
    
    def record_trade(self, symbol: str, side: str, price: float, 
                    pnl: float = 0.0, reasoning: str = "", 
                    confidence: float = 0.0) -> int:
        """
        Record a trade in the database
        
        Args:
            symbol: Trading symbol
            side: Trade side (BUY/SELL)
            price: Execution price
            pnl: Profit/Loss for this trade
            reasoning: AI reasoning for the trade
            confidence: AI confidence level (0-100)
            
        Returns:
            Trade ID (row id)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trade_history 
                (timestamp, symbol, side, price, pnl, reasoning, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                symbol,
                side.upper(),
                price,
                pnl,
                reasoning,
                confidence
            ))
            
            trade_id = cursor.lastrowid
            
            # Update total PnL in bot_state
            cursor.execute('''
                UPDATE bot_state 
                SET total_pnl = total_pnl + ?,
                    last_action_time = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (pnl, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Trade recorded: {side} {symbol} @ {price} (PnL: {pnl:+.2f})")
            return trade_id
            
        except Exception as e:
            logger.error(f"Failed to record trade: {str(e)}")
            return -1
    
    def get_recent_performance(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent trade performance for AI learning
        
        Args:
            limit: Number of recent trades to retrieve (default: 5)
            
        Returns:
            List of trade dictionaries with all fields
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, timestamp, symbol, side, price, pnl, 
                    reasoning, confidence
                FROM trade_history
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            trades = []
            for row in rows:
                trades.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'symbol': row['symbol'],
                    'side': row['side'],
                    'price': row['price'],
                    'pnl': row['pnl'],
                    'reasoning': row['reasoning'],
                    'confidence': row['confidence']
                })
            
            logger.info(f"📊 Retrieved {len(trades)} recent trades")
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get recent performance: {str(e)}")
            return []
    
    def get_bot_state(self) -> Dict[str, Any]:
        """
        Get current bot state
        
        Returns:
            Dictionary with last_action_time and total_pnl
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM bot_state WHERE id = 1')
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'last_action_time': row['last_action_time'],
                    'total_pnl': row['total_pnl'],
                    'updated_at': row['updated_at']
                }
            else:
                return {
                    'last_action_time': None,
                    'total_pnl': 0.0,
                    'updated_at': None
                }
                
        except Exception as e:
            logger.error(f"Failed to get bot state: {str(e)}")
            return {
                'last_action_time': None,
                'total_pnl': 0.0,
                'updated_at': None
            }
    
    def update_bot_state(self, last_action_time: Optional[str] = None, 
                        total_pnl: Optional[float] = None) -> bool:
        """
        Update bot state
        
        Args:
            last_action_time: Last action timestamp (ISO format)
            total_pnl: Total P&L (optional, usually updated via record_trade)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if last_action_time:
                updates.append('last_action_time = ?')
                params.append(last_action_time)
            
            if total_pnl is not None:
                updates.append('total_pnl = ?')
                params.append(total_pnl)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                sql = f"UPDATE bot_state SET {', '.join(updates)} WHERE id = 1"
                cursor.execute(sql, params)
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update bot state: {str(e)}")
            return False
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """
        Get trade statistics
        
        Returns:
            Dictionary with various statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total trades
            cursor.execute('SELECT COUNT(*) FROM trade_history')
            total_trades = cursor.fetchone()[0]
            
            # Win rate
            cursor.execute('SELECT COUNT(*) FROM trade_history WHERE pnl > 0')
            winning_trades = cursor.fetchone()[0]
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            # Average PnL
            cursor.execute('SELECT AVG(pnl) FROM trade_history')
            avg_pnl = cursor.fetchone()[0] or 0.0
            
            # Total PnL
            cursor.execute('SELECT total_pnl FROM bot_state WHERE id = 1')
            total_pnl = cursor.fetchone()[0] or 0.0
            
            # Average confidence
            cursor.execute('SELECT AVG(confidence) FROM trade_history WHERE confidence > 0')
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'total_pnl': total_pnl,
                'avg_confidence': avg_confidence
            }
            
        except Exception as e:
            logger.error(f"Failed to get trade statistics: {str(e)}")
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0.0,
                'avg_pnl': 0.0,
                'total_pnl': 0.0,
                'avg_confidence': 0.0
            }
    
    def clear_history(self) -> bool:
        """
        Clear all trade history (for testing purposes)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM trade_history')
            cursor.execute('UPDATE bot_state SET total_pnl = 0.0 WHERE id = 1')
            
            conn.commit()
            conn.close()
            
            logger.warning("⚠️ Trade history cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear history: {str(e)}")
            return False
