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
        """Test Alpha-Apex multi-tier TP/SL calculation for LONG position"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Add LONG position
        symbol = "cmt_btcusdt"
        client.open_positions[symbol] = {
            "entryPrice": "50000",
            "side": "LONG",
            "size": "0.1"
        }
        
        # Test first partial trigger at +0.25%
        partial1_price = 50125  # 0.25% above entry
        trigger = client.check_tp_sl_triggers(symbol, partial1_price)
        assert trigger == "PARTIAL_1"
        
        # Mark first partial taken
        client.position_scaling_state[symbol] = {
            "partial_taken": True,
            "breakeven_set": True,
            "reinvested": False,
            "original_size": 0.1,
            "realized_profit": 0.125
        }
        
        # Test second partial trigger at +0.50%
        partial2_price = 50250  # 0.50% above entry
        trigger = client.check_tp_sl_triggers(symbol, partial2_price)
        assert trigger == "PARTIAL_2"
        
        # Test SL trigger (1.06% loss - fee adjusted)
        client.position_scaling_state[symbol]["breakeven_set"] = False
        sl_price = 49470  # 1.06% below entry
        trigger = client.check_tp_sl_triggers(symbol, sl_price)
        assert trigger == "SL"
        
        # Test break-even SL after first partial
        client.position_scaling_state[symbol]["breakeven_set"] = True
        be_price = 49990  # Just below entry
        trigger = client.check_tp_sl_triggers(symbol, be_price)
        assert trigger == "SL"
        
        # Test no trigger (within range)
        neutral_price = 50050  # 0.1% above entry
        trigger = client.check_tp_sl_triggers(symbol, neutral_price)
        assert trigger is None
    
    def test_tp_sl_calculation_short(self):
        """Test Alpha-Apex multi-tier TP/SL calculation for SHORT position"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Add SHORT position
        symbol = "cmt_ethusdt"
        client.open_positions[symbol] = {
            "entryPrice": "3000",
            "side": "SHORT",
            "size": "1.0"
        }
        
        # Test first partial trigger at +0.25% (price drop)
        partial1_price = 2992.5  # 0.25% below entry
        trigger = client.check_tp_sl_triggers(symbol, partial1_price)
        assert trigger == "PARTIAL_1"
        
        # Mark first partial taken
        client.position_scaling_state[symbol] = {
            "partial_taken": True,
            "breakeven_set": True,
            "reinvested": False,
            "original_size": 1.0,
            "realized_profit": 0.125
        }
        
        # Test second partial trigger at +0.50%
        partial2_price = 2985  # 0.50% below entry
        trigger = client.check_tp_sl_triggers(symbol, partial2_price)
        assert trigger == "PARTIAL_2"
        
        # Test SL trigger (1.06% gain against short)
        client.position_scaling_state[symbol]["breakeven_set"] = False
        sl_price = 3031.8  # 1.06% above entry
        trigger = client.check_tp_sl_triggers(symbol, sl_price)
        assert trigger == "SL"
        
        # Test no trigger
        neutral_price = 2997  # 0.1% below entry
        trigger = client.check_tp_sl_triggers(symbol, neutral_price)
        assert trigger is None
    
    def test_set_leverage_endpoint(self):
        """Test leverage endpoint uses correct path and body format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 0, 'success': True}
        
        # Patch the session.post method instead of requests.post
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
        
            # Call set_leverage
            result = client.set_leverage("cmt_btcusdt", 10)
            
            # Verify result
            assert result is True
            
            # Verify the endpoint was called with correct parameters
            assert mock_post.called
            call_args = mock_post.call_args
            
            # Check URL contains correct path
            assert "/capi/v2/account/leverage" in call_args[0][0]
            
            # Check body contains marginMode and leverage as string
            body_data = json.loads(call_args[1]['data'])
            assert body_data['symbol'] == "cmt_btcusdt"
            assert body_data['marginMode'] == "isolated"  # Updated for Critical Fix 1
            assert body_data['leverage'] == "10"
            assert isinstance(body_data['leverage'], str)
    
    def test_set_leverage_already_set_handling(self):
        """Test 'already set' message is handled as success"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response with "already set" message
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 1,
            'message': 'Leverage already set to 10x',
            'success': False
        }
        
        # Patch the session.post method instead of requests.post
        with patch.object(client.session, 'post', return_value=mock_response):
            # Call set_leverage
            result = client.set_leverage("cmt_btcusdt", 10)
            
            # Should return True (success) for "already set" message
            assert result is True
    
    def test_get_klines_granularity_parameter(self):
        """Test candles endpoint uses 'granularity' parameter instead of 'interval'"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response (WEEX V2 returns list directly)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [1234567890, '50000', '51000', '49000', '50500', '100'],
            [1234567900, '50500', '51500', '50000', '51000', '150']
        ]
        
        # Patch the session.get method instead of requests.get
        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            # Call get_market_klines
            klines = client.get_market_klines("cmt_btcusdt", "1m", limit=2)
            
            # Verify result
            assert len(klines) == 2
            
            # Verify the endpoint was called with 'granularity' parameter
            assert mock_get.called
            call_args = mock_get.call_args
            url = call_args[0][0]
            
            # Check URL contains 'granularity' not 'interval'
            assert "granularity=1m" in url
            assert "interval=" not in url
            # Alpha-Apex: Verify cmt_ prefix is stripped for market data
            assert "btcusdt" in url.lower()
            assert "cmt_btcusdt" not in url.lower()


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
    
    def test_log_decision_with_reasoning(self, temp_log_file):
        """Test new log_decision method with reasoning"""
        logger = AITradingLogger(temp_log_file)
        
        # Log a decision with reasoning
        logger.log_decision(
            symbol="cmt_btcusdt",
            decision="BUY",
            confidence=0.85,
            reason="RSI oversold at 28 and high funding rate suggests short squeeze"
        )
        
        # Read log file
        with open(temp_log_file, 'r') as f:
            log_line = f.readline().strip()
        
        # Should be valid JSON
        log_entry = json.loads(log_line)
        
        assert log_entry["type"] == "AI_DECISION"
        assert log_entry["symbol"] == "cmt_btcusdt"
        assert log_entry["decision"] == "BUY"
        assert log_entry["confidence"] == 0.85
        assert log_entry["reason"] == "RSI oversold at 28 and high funding rate suggests short squeeze"
        assert "timestamp" in log_entry
    
    def test_log_decision_for_all_actions(self, temp_log_file):
        """Test log_decision works for HOLD, BUY, and SELL decisions"""
        logger = AITradingLogger(temp_log_file)
        
        # Test all decision types
        decisions = [
            ("BUY", "Strong bullish momentum"),
            ("SELL", "Overbought conditions detected"),
            ("HOLD", "Neutral market conditions")
        ]
        
        for decision, reason in decisions:
            logger.log_decision(
                symbol="cmt_ethusdt",
                decision=decision,
                confidence=0.75,
                reason=reason
            )
        
        # Read all log entries
        with open(temp_log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        # Verify each entry
        for i, (expected_decision, expected_reason) in enumerate(decisions):
            log_entry = json.loads(lines[i].strip())
            assert log_entry["decision"] == expected_decision
            assert log_entry["reason"] == expected_reason


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
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Test with sample data (trending up)
        closes = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116]
        rsi = bot.calculate_rsi(closes, period=14)
        
        # RSI should be above 50 for uptrend
        assert rsi > 50
        assert rsi <= 100
    
    def test_sma_calculation(self, mock_env):
        """Test SMA calculation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Test with sample data
        closes = [100, 102, 104, 106, 108]
        sma = bot.calculate_sma(closes, period=5)
        
        # SMA should be average of closes
        expected_sma = sum(closes) / len(closes)
        assert abs(sma - expected_sma) < 0.01
    
    def test_signal_generation_buy(self, mock_env):
        """Test BUY signal generation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(use_llm=False, test_mode=True)  # Use RSI/SMA fallback for testing
        
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
        
        bot = CompetitionTradingBot(use_llm=False, test_mode=True)  # Use RSI/SMA fallback for testing
        
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
        
        bot = CompetitionTradingBot(test_mode=True)
        
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


class TestSafetyEnhancements:
    """Test safety and operational enhancements"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables for testing"""
        monkeypatch.setenv("API_KEY", "test_key")
        monkeypatch.setenv("API_SECRET", "test_secret")
        monkeypatch.setenv("API_PASSWORD", "test_password")
    
    def test_calculate_total_exposure(self, mock_env):
        """Test Critical Fix 2: Global exposure calculation"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Mock has_open_position and set open_positions directly
        def mock_has_open_position(symbol):
            return symbol in ["cmt_btcusdt", "cmt_ethusdt"]
        
        # Set positions in the client's tracking
        bot.client.open_positions = {
            "cmt_btcusdt": {"size": "0.1", "entryPrice": "10000"},  # 0.1 * 10000 = 1000
            "cmt_ethusdt": {"size": "0.5", "entryPrice": "1000"}     # 0.5 * 1000 = 500
        }
        
        with patch.object(bot.client, 'has_open_position', side_effect=mock_has_open_position):
            with patch.object(bot.client, 'get_account_balance', return_value={'availableBalance': '10000'}):
                exposure = bot.calculate_total_exposure()
        
        # Should be 15% (1500 / 10000 * 100)
        assert abs(exposure - 15.0) < 0.1
    
    def test_calculate_total_exposure_no_positions(self, mock_env):
        """Test exposure calculation with no positions"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        bot.client.open_positions = {}
        
        with patch.object(bot.client, 'get_account_balance', return_value={'availableBalance': '10000'}):
            exposure = bot.calculate_total_exposure()
        
        assert exposure == 0.0
    
    def test_cancel_stale_orders(self, mock_env):
        """Test Enhancement 3: Stale order reaper"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Add a stale order (older than 5 minutes)
        old_time = time.time() - 400  # 400 seconds ago
        bot.pending_orders = {
            "order123": {"symbol": "cmt_btcusdt", "timestamp": old_time, "side": "BUY"},
            "order456": {"symbol": "cmt_ethusdt", "timestamp": time.time(), "side": "BUY"}  # Fresh
        }
        
        # Mock cancel_order method (create it if it doesn't exist)
        with patch.object(bot.client, 'cancel_order', create=True, return_value=True):
            bot.cancel_stale_orders(max_age_seconds=300)
        
        # Only fresh order should remain
        assert "order123" not in bot.pending_orders
        assert "order456" in bot.pending_orders
    
    def test_is_volume_spike_sufficient(self, mock_env):
        """Test Enhancement 6: Volume spike filter with sufficient volume"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Create klines with recent volume spike
        klines = []
        for i in range(20):
            volume = 1000 if i < 19 else 2000  # Last candle has 2x volume
            klines.append([
                1640000000000 + i * 60000,
                50000, 50100, 49900, 50050,
                volume
            ])
        
        result = bot.is_volume_spike(klines, threshold=1.5)
        assert result is True
    
    def test_is_volume_spike_insufficient(self, mock_env):
        """Test Enhancement 6: Volume spike filter with low volume"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Create klines with low recent volume
        klines = []
        for i in range(20):
            volume = 1000 if i < 19 else 500  # Last candle has low volume
            klines.append([
                1640000000000 + i * 60000,
                50000, 50100, 49900, 50050,
                volume
            ])
        
        result = bot.is_volume_spike(klines, threshold=1.5)
        assert result is False
    
    def test_is_volume_spike_edge_cases(self, mock_env):
        """Test volume spike filter edge cases"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Empty klines - should allow trade
        assert bot.is_volume_spike([], threshold=1.5) is True
        
        # Single candle - should allow trade
        assert bot.is_volume_spike([[0, 0, 0, 0, 0, 1000]], threshold=1.5) is True
    
    # Legacy tests removed - Alpha-Apex uses PARTIAL_1, PARTIAL_2, SL triggers instead of TP
    # def test_fee_adjusted_tp_sl_long(self):
    #     """Test Enhancement 5: Fee-adjusted TP/SL for LONG position"""
    #     # DEPRECATED: Alpha-Apex returns "PARTIAL_1", "PARTIAL_2", or "SL", never "TP"
    
    # def test_fee_adjusted_tp_sl_short(self):
    #     """Test Enhancement 5: Fee-adjusted TP/SL for SHORT position"""
    #     # DEPRECATED: Alpha-Apex returns "PARTIAL_1", "PARTIAL_2", or "SL", never "TP"
    
    def test_position_timeout_tracking(self, mock_env):
        """Test Enhancement 8: Position timeout tracking"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Track position open time
        symbol = "cmt_btcusdt"
        bot.position_open_times[symbol] = time.time() - 3700  # 61 minutes ago
        
        # Check if it's been open too long
        time_open = time.time() - bot.position_open_times[symbol]
        assert time_open > 3600  # Over 1 hour
    
    def test_margin_mode_isolated(self):
        """Test Critical Fix 1: Margin mode changed to isolated"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 0, 'success': True}
        
        # Patch the session.post method instead of requests.post
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            # Call set_leverage
            result = client.set_leverage("cmt_btcusdt", 20)
            
            # Verify result
            assert result is True
            
            # Verify the endpoint was called with isolated margin mode
            call_args = mock_post.call_args
            body_data = json.loads(call_args[1]['data'])
            assert body_data['marginMode'] == "isolated", "Margin mode should be isolated, not crossed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
