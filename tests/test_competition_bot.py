"""
Tests for Competition-Ready Trading Bot Components
"""
import pytest
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import modules to test
from core.weex_v2_client import WEEXv2Client
from core.ai_logger import AITradingLogger


class TestWEEXv2Client:
    """Test WEEX v2 API client"""
    
    def test_signature_generation(self):
        """Test signature generation matches expected format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        timestamp = "1234567890000"
        method = "GET"
        path = "/capi/v2/market/candles"
        query = "?symbol=cmt_btcusdt"
        body = ""
        
        signature = client.generate_signature(timestamp, method, path, query, body)
        
        # Signature should be base64 encoded
        assert isinstance(signature, str)
        assert len(signature) > 0
        
        # Should be consistent
        signature2 = client.generate_signature(timestamp, method, path, query, body)
        assert signature == signature2
    
    def test_cooldown_after_521_error(self):
        """Test cooldown mechanism after 521 error"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Simulate 521 error
        client.last_521_error_time = time.time()
        
        # Should raise exception during cooldown
        with pytest.raises(Exception, match="Cooldown active"):
            client.send_weex_request("GET", "/test")
    
    def test_has_open_position_tracking(self):
        """Test position tracking"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # No position initially
        assert "cmt_btcusdt" not in client.open_positions
        
        # Add mock position
        client.open_positions["cmt_btcusdt"] = {
            "symbol": "cmt_btcusdt",
            "size": "0.1",
            "entryPrice": "50000",
            "side": "LONG"
        }
        
        # Should track position
        assert "cmt_btcusdt" in client.open_positions
    
    def test_tp_sl_calculation_long(self):
        """Test TP/SL trigger calculation for LONG position"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Add LONG position
        symbol = "cmt_btcusdt"
        client.open_positions[symbol] = {
            "entryPrice": "50000",
            "side": "LONG",
            "size": "0.1"
        }
        
        # Test TP trigger (2% gain)
        tp_price = 51000  # 2% above entry
        trigger = client.check_tp_sl_triggers(symbol, tp_price)
        assert trigger == "TP"
        
        # Test SL trigger (1% loss)
        sl_price = 49500  # 1% below entry
        trigger = client.check_tp_sl_triggers(symbol, sl_price)
        assert trigger == "SL"
        
        # Test no trigger (within range)
        neutral_price = 50500  # 1% above entry
        trigger = client.check_tp_sl_triggers(symbol, neutral_price)
        assert trigger is None
    
    def test_tp_sl_calculation_short(self):
        """Test TP/SL trigger calculation for SHORT position"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Add SHORT position
        symbol = "cmt_ethusdt"
        client.open_positions[symbol] = {
            "entryPrice": "3000",
            "side": "SHORT",
            "size": "1.0"
        }
        
        # Test TP trigger (2% drop)
        tp_price = 2940  # 2% below entry
        trigger = client.check_tp_sl_triggers(symbol, tp_price)
        assert trigger == "TP"
        
        # Test SL trigger (1% gain against short)
        sl_price = 3030  # 1% above entry
        trigger = client.check_tp_sl_triggers(symbol, sl_price)
        assert trigger == "SL"
        
        # Test no trigger
        neutral_price = 2985  # 0.5% below entry
        trigger = client.check_tp_sl_triggers(symbol, neutral_price)
        assert trigger is None


class TestAITradingLogger:
    """Test AI Trading Logger"""
    
    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create temporary log file"""
        log_file = tmp_path / "test_trading.log"
        return str(log_file)
    
    def test_logger_initialization(self, temp_log_file):
        """Test logger initializes correctly"""
        logger = AITradingLogger(temp_log_file)
        
        assert logger.log_file == temp_log_file
        assert logger.heartbeat_interval == 600
        assert Path(temp_log_file).exists()
    
    def test_json_log_format(self, temp_log_file):
        """Test logs are in single-line JSON format"""
        logger = AITradingLogger(temp_log_file)
        
        # Log a trade decision
        logger.log_trade_decision(
            symbol="cmt_btcusdt",
            action="BUY",
            reason="Test reason",
            confidence=0.75,
            indicators={"rsi": 30, "sma": 50000}
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_line = f.readline().strip()
        
        # Should be valid JSON
        log_entry = json.loads(log_line)
        
        assert log_entry["type"] == "TRADE_DECISION"
        assert log_entry["symbol"] == "cmt_btcusdt"
        assert log_entry["action"] == "BUY"
        assert log_entry["confidence"] == 0.75
        assert "timestamp" in log_entry
    
    def test_heartbeat_logging(self, temp_log_file):
        """Test heartbeat logging"""
        logger = AITradingLogger(temp_log_file)
        
        # Force heartbeat (should always log)
        logger.force_heartbeat(
            market_data={"price": 50000, "rsi": 50},
            sentiment="RSI is 50, Neutral stance"
        )
        
        # Read log
        with open(temp_log_file, 'r') as f:
            log_line = f.readline().strip()
        
        log_entry = json.loads(log_line)
        
        assert log_entry["type"] == "HEARTBEAT"
        assert log_entry["market_sentiment"] == "RSI is 50, Neutral stance"
        assert log_entry["forced"] is True
    
    def test_heartbeat_interval(self, temp_log_file):
        """Test heartbeat respects 10-minute interval"""
        logger = AITradingLogger(temp_log_file)
        
        # Reset last_heartbeat_time to 0 to force first heartbeat
        logger.last_heartbeat_time = 0
        
        # First heartbeat should log
        result1 = logger.log_heartbeat(
            market_data={"price": 50000},
            sentiment="Test 1"
        )
        assert result1 is True
        
        # Immediate second heartbeat should not log (interval not elapsed)
        result2 = logger.log_heartbeat(
            market_data={"price": 50000},
            sentiment="Test 2"
        )
        assert result2 is False
        
        # Should only have one entry
        with open(temp_log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        
        # Verify it's the first heartbeat
        log_entry = json.loads(lines[0].strip())
        assert log_entry["market_sentiment"] == "Test 1"
    
    def test_tp_sl_logging(self, temp_log_file):
        """Test TP/SL trigger logging"""
        logger = AITradingLogger(temp_log_file)
        
        # Log TP trigger
        logger.log_tp_sl_trigger(
            symbol="cmt_btcusdt",
            trigger_type="TP",
            entry_price=50000,
            exit_price=51000,
            pnl_pct=2.0
        )
        
        with open(temp_log_file, 'r') as f:
            log_line = f.readline().strip()
        
        log_entry = json.loads(log_line)
        
        assert log_entry["type"] == "TP_TRIGGER"
        assert log_entry["symbol"] == "cmt_btcusdt"
        assert log_entry["pnl_pct"] == 2.0
    
    def test_error_logging(self, temp_log_file):
        """Test error logging"""
        logger = AITradingLogger(temp_log_file)
        
        logger.log_error(
            error_type="521_ERROR",
            error_message="Firewall block",
            context={"symbol": "cmt_btcusdt"}
        )
        
        with open(temp_log_file, 'r') as f:
            log_line = f.readline().strip()
        
        log_entry = json.loads(log_line)
        
        assert log_entry["type"] == "ERROR"
        assert log_entry["error_type"] == "521_ERROR"
        assert log_entry["context"]["symbol"] == "cmt_btcusdt"
    
    def test_log_stats(self, temp_log_file):
        """Test log statistics"""
        logger = AITradingLogger(temp_log_file)
        
        # Create various log entries
        logger.force_heartbeat({"price": 50000}, "Test")
        logger.log_trade_decision("cmt_btcusdt", "BUY", "Test", 0.75, {})
        logger.log_order_execution("cmt_btcusdt", "BUY", 0.1, 50000)
        logger.log_tp_sl_trigger("cmt_btcusdt", "TP", 50000, 51000, 2.0)
        logger.log_error("TEST_ERROR", "Test error")
        
        # Get stats
        stats = logger.get_log_stats()
        
        assert stats["total_lines"] == 5
        assert stats["heartbeats"] == 1
        assert stats["trade_decisions"] == 1
        assert stats["order_executions"] == 1
        assert stats["tp_triggers"] == 1
        assert stats["errors"] == 1


class TestCompetitionBotLogic:
    """Test competition bot logic"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables for testing"""
        monkeypatch.setenv("API_KEY", "test_key")
        monkeypatch.setenv("API_SECRET", "test_secret")
        monkeypatch.setenv("API_PASSWORD", "test_password")
    
    def test_rsi_calculation(self, mock_env):
        """Test RSI calculation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot()
        
        # Test with sample data (trending up)
        closes = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116]
        rsi = bot.calculate_rsi(closes, period=14)
        
        # RSI should be above 50 for uptrend
        assert rsi > 50
        assert rsi <= 100
    
    def test_sma_calculation(self, mock_env):
        """Test SMA calculation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot()
        
        # Test with sample data
        closes = [100, 102, 104, 106, 108]
        sma = bot.calculate_sma(closes, period=5)
        
        # SMA should be average of closes
        expected_sma = sum(closes) / len(closes)
        assert abs(sma - expected_sma) < 0.01
    
    def test_signal_generation_buy(self, mock_env):
        """Test BUY signal generation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(use_llm=False)  # Use RSI/SMA fallback for testing
        
        # Create k-lines data that would suggest BUY (price trending down, RSI oversold)
        klines = []
        base_price = 52000
        for i in range(50):
            # Trending down to create oversold condition
            price = base_price - (i * 50)
            klines.append([
                1640000000000 + i * 60000,  # timestamp
                price,  # open
                price + 50,  # high
                price - 50,  # low
                price,  # close
                1000000  # volume
            ])
        
        signal = bot.generate_signal(klines, "cmt_btcusdt")
        
        assert signal["action"] == "BUY"
        assert signal["confidence"] > 0.6
    
    def test_signal_generation_sell(self, mock_env):
        """Test SELL signal generation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(use_llm=False)  # Use RSI/SMA fallback for testing
        
        # Create k-lines data that would suggest SELL (price trending up, RSI overbought)
        klines = []
        base_price = 48000
        for i in range(50):
            # Trending up to create overbought condition
            price = base_price + (i * 50)
            klines.append([
                1640000000000 + i * 60000,  # timestamp
                price,  # open
                price + 50,  # high
                price - 50,  # low
                price,  # close
                1000000  # volume
            ])
        
        signal = bot.generate_signal(klines, "cmt_btcusdt")
        
        assert signal["action"] == "SELL"
        assert signal["confidence"] > 0.6
    
    def test_sentiment_generation(self, mock_env):
        """Test sentiment string generation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot()
        
        # Test neutral sentiment
        indicators = {
            "valid": True,
            "current_price": 50000,
            "rsi": 50,
            "sma_20": 50000
        }
        
        sentiment = bot.generate_sentiment(indicators)
        
        assert "RSI is 50" in sentiment
        assert "Neutral" in sentiment
        assert "50000" in sentiment


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
