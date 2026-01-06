"""
Test WEEX API fixes and new modules (database, LLM strategy)
"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db import DatabaseManager
from core.strategy_engine import LLMStrategy


class TestDatabaseManager:
    """Test DatabaseManager functionality"""
    
    def setup_method(self):
        """Setup test database"""
        self.test_db_path = "/tmp/test_trading_memory.db"
        # Clean up if exists
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = DatabaseManager(self.test_db_path)
    
    def teardown_method(self):
        """Cleanup test database"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_database_initialization(self):
        """Test database and tables are created"""
        assert os.path.exists(self.test_db_path)
    
    def test_record_trade(self):
        """Test recording a trade"""
        trade_id = self.db.record_trade(
            symbol="cmt_btcusdt",
            side="BUY",
            price=50000.0,
            pnl=0.0,
            reasoning="Test trade",
            confidence=85.0
        )
        assert trade_id > 0
    
    def test_get_recent_performance(self):
        """Test retrieving recent trades"""
        # Record some trades
        for i in range(3):
            self.db.record_trade(
                symbol="cmt_btcusdt",
                side="BUY" if i % 2 == 0 else "SELL",
                price=50000.0 + i * 100,
                pnl=i * 0.5,
                reasoning=f"Trade {i}",
                confidence=80.0 + i
            )
        
        trades = self.db.get_recent_performance(limit=5)
        assert len(trades) == 3
        assert trades[0]['symbol'] == "cmt_btcusdt"
    
    def test_get_bot_state(self):
        """Test bot state retrieval"""
        state = self.db.get_bot_state()
        assert 'last_action_time' in state
        assert 'total_pnl' in state
        assert state['total_pnl'] == 0.0
    
    def test_update_bot_state(self):
        """Test bot state update"""
        from datetime import datetime
        now = datetime.now().isoformat()
        success = self.db.update_bot_state(last_action_time=now)
        assert success
        
        state = self.db.get_bot_state()
        assert state['last_action_time'] == now
    
    def test_get_trade_statistics(self):
        """Test trade statistics"""
        # Record some trades with different PnLs
        self.db.record_trade("cmt_btcusdt", "BUY", 50000.0, 2.5, "Win", 90.0)
        self.db.record_trade("cmt_btcusdt", "SELL", 51000.0, -1.0, "Loss", 85.0)
        self.db.record_trade("cmt_ethusdt", "BUY", 3000.0, 1.5, "Win", 88.0)
        
        stats = self.db.get_trade_statistics()
        assert stats['total_trades'] == 3
        assert stats['winning_trades'] == 2
        assert stats['win_rate'] > 0


class TestLLMStrategy:
    """Test LLMStrategy functionality"""
    
    def setup_method(self):
        """Setup LLM strategy (without API key for basic tests)"""
        # Don't use real API key in tests
        self.strategy = LLMStrategy(api_key=None)
    
    def test_llm_strategy_initialization(self):
        """Test LLM strategy initializes"""
        assert self.strategy is not None
        assert self.strategy.confidence_threshold == 80
    
    def test_format_candles(self):
        """Test candle formatting"""
        # Mock candle data
        klines = [
            [1609459200000, 29000.0, 29500.0, 28500.0, 29200.0, 1000.0],
            [1609459260000, 29200.0, 29600.0, 29000.0, 29400.0, 1100.0],
        ]
        
        formatted = self.strategy._format_candles(klines)
        assert "Recent Price Data" in formatted
        assert "29000.00" in formatted or "29,000.00" in formatted
    
    def test_format_past_trades(self):
        """Test past trades formatting"""
        past_trades = [
            {
                'symbol': 'cmt_btcusdt',
                'side': 'BUY',
                'price': 50000.0,
                'pnl': 2.5,
                'confidence': 90.0,
                'reasoning': 'Strong uptrend'
            }
        ]
        
        formatted = self.strategy._format_past_trades(past_trades)
        assert "Past Trade Performance" in formatted
        assert "cmt_btcusdt" in formatted
    
    def test_generate_signal_without_api_key(self):
        """Test signal generation fails gracefully without API key"""
        klines = [
            [1609459200000, 29000.0, 29500.0, 28500.0, 29200.0, 1000.0],
        ]
        past_trades = []
        
        signal = self.strategy.generate_signal("cmt_btcusdt", klines, past_trades)
        # Should return HOLD signal when LLM call fails
        assert signal['action'] == 'HOLD'
        assert signal['confidence'] == 0
    
    def test_get_market_sentiment(self):
        """Test market sentiment generation"""
        klines = [
            [1609459200000, 29000.0, 29500.0, 28500.0, 29200.0, 1000.0],
            [1609459260000, 29200.0, 30000.0, 29000.0, 29800.0, 1100.0],
        ]
        past_trades = [
            {'pnl': 2.5},
            {'pnl': -1.0}
        ]
        
        sentiment = self.strategy.get_market_sentiment(klines, past_trades)
        assert isinstance(sentiment, str)
        assert len(sentiment) > 0


class TestWEEXv2ClientUpdates:
    """Test WEEX v2 client API fixes"""
    
    def test_imports(self):
        """Test that updated modules can be imported"""
        from core.weex_v2_client import WEEXv2Client
        assert WEEXv2Client is not None
    
    def test_client_has_required_methods(self):
        """Test client has the required methods"""
        from core.weex_v2_client import WEEXv2Client
        
        # Create a mock client (won't make real API calls in this test)
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        assert hasattr(client, 'get_market_klines')
        assert hasattr(client, 'set_leverage')
        assert hasattr(client, 'place_market_order')
        assert hasattr(client, 'has_open_position')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
