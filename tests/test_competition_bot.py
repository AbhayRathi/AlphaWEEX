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
        
        # Add LONG position - use uppercase symbol without cmt_ prefix (as stored internally after cleaning)
        symbol = "BTCUSDT"
        client.open_positions[symbol] = {
            "entryPrice": "50000",
            "side": "LONG",
            "size": "0.1"
        }
        
        # Test first partial trigger at +0.25%
        partial1_price = 50125  # 0.25% above entry
        trigger = client.check_tp_sl_triggers("cmt_btcusdt", partial1_price)
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
        trigger = client.check_tp_sl_triggers("cmt_btcusdt", partial2_price)
        assert trigger == "PARTIAL_2"
        
        # Test SL trigger (0.50% loss for longs)
        client.position_scaling_state[symbol]["breakeven_set"] = False
        # Test SL trigger (0.50% loss for longs)
        client.position_scaling_state[symbol]["breakeven_set"] = False
        sl_price = 49750  # 0.50% below entry (50000 * 0.995 = 49750)
        trigger = client.check_tp_sl_triggers("cmt_btcusdt", sl_price)
        assert trigger == "SL"
        
        # Test no trigger (within range)
        # Reset state
        client.position_scaling_state[symbol] = {
            "partial_taken": False,
            "breakeven_set": False,
            "reinvested": False,
            "original_size": 0.1,
            "realized_profit": 0.0
        }
        neutral_price = 50050  # 0.1% above entry
        trigger = client.check_tp_sl_triggers("cmt_btcusdt", neutral_price)
        assert trigger is None
    
    def test_tp_sl_calculation_short(self):
        """Test Alpha-Apex multi-tier TP/SL calculation for SHORT position"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Add SHORT position - use uppercase symbol without cmt_ prefix
        symbol = "ETHUSDT"
        client.open_positions[symbol] = {
            "entryPrice": "3000",
            "side": "SHORT",
            "size": "1.0"
        }
        
        # Test first partial trigger at +0.25% (price drop)
        partial1_price = 2992.5  # 0.25% below entry
        trigger = client.check_tp_sl_triggers("cmt_ethusdt", partial1_price)
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
        trigger = client.check_tp_sl_triggers("cmt_ethusdt", partial2_price)
        assert trigger == "PARTIAL_2"
        
        # Test SL trigger (0.40% gain against short - tighter for shorts)
        client.position_scaling_state[symbol]["breakeven_set"] = False
        sl_price = 3012  # 0.40% above entry (3000 * 1.004 = 3012)
        trigger = client.check_tp_sl_triggers("cmt_ethusdt", sl_price)
        assert trigger == "SL"
        
        # Test no trigger
        # Reset state
        client.position_scaling_state[symbol] = {
            "partial_taken": False,
            "breakeven_set": False,
            "reinvested": False,
            "original_size": 1.0,
            "realized_profit": 0.0
        }
        neutral_price = 2997  # 0.1% below entry
        trigger = client.check_tp_sl_triggers("cmt_ethusdt", neutral_price)
        assert trigger is None
    
    def test_set_leverage_endpoint(self):
        """Test leverage endpoint uses correct path and body format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map to avoid network calls
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
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
            
            # Check URL contains correct path (updated to /capi/v2/account/setLeverage)
            assert "/capi/v2/account/setLeverage" in call_args[0][0]
            
            # Check body contains marginMode as string "isolated" and leverage as string
            body_data = json.loads(call_args[1]['data'])
            # Symbol should be resolved to contract format (cmt_btcusdt -> BTCUSDT_UMCBL)
            assert body_data['symbol'] == "BTCUSDT_UMCBL"
            assert body_data['marginMode'] == "isolated"  # String: "isolated" (required by V2 API)
            assert body_data['leverage'] == "10"  # String format required by V2 API
            assert isinstance(body_data['marginMode'], str)
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
            # Verify symbol is cleaned (cmt_ removed, uppercase)
            assert "BTCUSDT" in url
            assert "CMT_" not in url
    
    def test_get_klines_error_handling(self):
        """Test klines endpoint handles errors properly"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map to avoid network calls
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        # Mock call to fail with 400 (non-40020 error to avoid symbol format fallback)
        mock_response_fail = Mock()
        mock_response_fail.status_code = 400
        mock_response_fail.text = "Invalid request"
        mock_response_fail.json.return_value = {'code': '40001', 'msg': 'Invalid request'}
        
        # Patch the session.get method to return error response
        with patch.object(client.session, 'get', return_value=mock_response_fail) as mock_get:
            # Call get_market_klines
            klines = client.get_market_klines("cmt_btcusdt", "1m", limit=2)
            
            # Verify result - should return empty list on error
            assert len(klines) == 0
            
            # Verify the endpoint was called once
            assert mock_get.call_count == 1
    
    def test_get_klines_success(self):
        """Test klines endpoint succeeds with symbol converted to contract format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map to avoid network calls
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        # Mock successful response on first try
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [1234567890, '50000', '51000', '49000', '50500', '100']
        ]
        
        # Patch the session.get method
        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            # Call get_market_klines
            klines = client.get_market_klines("cmt_btcusdt", "1m", limit=1)
            
            # Verify result
            assert len(klines) == 1
            
            # Verify the endpoint was called only once
            assert mock_get.call_count == 1
            
            # Should resolve symbol to contract format
            call_url = mock_get.call_args[0][0]
            assert "BTCUSDT_UMCBL" in call_url
            assert "CMT_" not in call_url
    
    def test_get_order_book_symbol_format(self):
        """Test order book endpoint converts symbol to uppercase"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'success': True,
            'data': {
                'bids': [['50000', '1.0']],
                'asks': [['50100', '1.0']]
            }
        }
        
        # Patch the session.get method
        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            # Call get_order_book with lowercase symbol
            order_book = client.get_order_book("cmt_btcusdt", depth=5)
            
            # Verify result
            assert order_book is not None
            
            # Verify the endpoint was called with correct URL
            assert mock_get.called
            call_args = mock_get.call_args
            url = call_args[0][0]
            
            # Verify symbol is cleaned (cmt_ removed, uppercase)
            assert "BTCUSDT" in url
            assert "CMT_" not in url
            assert "depth=5" in url
    
    def test_get_ticker_symbol_format(self):
        """Test ticker endpoint converts symbol to uppercase"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'success': True,
            'data': {
                'lastPrice': '50000',
                'volume24h': '10000',
                'high24h': '51000',
                'low24h': '49000'
            }
        }
        
        # Patch the session.get method
        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            # Call get_ticker with lowercase symbol
            ticker = client.get_ticker("cmt_ethusdt")
            
            # Verify result
            assert ticker is not None
            assert ticker.get('lastPrice') == '50000'
            
            # Verify the endpoint was called with correct URL
            assert mock_get.called
            call_args = mock_get.call_args
            url = call_args[0][0]
            
            # Verify symbol is cleaned (cmt_ removed, uppercase)
            assert "ETHUSDT" in url
            assert "CMT_" not in url
    
    def test_symbol_format_preserved(self):
        """Test symbol formatting cleans symbols (removes cmt_, uppercase)"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [1234567890, '50000', '51000', '49000', '50500', '100']
        ]
        
        # Patch the session.get method
        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            # Call with lowercase symbol
            klines = client.get_market_klines("cmt_btcusdt", "1m", limit=1)
            
            # Verify result
            assert len(klines) == 1
            
            # Verify the endpoint was called with correct URL
            assert mock_get.called
            call_args = mock_get.call_args
            url = call_args[0][0]
            
            # Should clean symbol (remove cmt_, uppercase)
            assert "BTCUSDT" in url
            assert "CMT_" not in url
    
    def test_place_market_order_preserves_cmt_prefix(self):
        """Test that place_market_order resolves symbol to contract format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map to avoid network calls
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        # Clear any active symbols from previous tests to avoid AI Wars blocking
        client.active_symbols.clear()
        
        # Mock successful order response with nested structure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'success': True,
            'data': {'orderId': '123456', 'status': 'filled'}
        }
        
        # Patch the session.post method
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            # Patch check_spread to return True (skip spread check complexity)
            with patch.object(client, 'check_spread', return_value=True):
                # Call place_market_order with lowercase symbol
                result = client.place_market_order("cmt_btcusdt", "BUY", 0.01)
                
                # Verify order was placed successfully
                assert result is not None
                # Handle nested response structure - orderId is in result['data']['orderId']
                assert result.get('data', {}).get('orderId') == '123456'
                
                # Verify the endpoint was called
                assert mock_post.called
                call_args = mock_post.call_args
                
                # Check body contains resolved contract symbol (cmt_btcusdt -> BTCUSDT_UMCBL)
                body_data = json.loads(call_args[1]['data'])
                assert body_data['symbol'] == "BTCUSDT_UMCBL"
                assert "CMT_" not in body_data['symbol']
                assert body_data['side'] == "1"  # BUY is mapped to "1" in V2 API
                assert body_data['type'] == "1"  # MARKET type is "1" in V2 API
    
    def test_get_account_balance_zero_protection(self):
        """Test that get_account_balance retries on zero balance instead of using fallback"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock API response with zero balance
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'collateral': [
                {
                    'coin_id': '2',
                    'totalEquity': '0.0',
                    'equity': '0.0',
                    'accountEquity': '0.0'
                }
            ]
        }
        
        # Mock time.sleep to avoid actual delays
        with patch('time.sleep'):
            with patch.object(client, 'send_weex_request', return_value=mock_response):
                # Should retry 3 times then return None (not fallback)
                balance = client.get_account_balance()
                assert balance is None, "Should return None after retries, not use emergency fallback"
    
    def test_get_account_balance_comprehensive_key_checking(self):
        """Test that get_account_balance checks all equity keys"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock API response with only accountEquity populated
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'collateral': [
                {
                    'coin_id': '2',
                    'totalEquity': None,
                    'equity': '0.0',
                    'accountEquity': '750.5'
                }
            ]
        }
        
        with patch.object(client, 'send_weex_request', return_value=mock_response):
            balance = client.get_account_balance()
            assert balance is not None
            assert balance['equity'] == 750.5
            assert balance['totalEquity'] == 750.5
    
    def test_get_account_balance_negative_protection(self):
        """Test that get_account_balance handles negative balance"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        client.last_known_positive_balance = 500.0
        
        # Mock API response with negative balance
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'collateral': [
                {
                    'coin_id': '2',
                    'totalEquity': '-10.5',
                    'equity': '-10.5',
                    'accountEquity': '-10.5'
                }
            ]
        }
        
        with patch.object(client, 'send_weex_request', return_value=mock_response):
            balance = client.get_account_balance()
            assert balance is not None
            assert balance['equity'] == 500.0  # Should use last known positive balance
            assert balance['totalEquity'] == 500.0
    
    def test_frozen_balance_check_both_zero(self):
        """Test that frozen balance only triggers when BOTH equity AND available are zero"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Mock balance data with both zero - should be frozen
        mock_balance = {
            'equity': 0,
            'totalEquity': 0,
            'availableBalance': 0,
            'available': 0
        }
        
        with patch.object(bot.client, 'get_account_balance', return_value=mock_balance):
            is_frozen = bot.check_frozen_balance()
            assert is_frozen is True, "Should be frozen when both equity and available are zero"
    
    def test_frozen_balance_check_equity_positive(self):
        """Test that frozen balance does NOT trigger when equity > 0 and available = 0"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Mock balance data with equity > 0 but available = 0 (open position scenario)
        mock_balance = {
            'equity': 1000.0,
            'totalEquity': 1000.0,
            'availableBalance': 0,
            'available': 0
        }
        
        with patch.object(bot.client, 'get_account_balance', return_value=mock_balance):
            is_frozen = bot.check_frozen_balance()
            assert is_frozen is False, "Should NOT be frozen when equity > 0 (has open positions)"
    
    def test_frozen_balance_check_both_positive(self):
        """Test that frozen balance does NOT trigger when both equity and available are positive"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Mock balance data with both positive - normal trading scenario
        mock_balance = {
            'equity': 1000.0,
            'totalEquity': 1000.0,
            'availableBalance': 500.0,
            'available': 500.0
        }
        
        with patch.object(bot.client, 'get_account_balance', return_value=mock_balance):
            is_frozen = bot.check_frozen_balance()
            assert is_frozen is False, "Should NOT be frozen when both equity and available are positive"
    
    def test_balance_available_fallback_from_amount(self):
        """Test that available fallbacks to amount when explicit available field is missing"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock API response without 'available' field but with 'amount'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'collateral': [
                {
                    'coin_id': '2',
                    'amount': '887.61'
                    # No 'available', 'availableBalance', or 'availableFunds' fields
                }
            ]
        }
        
        # Ensure haircut is 1.0 (default)
        with patch.dict(os.environ, {"WEEX_AVAILABLE_FALLBACK_HAIRCUT": "1.0"}):
            with patch.object(client, 'send_weex_request', return_value=mock_response):
                with patch.object(client, 'get_pending_orders_cached', return_value=[]):
                    balance = client.get_account_balance()
                    assert balance is not None
                    # Available should fallback to amount value
                    assert abs(balance['available'] - 887.61) < 0.01, f"Expected available ~887.61, got {balance['available']}"
                    # Equity should also be from amount
                    assert abs(balance['equity'] - 887.61) < 0.01
    
    def test_balance_available_fallback_with_haircut(self):
        """Test that available fallback applies haircut factor correctly"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock API response without 'available' field but with 'amount'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'collateral': [
                {
                    'coin_id': '2',
                    'amount': '1000.0'
                    # No 'available' fields
                }
            ]
        }
        
        # Apply 0.98 haircut
        with patch.dict(os.environ, {"WEEX_AVAILABLE_FALLBACK_HAIRCUT": "0.98"}):
            with patch.object(client, 'send_weex_request', return_value=mock_response):
                with patch.object(client, 'get_pending_orders_cached', return_value=[]):
                    balance = client.get_account_balance()
                    assert balance is not None
                    # Available should be amount * haircut = 1000 * 0.98 = 980
                    assert abs(balance['available'] - 980.0) < 0.01, f"Expected available ~980.0, got {balance['available']}"
    
    def test_effective_available_during_cooldown(self):
        """Test that trades use effective_available during pending-orders cooldown"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Mock balance with available > 0 but liquid_capital = 0 (simulating cooldown)
        mock_balance = {
            'equity': 1000.0,
            'totalEquity': 1000.0,
            'available': 500.0,
            'availableBalance': 500.0,
            'liquidCapital': 0.0  # Liquid capital is 0 due to cooldown returning empty
        }
        
        with patch.object(bot.client, 'get_account_balance', return_value=mock_balance):
            # Use the actual helper method from the bot
            effective_available = bot.get_effective_available()
            
            # effective_available should be 500 (from available), NOT 0 (from liquidCapital)
            assert effective_available == 500.0, f"Expected effective_available=500.0, got {effective_available}"
            
            # The trade should NOT be blocked when effective_available > 0
            assert effective_available > 0.0, "Trade should not be blocked when available > 0 even if liquidCapital is 0"
    
    def test_effective_available_uses_liquid_capital_when_positive(self):
        """Test that effective_available uses liquid_capital when it's positive"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Mock balance with both available and liquid_capital > 0
        mock_balance = {
            'equity': 1000.0,
            'totalEquity': 1000.0,
            'available': 500.0,
            'availableBalance': 500.0,
            'liquidCapital': 350.0  # Liquid capital after deducting pending orders margin
        }
        
        with patch.object(bot.client, 'get_account_balance', return_value=mock_balance):
            # Use the actual helper method from the bot
            effective_available = bot.get_effective_available()
            
            # effective_available should be 350 (from liquidCapital, not available)
            assert effective_available == 350.0, f"Expected effective_available=350.0 (liquid_capital), got {effective_available}"


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
            # Mock get_account_balance with non-zero equity (10000) for proper exposure calculation
            with patch.object(bot.client, 'get_account_balance', return_value={'equity': 10000, 'availableBalance': '10000'}):
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
    
    def test_kill_switch_zero_division_protection(self, mock_env):
        """Test that check_kill_switch handles zero division gracefully"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        
        # Set initial equity to 0 to trigger potential division by zero
        bot.initial_equity = 0.0
        
        # Mock get_current_equity to return a value
        with patch.object(bot, 'get_current_equity', return_value=100.0):
            # This should not raise ZeroDivisionError
            result = bot.check_kill_switch()
            
            # Should return False (no kill switch) and not crash
            assert result is False
    
    def test_kill_switch_with_valid_equity(self, mock_env):
        """Test kill switch with valid equity values"""
        from competition_bot import CompetitionTradingBot
        
        bot = CompetitionTradingBot(test_mode=True)
        bot.initial_equity = 1000.0
        
        # Mock get_current_equity to return a value within acceptable range
        with patch.object(bot, 'get_current_equity', return_value=950.0):
            # No kill switch should be triggered (only 5% drawdown)
            result = bot.check_kill_switch()
            assert result is False
        
        # Mock get_current_equity to return a value that triggers kill switch
        with patch.object(bot, 'get_current_equity', return_value=850.0):
            with patch.object(bot, 'close_all_positions'):
                # Kill switch should be triggered (15% drawdown)
                result = bot.check_kill_switch()
                assert result is True
                assert bot.emergency_stop is True
        
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
    
    def test_margin_mode_cross(self):
        """Test Critical Fix: Margin mode is string "isolated" (required by WEEX V2 API)"""
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
            
            # Verify the endpoint was called with isolated margin mode (string format as required by V2 API)
            call_args = mock_post.call_args
            body_data = json.loads(call_args[1]['data'])
            assert body_data['marginMode'] == "isolated", "Margin mode should be string 'isolated' for V2 API"
            assert isinstance(body_data['marginMode'], str), "Margin mode should be string type"


class TestVolatilityBypass:
    """Test volatility bypass environment variable configuration"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv('API_KEY', 'test_key')
        monkeypatch.setenv('API_SECRET', 'test_secret')
        monkeypatch.setenv('API_PASSWORD', 'test_pass')
    
    def test_volatility_bypass_disabled_via_env(self, mock_env, monkeypatch):
        """Test WEEX_DISABLE_VOLATILITY_BYPASS=true disables volatility filter"""
        # Set the environment variable BEFORE importing
        monkeypatch.setenv('WEEX_DISABLE_VOLATILITY_BYPASS', 'true')
        
        # Force reimport to pick up new env var
        # Note: imports inside method are intentional due to module reload requirements
        import importlib
        import competition_bot
        importlib.reload(competition_bot)
        
        assert competition_bot.VOLATILITY_BYPASS_DISABLED is True
        
        # Reset to default and verify cleanup
        monkeypatch.delenv('WEEX_DISABLE_VOLATILITY_BYPASS', raising=False)
        importlib.reload(competition_bot)
        assert competition_bot.VOLATILITY_BYPASS_DISABLED is False, "Should reset to default after env var removed"
    
    def test_volatility_bypass_threshold_from_env(self, mock_env, monkeypatch):
        """Test VOLATILITY_BYPASS_PCT sets threshold from environment"""
        monkeypatch.setenv('VOLATILITY_BYPASS_PCT', '1.5')
        
        # Note: imports inside method are intentional due to module reload requirements
        import importlib
        import competition_bot
        importlib.reload(competition_bot)
        
        assert competition_bot.VOLATILITY_BYPASS_THRESHOLD == 1.5
        
        # Reset to default and verify cleanup
        monkeypatch.delenv('VOLATILITY_BYPASS_PCT', raising=False)
        importlib.reload(competition_bot)
        assert competition_bot.VOLATILITY_BYPASS_THRESHOLD == 0.33, "Should reset to default after env var removed"
    
    def test_volatility_bypass_default_values(self, mock_env, monkeypatch):
        """Test default values when env vars are not set"""
        # Ensure env vars are not set
        monkeypatch.delenv('WEEX_DISABLE_VOLATILITY_BYPASS', raising=False)
        monkeypatch.delenv('VOLATILITY_BYPASS_PCT', raising=False)
        
        # Note: imports inside method are intentional due to module reload requirements
        import importlib
        import competition_bot
        importlib.reload(competition_bot)
        
        assert competition_bot.VOLATILITY_BYPASS_DISABLED is False
        assert competition_bot.VOLATILITY_BYPASS_THRESHOLD == 0.33


class TestOrderLogging:
    """Test order placement logging for traceability"""
    
    def test_place_market_order_logs_attempt_and_result(self):
        """Test that place_market_order logs attempt and result"""
        import logging
        
        # Create client and clear any persisted state
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        client.active_symbols = set()  # Clear any persisted active symbols
        
        # Pre-populate contract map to avoid discovery calls
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = time.time()
        
        # Pre-populate symbol format cache
        client._symbol_format_cache[("/capi/v2/order/placeOrder", "BTCUSDT")] = "contract"
        client._symbol_format_cache_timestamp[("/capi/v2/order/placeOrder", "BTCUSDT")] = time.time()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': '00000',
            'data': {'orderId': 'test_order_123'},
            'success': True
        }
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch('core.weex_v2_client.logger') as mock_logger:
                result = client.place_market_order("BTCUSDT", "BUY", 0.001)
                
                # Verify "Placing order" log was called
                placing_calls = [call for call in mock_logger.info.call_args_list 
                               if '📤 Placing order' in str(call)]
                assert len(placing_calls) >= 1, "Should log placing order attempt"
                
                # Verify "Order placed" log was called
                placed_calls = [call for call in mock_logger.info.call_args_list 
                              if '📥 Order placed' in str(call)]
                assert len(placed_calls) >= 1, "Should log order placed result"


class TestVolatilityGuardBehavior:
    """Test volatility guard behavior (veto vs allow)"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv('API_KEY', 'test_key')
        monkeypatch.setenv('API_SECRET', 'test_secret')
        monkeypatch.setenv('API_PASSWORD', 'test_pass')
    
    def test_volatility_guard_vetoes_high_volatility(self, mock_env, monkeypatch, caplog):
        """Test that volatility guard vetoes trade when 5m change > threshold"""
        import importlib
        import logging
        
        # Set threshold to 0.33 and ensure bypass is NOT disabled
        monkeypatch.setenv('VOLATILITY_BYPASS_PCT', '0.33')
        monkeypatch.delenv('WEEX_DISABLE_VOLATILITY_BYPASS', raising=False)
        
        import competition_bot
        importlib.reload(competition_bot)
        
        # Verify settings
        assert competition_bot.VOLATILITY_BYPASS_THRESHOLD == 0.33
        assert competition_bot.VOLATILITY_BYPASS_DISABLED is False
        
        # Create mock bot with test mode
        with patch.object(competition_bot, 'WEEXv2Client'):
            with patch.object(competition_bot, 'AITradingLogger'):
                with patch.object(competition_bot, 'AILogEngine'):
                    with patch.object(competition_bot, 'DatabaseManager'):
                        with patch.object(competition_bot, 'FundingRateAnalyzer'):
                            with patch.object(competition_bot, 'TradeJournal'):
                                with patch.object(competition_bot, 'PositionStatePersistence'):
                                    bot = competition_bot.CompetitionTradingBot(use_llm=False, test_mode=True)
                                    
                                    # Mock client methods
                                    bot.client.get_market_klines = Mock(return_value=[
                                        # Simulating 5 klines where price change is 0.50% (> 0.33% threshold)
                                        ['', '', '', '', '100.00'],  # oldest
                                        ['', '', '', '', '100.10'],
                                        ['', '', '', '', '100.20'],
                                        ['', '', '', '', '100.30'],
                                        ['', '', '', '', '100.50'],  # newest (0.50% change)
                                    ])
                                    bot.client.has_open_position = Mock(return_value=False)
                                    
                                    # Mock signal to be BUY with high confidence
                                    bot.generate_signal = Mock(return_value={
                                        "action": "BUY",
                                        "confidence": 0.80,
                                        "reason": "Test signal"
                                    })
                                    
                                    bot.get_behavioral_tag = Mock(return_value="NORMAL")
                                    
                                    # Enable logging capture
                                    with caplog.at_level(logging.INFO):
                                        bot.process_symbol("BTCUSDT")
                                    
                                    # Check that the volatility guard log appears
                                    assert any("Skipping trade by volatility bypass" in record.message for record in caplog.records), \
                                        f"Should log volatility skip reason. Captured logs: {[r.message for r in caplog.records]}"
    
    def test_volatility_guard_allows_when_disabled(self, mock_env, monkeypatch, caplog):
        """Test that volatility filter is disabled when WEEX_DISABLE_VOLATILITY_BYPASS=true"""
        import importlib
        import logging
        
        # Disable volatility filter
        monkeypatch.setenv('WEEX_DISABLE_VOLATILITY_BYPASS', 'true')
        
        import competition_bot
        importlib.reload(competition_bot)
        
        assert competition_bot.VOLATILITY_BYPASS_DISABLED is True
        
        # Create mock bot with test mode
        with patch.object(competition_bot, 'WEEXv2Client'):
            with patch.object(competition_bot, 'AITradingLogger'):
                with patch.object(competition_bot, 'AILogEngine'):
                    with patch.object(competition_bot, 'DatabaseManager'):
                        with patch.object(competition_bot, 'FundingRateAnalyzer'):
                            with patch.object(competition_bot, 'TradeJournal'):
                                with patch.object(competition_bot, 'PositionStatePersistence'):
                                    bot = competition_bot.CompetitionTradingBot(use_llm=False, test_mode=True)
                                    
                                    # Mock client methods with HIGH volatility (would normally be vetoed)
                                    bot.client.get_market_klines = Mock(return_value=[
                                        ['', '', '', '', '100.00'],  # oldest
                                        ['', '', '', '', '100.10'],
                                        ['', '', '', '', '100.20'],
                                        ['', '', '', '', '100.30'],
                                        ['', '', '', '', '100.50'],  # newest (0.50% change > 0.33% threshold)
                                    ])
                                    bot.client.has_open_position = Mock(return_value=False)
                                    
                                    bot.generate_signal = Mock(return_value={
                                        "action": "HOLD",
                                        "confidence": 0.50,
                                        "reason": "Test hold signal"
                                    })
                                    
                                    bot.get_behavioral_tag = Mock(return_value="NORMAL")
                                    
                                    with caplog.at_level(logging.INFO):
                                        bot.process_symbol("BTCUSDT")
                                    
                                    # Should log that filter is disabled
                                    assert any("Volatility filter disabled" in record.message for record in caplog.records), \
                                        f"Should log that volatility filter is disabled. Captured logs: {[r.message for r in caplog.records]}"
                                    
                                    # Should NOT log volatility skip reason
                                    assert not any("Skipping trade by volatility bypass" in record.message for record in caplog.records), \
                                        "Should NOT log volatility skip when bypass is disabled"
        
        # Cleanup
        monkeypatch.delenv('WEEX_DISABLE_VOLATILITY_BYPASS', raising=False)
        importlib.reload(competition_bot)


class TestSkipReasonLogs:
    """Test that skip-reason logs are present and explicit"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv('API_KEY', 'test_key')
        monkeypatch.setenv('API_SECRET', 'test_secret')
        monkeypatch.setenv('API_PASSWORD', 'test_pass')
        # Disable volatility filter for these tests
        monkeypatch.setenv('WEEX_DISABLE_VOLATILITY_BYPASS', 'true')
    
    def test_effective_available_zero_skip_log(self, mock_env, monkeypatch, caplog):
        """Test skip-reason log when effective_available <= 0"""
        import importlib
        import logging
        
        import competition_bot
        importlib.reload(competition_bot)
        
        with patch.object(competition_bot, 'WEEXv2Client'):
            with patch.object(competition_bot, 'AITradingLogger'):
                with patch.object(competition_bot, 'AILogEngine'):
                    with patch.object(competition_bot, 'DatabaseManager'):
                        with patch.object(competition_bot, 'FundingRateAnalyzer'):
                            with patch.object(competition_bot, 'TradeJournal'):
                                with patch.object(competition_bot, 'PositionStatePersistence'):
                                    bot = competition_bot.CompetitionTradingBot(use_llm=False, test_mode=True)
                                    
                                    # Mock to trigger funds check failure
                                    bot.client.get_market_klines = Mock(return_value=[
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                    ])
                                    bot.client.has_open_position = Mock(return_value=False)
                                    bot.generate_signal = Mock(return_value={
                                        "action": "BUY",
                                        "confidence": 0.80,
                                        "reason": "Test buy"
                                    })
                                    bot.get_behavioral_tag = Mock(return_value="NORMAL")
                                    bot.calculate_total_exposure = Mock(return_value=0.0)
                                    # Return 0 available funds
                                    bot.get_effective_available = Mock(return_value=0.0)
                                    
                                    with caplog.at_level(logging.INFO):
                                        bot.process_symbol("BTCUSDT")
                                    
                                    # Check for effective_available skip log
                                    assert any("Skipped by available funds" in record.message or 
                                              "effective_available" in record.message.lower() or
                                              "available funds" in record.message for record in caplog.records), \
                                        f"Should log skip when effective_available=0. Logs: {[r.message for r in caplog.records]}"


class TestPassedAllGuardsLog:
    """Test that 'Passed all guards' log appears before order placement"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv('API_KEY', 'test_key')
        monkeypatch.setenv('API_SECRET', 'test_secret')
        monkeypatch.setenv('API_PASSWORD', 'test_pass')
        monkeypatch.setenv('WEEX_DISABLE_VOLATILITY_BYPASS', 'true')
    
    def test_passed_all_guards_log_before_buy(self, mock_env, monkeypatch, caplog):
        """Test that 'Passed all guards' is logged before placing BUY order"""
        import importlib
        import logging
        
        import competition_bot
        importlib.reload(competition_bot)
        
        with patch.object(competition_bot, 'WEEXv2Client'):
            with patch.object(competition_bot, 'AITradingLogger'):
                with patch.object(competition_bot, 'AILogEngine'):
                    with patch.object(competition_bot, 'DatabaseManager'):
                        with patch.object(competition_bot, 'FundingRateAnalyzer'):
                            with patch.object(competition_bot, 'TradeJournal'):
                                with patch.object(competition_bot, 'PositionStatePersistence'):
                                    bot = competition_bot.CompetitionTradingBot(use_llm=False, test_mode=True)
                                    
                                    # Mock successful order flow
                                    bot.client.get_market_klines = Mock(return_value=[
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                        ['', '', '', '', '100.00'],
                                    ])
                                    bot.client.has_open_position = Mock(return_value=False)
                                    bot.client.set_leverage = Mock(return_value=True)
                                    bot.client.place_market_order = Mock(return_value={
                                        'orderId': 'test_order_123',
                                        'code': '00000'
                                    })
                                    bot.generate_signal = Mock(return_value={
                                        "action": "BUY",
                                        "confidence": 0.80,
                                        "reason": "Test buy"
                                    })
                                    bot.get_behavioral_tag = Mock(return_value="NORMAL")
                                    bot.calculate_total_exposure = Mock(return_value=0.0)
                                    bot.get_effective_available = Mock(return_value=1000.0)
                                    bot.is_volume_spike = Mock(return_value=True)
                                    bot.analyze_market = Mock(return_value={'atr_pct': 1.5, 'rsi': 50})
                                    bot.calculate_position_size = Mock(return_value=0.001)
                                    
                                    with caplog.at_level(logging.INFO):
                                        bot.process_symbol("BTCUSDT")
                                    
                                    # Check for "Passed all guards" log
                                    assert any("Passed all guards" in record.message for record in caplog.records), \
                                        f"Should log 'Passed all guards' before placing order. Logs: {[r.message for r in caplog.records]}"


class TestOrderFailureLogging:
    """Test that order failures are logged properly"""
    
    def test_order_failure_logged_when_order_returns_none(self):
        """Test that order failure is logged when place_market_order returns None"""
        import logging
        
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        client.active_symbols = set()
        
        # Pre-populate contract map
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = time.time()
        
        # Pre-populate symbol format cache
        client._symbol_format_cache[("/capi/v2/order/placeOrder", "BTCUSDT")] = "contract"
        client._symbol_format_cache_timestamp[("/capi/v2/order/placeOrder", "BTCUSDT")] = time.time()
        
        # Mock failed response (non-200)
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.return_value = {'code': '40001', 'msg': 'Bad request'}
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch('core.weex_v2_client.logger') as mock_logger:
                result = client.place_market_order("BTCUSDT", "BUY", 0.001)
                
                # Order should return None
                assert result is None
                
                # Verify attempt log was called
                placing_calls = [call for call in mock_logger.info.call_args_list 
                               if '📤 Placing order' in str(call)]
                assert len(placing_calls) >= 1, "Should log placing order attempt"
    
    def test_order_failure_logged_when_response_has_error(self):
        """Test that order failure is logged when API returns error code"""
        import logging
        
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        client.active_symbols = set()
        
        # Pre-populate contract map
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = time.time()
        
        # Pre-populate symbol format cache
        client._symbol_format_cache[("/capi/v2/order/placeOrder", "BTCUSDT")] = "contract"
        client._symbol_format_cache_timestamp[("/capi/v2/order/placeOrder", "BTCUSDT")] = time.time()
        
        # Mock response with error code (200 but code != 00000)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': '40001',
            'msg': 'Insufficient balance'
        }
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with patch('core.weex_v2_client.logger') as mock_logger:
                result = client.place_market_order("BTCUSDT", "BUY", 0.001)
                
                # Order should return None
                assert result is None
                
                # Verify failure log was called
                fail_calls = [call for call in mock_logger.warning.call_args_list 
                             if 'Order failed' in str(call)]
                assert len(fail_calls) >= 1, f"Should log order failure. Warning calls: {mock_logger.warning.call_args_list}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
