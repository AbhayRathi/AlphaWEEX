"""
Tests for LLM Strategy Engine and Database Manager
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import modules to test
from core.db import DatabaseManager
from core.strategy_engine import StrategyEngine


class TestDatabaseManager:
    """Test SQLite Database Manager"""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database"""
        db_path = tmp_path / "test_trading.db"
        db = DatabaseManager(str(db_path))
        yield db
        db.close()
    
    def test_database_initialization(self, temp_db):
        """Test database and tables are created"""
        assert temp_db.conn is not None
        
        # Check trades table exists
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        assert cursor.fetchone() is not None
    
    def test_record_trade_entry(self, temp_db):
        """Test recording a trade entry"""
        trade_id = temp_db.record_trade_entry(
            symbol="cmt_btcusdt",
            side="BUY",
            price=50000.0,
            size=0.1,
            reasoning="Test reasoning",
            confidence=0.75
        )
        
        assert trade_id > 0
        
        # Verify trade was stored
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row['symbol'] == "cmt_btcusdt"
        assert row['side'] == "BUY"
        assert row['price'] == 50000.0
        assert row['size'] == 0.1
        assert row['reasoning'] == "Test reasoning"
        assert row['confidence'] == 0.75
    
    def test_record_trade_exit(self, temp_db):
        """Test recording a trade exit"""
        # First, create a trade entry
        trade_id = temp_db.record_trade_entry(
            symbol="cmt_btcusdt",
            side="BUY",
            price=50000.0,
            size=0.1
        )
        
        # Record exit
        success = temp_db.record_trade_exit(
            symbol="cmt_btcusdt",
            exit_price=51000.0,
            outcome=2.0  # 2% profit
        )
        
        assert success is True
        
        # Verify exit was recorded
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        row = cursor.fetchone()
        
        assert row['exit_price'] == 51000.0
        assert row['outcome'] == 2.0
        assert row['exit_timestamp'] is not None
    
    def test_get_recent_performance_empty(self, temp_db):
        """Test performance metrics with no trades"""
        performance = temp_db.get_recent_performance(limit=10)
        
        assert performance['total_trades'] == 0
        assert performance['win_rate'] == 0.0
        assert performance['avg_profit'] == 0.0
        assert performance['total_pnl'] == 0.0
    
    def test_get_recent_performance_with_trades(self, temp_db):
        """Test performance metrics with trades"""
        # Create winning trades
        for i in range(3):
            trade_id = temp_db.record_trade_entry(
                symbol="cmt_btcusdt",
                side="BUY",
                price=50000.0 + i * 100,
                size=0.1
            )
            temp_db.record_trade_exit(
                symbol="cmt_btcusdt",
                exit_price=51000.0 + i * 100,
                outcome=2.0  # 2% profit each
            )
        
        # Create losing trade
        trade_id = temp_db.record_trade_entry(
            symbol="cmt_btcusdt",
            side="BUY",
            price=50000.0,
            size=0.1
        )
        temp_db.record_trade_exit(
            symbol="cmt_btcusdt",
            exit_price=49500.0,
            outcome=-1.0  # 1% loss
        )
        
        performance = temp_db.get_recent_performance(limit=10)
        
        assert performance['total_trades'] == 4
        assert performance['winning_trades'] == 3
        assert performance['losing_trades'] == 1
        assert performance['win_rate'] == 0.75  # 3 out of 4
        assert performance['total_pnl'] == 5.0  # 2+2+2-1
        assert abs(performance['avg_profit'] - 1.25) < 0.01  # Average of 2,2,2,-1
    
    def test_get_symbol_performance(self, temp_db):
        """Test symbol-specific performance"""
        # BTC trades
        for i in range(2):
            trade_id = temp_db.record_trade_entry(
                symbol="cmt_btcusdt",
                side="BUY",
                price=50000.0,
                size=0.1
            )
            temp_db.record_trade_exit(
                symbol="cmt_btcusdt",
                exit_price=51000.0,
                outcome=2.0
            )
        
        # ETH trade
        trade_id = temp_db.record_trade_entry(
            symbol="cmt_ethusdt",
            side="BUY",
            price=3000.0,
            size=1.0
        )
        temp_db.record_trade_exit(
            symbol="cmt_ethusdt",
            exit_price=2970.0,
            outcome=-1.0
        )
        
        btc_performance = temp_db.get_symbol_performance("cmt_btcusdt", limit=10)
        eth_performance = temp_db.get_symbol_performance("cmt_ethusdt", limit=10)
        
        assert btc_performance['total_trades'] == 2
        assert btc_performance['win_rate'] == 1.0  # 100%
        assert btc_performance['total_pnl'] == 4.0
        
        assert eth_performance['total_trades'] == 1
        assert eth_performance['win_rate'] == 0.0  # 0%
        assert eth_performance['total_pnl'] == -1.0
    
    def test_get_all_trades(self, temp_db):
        """Test getting all trades"""
        # Create multiple trades
        for i in range(5):
            temp_db.record_trade_entry(
                symbol="cmt_btcusdt",
                side="BUY",
                price=50000.0 + i * 100,
                size=0.1
            )
        
        trades = temp_db.get_all_trades(limit=10)
        
        assert len(trades) == 5
        assert all('symbol' in t for t in trades)
        assert all(t['symbol'] == "cmt_btcusdt" for t in trades)


class TestStrategyEngine:
    """Test LLM Strategy Engine"""
    
    @pytest.fixture
    def mock_klines(self):
        """Create mock k-lines data"""
        klines = []
        for i in range(100):
            klines.append([
                1640000000000 + i * 60000,  # timestamp
                50000 + i * 10,  # open
                50100 + i * 10,  # high
                49900 + i * 10,  # low
                50050 + i * 10,  # close
                1000000 + i * 1000  # volume
            ])
        return klines
    
    @pytest.fixture
    def mock_performance(self):
        """Create mock performance data"""
        return {
            "total_trades": 10,
            "winning_trades": 6,
            "losing_trades": 4,
            "win_rate": 0.6,
            "avg_profit": 0.5,
            "total_pnl": 5.0,
            "best_trade": 3.0,
            "worst_trade": -2.0,
            "recent_trades": [
                {"symbol": "cmt_btcusdt", "side": "BUY", "outcome": 2.0},
                {"symbol": "cmt_btcusdt", "side": "BUY", "outcome": -1.0}
            ]
        }
    
    def test_strategy_engine_initialization_no_key(self):
        """Test initialization fails without API key"""
        with pytest.raises(ValueError, match="API key required"):
            StrategyEngine(provider="openai", api_key=None)
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_format_candles_data(self, mock_openai_class, mock_klines):
        """Test formatting k-lines for LLM prompt"""
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        formatted = engine._format_candles_data(mock_klines)
        
        assert "Current Price:" in formatted
        assert "Price Change" in formatted
        assert "Recent Price Action" in formatted
        assert "$" in formatted
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_format_trade_history(self, mock_openai_class, mock_performance):
        """Test formatting trade history for LLM prompt"""
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        formatted = engine._format_trade_history(mock_performance)
        
        assert "Total Trades: 10" in formatted
        assert "Win Rate: 60.0%" in formatted
        assert "Total P&L: +5.00%" in formatted
        assert "Recent Trades:" in formatted
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_format_trade_history_empty(self, mock_openai_class):
        """Test formatting empty trade history"""
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        formatted = engine._format_trade_history({"total_trades": 0})
        
        assert "No trade history available" in formatted
        assert "first trade" in formatted.lower()
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_build_prompt(self, mock_openai_class, mock_klines, mock_performance):
        """Test building complete prompt"""
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        prompt = engine._build_prompt(
            symbol="cmt_btcusdt",
            klines=mock_klines,
            performance=mock_performance,
            balance=1000.0,
            leverage=20
        )
        
        assert "cmt_btcusdt" in prompt
        assert "1000.00 USDT" in prompt
        assert "20x" in prompt
        assert "BUY" in prompt
        assert "SELL" in prompt
        assert "HOLD" in prompt
        assert "JSON" in prompt
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_call_openai_success(self, mock_openai_class, mock_klines, mock_performance):
        """Test calling OpenAI API successfully"""
        # Mock the OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "action": "BUY",
            "confidence": 0.75,
            "reasoning": "Strong uptrend with high volume"
        })
        # Mock usage for token tracking
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 500
        mock_usage.completion_tokens = 100
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        decision = engine.get_decision(
            symbol="cmt_btcusdt",
            klines=mock_klines,
            performance=mock_performance
        )
        
        assert decision['action'] == "BUY"
        assert decision['confidence'] == 0.75
        assert "uptrend" in decision['reasoning'].lower()
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_get_decision_fallback_on_error(self, mock_openai_class, mock_klines, mock_performance):
        """Test fallback to HOLD on LLM error"""
        # Mock the OpenAI API to raise an error
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        decision = engine.get_decision(
            symbol="cmt_btcusdt",
            klines=mock_klines,
            performance=mock_performance
        )
        
        assert decision['action'] == "HOLD"
        assert decision['confidence'] == 0.0
        assert "error" in decision['reasoning'].lower()
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_validate_invalid_action(self, mock_openai_class, mock_klines, mock_performance):
        """Test validation of invalid action from LLM"""
        # Mock response with invalid action
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "action": "INVALID",
            "confidence": 0.75,
            "reasoning": "Test"
        })
        # Mock usage for token tracking
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 500
        mock_usage.completion_tokens = 100
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        decision = engine.get_decision(
            symbol="cmt_btcusdt",
            klines=mock_klines,
            performance=mock_performance
        )
        
        # Should default to HOLD for invalid action
        assert decision['action'] == "HOLD"
    
    @patch('core.strategy_engine.ANTHROPIC_AVAILABLE', True)
    @patch('core.strategy_engine.anthropic.Anthropic')
    def test_call_anthropic_success(self, mock_anthropic_class, mock_klines, mock_performance):
        """Test calling Anthropic API successfully"""
        # Mock the Anthropic response
        mock_client = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps({
            "action": "SELL",
            "confidence": 0.80,
            "reasoning": "Overbought conditions detected"
        })
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        # Mock usage for token tracking
        mock_usage = MagicMock()
        mock_usage.input_tokens = 600
        mock_usage.output_tokens = 120
        mock_response.usage = mock_usage
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        engine = StrategyEngine(provider="anthropic", api_key="test_key")
        
        decision = engine.get_decision(
            symbol="cmt_btcusdt",
            klines=mock_klines,
            performance=mock_performance
        )
        
        assert decision['action'] == "SELL"
        assert decision['confidence'] == 0.80
        assert "overbought" in decision['reasoning'].lower()
    
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_get_usage_stats(self, mock_openai_class, mock_klines, mock_performance):
        """Test LLM usage statistics tracking"""
        # Mock the OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "action": "BUY",
            "confidence": 0.75,
            "reasoning": "Test reasoning"
        })
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 500
        mock_usage.completion_tokens = 100
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        engine = StrategyEngine(provider="openai", api_key="test_key")
        
        # Make a decision to accumulate stats
        engine.get_decision(
            symbol="cmt_btcusdt",
            klines=mock_klines,
            performance=mock_performance
        )
        
        # Get usage stats
        stats = engine.get_usage_stats()
        
        assert stats['total_calls'] == 1
        assert stats['total_input_tokens'] == 500
        assert stats['total_output_tokens'] == 100
        assert stats['total_cost_usd'] > 0
        assert stats['provider'] == 'openai'
        assert stats['circuit_breaker_state'] == 'CLOSED'


class TestCompetitionBotIntegration:
    """Integration tests for competition bot with LLM"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables"""
        monkeypatch.setenv("API_KEY", "test_key")
        monkeypatch.setenv("API_SECRET", "test_secret")
        monkeypatch.setenv("API_PASSWORD", "test_password")
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
        monkeypatch.setenv("LLM_PROVIDER", "openai")
    
    @patch('competition_bot.LLM_API_KEY', 'test_openai_key')
    @patch('competition_bot.LLM_PROVIDER', 'openai')
    @patch('core.strategy_engine.OPENAI_AVAILABLE', True)
    @patch('core.strategy_engine.openai.OpenAI')
    def test_bot_initialization_with_llm(self, mock_openai_class, mock_env, tmp_path):
        """Test bot initializes with LLM strategy"""
        from competition_bot import CompetitionTradingBot
        
        # Change to temp directory for database
        os.chdir(tmp_path)
        
        bot = CompetitionTradingBot(use_llm=True)
        
        assert bot.use_llm is True
        assert bot.strategy_engine is not None
        assert bot.db is not None
    
    def test_bot_initialization_without_llm(self, mock_env, tmp_path):
        """Test bot initializes without LLM (fallback mode)"""
        from competition_bot import CompetitionTradingBot
        
        # Change to temp directory for database
        os.chdir(tmp_path)
        
        bot = CompetitionTradingBot(use_llm=False)
        
        assert bot.use_llm is False
        assert bot.db is not None
    
    def test_bot_health_check(self, mock_env, tmp_path):
        """Test bot health check method"""
        from competition_bot import CompetitionTradingBot
        
        # Change to temp directory for database
        os.chdir(tmp_path)
        
        bot = CompetitionTradingBot(use_llm=False)
        
        # Get health check
        health = bot.health_check()
        
        assert 'timestamp' in health
        assert 'bot_running' in health
        assert 'llm_enabled' in health
        assert 'database_available' in health
        assert health['llm_enabled'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
