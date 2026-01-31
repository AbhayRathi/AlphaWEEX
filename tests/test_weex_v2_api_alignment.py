"""
Focused tests for WEEX V2 API alignment fixes.

Tests cover:
1. Symbol formatting (remove 'cmt_' prefix, convert to UPPERCASE)
2. Position parsing (handle list and dict formats)
3. Leverage endpoint path
4. Integer types for leverage and marginMode
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.weex_v2_client import WEEXv2Client


class TestSymbolCleaning:
    """Test symbol cleaning functionality"""
    
    def test_clean_symbol_with_cmt_prefix_lowercase(self):
        """Test cleaning symbol with cmt_ prefix in lowercase"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        result = client.clean_symbol("cmt_btcusdt")
        assert result == "BTCUSDT"
    
    def test_clean_symbol_with_cmt_prefix_mixed_case(self):
        """Test cleaning symbol with cmt_ prefix in mixed case"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        result = client.clean_symbol("cmt_BtcUsDt")
        assert result == "BTCUSDT"
    
    def test_clean_symbol_without_cmt_prefix(self):
        """Test cleaning symbol without cmt_ prefix"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        result = client.clean_symbol("BTCUSDT")
        assert result == "BTCUSDT"
    
    def test_clean_symbol_lowercase_no_prefix(self):
        """Test cleaning lowercase symbol without prefix"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        result = client.clean_symbol("ethusdt")
        assert result == "ETHUSDT"
    
    def test_clean_symbol_empty_string(self):
        """Test cleaning empty symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        result = client.clean_symbol("")
        assert result == ""
    
    def test_clean_symbol_none(self):
        """Test cleaning None symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        result = client.clean_symbol(None)
        assert result == ""
    
    def test_clean_symbol_multiple_symbols(self):
        """Test cleaning multiple different symbols"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        test_cases = [
            ("cmt_btcusdt", "BTCUSDT"),
            ("cmt_ethusdt", "ETHUSDT"),
            ("cmt_solusdt", "SOLUSDT"),
            ("cmt_dogeusdt", "DOGEUSDT"),
            ("cmt_xrpusdt", "XRPUSDT"),
        ]
        for input_symbol, expected_output in test_cases:
            assert client.clean_symbol(input_symbol) == expected_output


class TestSetLeverage:
    """Test set_leverage method with API alignment fixes"""
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_set_leverage_uses_clean_symbol(self, mock_send_request):
        """Test that set_leverage uses clean_symbol for API call"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "success": True}
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        result = client.set_leverage("cmt_btcusdt", leverage=20)
        
        # Verify the request was made
        assert mock_send_request.called
        call_args = mock_send_request.call_args
        
        # Check the body contains cleaned symbol (BTCUSDT, not cmt_btcusdt)
        body = call_args[1]['body']
        assert body['symbol'] == "BTCUSDT"
        assert body['leverage'] == "20"  # WEEX V2 API requires string format
        assert body['marginMode'] == "isolated"  # WEEX V2 API requires string format
        assert result is True
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_set_leverage_endpoint_path(self, mock_send_request):
        """Test that set_leverage uses correct endpoint path"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "success": True}
        mock_send_request.return_value = mock_response
        
        # Call set_leverage
        client.set_leverage("cmt_btcusdt", leverage=20)
        
        # Verify correct path is used
        call_args = mock_send_request.call_args
        path = call_args[0][1]  # Second positional argument
        assert path == "/capi/v2/account/setLeverage"
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_set_leverage_string_types(self, mock_send_request):
        """Test that leverage and marginMode are strings as required by WEEX V2 API"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "success": True}
        mock_send_request.return_value = mock_response
        
        # Call with various types
        client.set_leverage("cmt_btcusdt", leverage=20)
        
        # Check body contains strings as required by WEEX V2 API
        body = mock_send_request.call_args[1]['body']
        assert isinstance(body['leverage'], str)
        assert isinstance(body['marginMode'], str)
        assert body['marginMode'] == "isolated"


class TestHasOpenPosition:
    """Test has_open_position method with API alignment fixes"""
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_has_open_position_uses_clean_symbol(self, mock_send_request):
        """Test that has_open_position uses clean_symbol for API call"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response with list format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "BTCUSDT", "size": "0.1", "entryPrice": "50000", "side": "LONG"}
        ]
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        result = client.has_open_position("cmt_btcusdt")
        
        # Verify query param uses cleaned symbol
        call_args = mock_send_request.call_args
        query_params = call_args[0][2]  # Third positional argument
        assert "BTCUSDT" in query_params
        assert "cmt_" not in query_params
        assert result is True
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_has_open_position_handles_list_format(self, mock_send_request):
        """Test that has_open_position handles raw list response"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response as raw list (API V2 format)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"symbol": "BTCUSDT", "size": "0.1", "entryPrice": "50000", "side": "LONG"},
            {"symbol": "ETHUSDT", "size": "1.0", "entryPrice": "3000", "side": "SHORT"}
        ]
        mock_send_request.return_value = mock_response
        
        # Should find position
        result = client.has_open_position("cmt_btcusdt")
        assert result is True
        # Position is now stored with cleaned symbol key (BTCUSDT) after symbol overwrite
        assert "BTCUSDT" in client.open_positions
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_has_open_position_handles_dict_format(self, mock_send_request):
        """Test that has_open_position handles dict format fallback"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response as dict with 'data' key (fallback format)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": [
                {"symbol": "BTCUSDT", "size": "0.1", "entryPrice": "50000", "side": "LONG"}
            ]
        }
        mock_send_request.return_value = mock_response
        
        # Should find position
        result = client.has_open_position("cmt_btcusdt")
        assert result is True
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_has_open_position_no_position_found(self, mock_send_request):
        """Test has_open_position when no position exists"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock empty list response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_send_request.return_value = mock_response
        
        # Should not find position
        result = client.has_open_position("cmt_btcusdt")
        assert result is False
        assert "cmt_btcusdt" not in client.open_positions


class TestPlaceMarketOrder:
    """Test place_market_order method with API alignment fixes"""
    
    @patch.object(WEEXv2Client, 'check_spread')
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_place_market_order_uses_clean_symbol(self, mock_send_request, mock_check_spread):
        """Test that place_market_order uses clean_symbol for API call"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        # Clear any active symbols from previous tests
        client.active_symbols.clear()
        
        # Mock spread check
        mock_check_spread.return_value = True
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "success": True, "data": {"orderId": "123"}}
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        result = client.place_market_order("cmt_btcusdt", "BUY", 0.1)
        
        # Verify body contains cleaned symbol
        call_args = mock_send_request.call_args
        body = call_args[1]['body']
        assert body['symbol'] == "BTCUSDT"
        assert "cmt_" not in body['symbol']
        assert result is not None
    
    @patch.object(WEEXv2Client, 'check_spread')
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_place_market_order_payload_format(self, mock_send_request, mock_check_spread):
        """Test that place_market_order has correct payload format to avoid 40020 error"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        # Clear any active symbols from previous tests
        client.active_symbols.clear()
        
        # Mock spread check
        mock_check_spread.return_value = True
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "00000", "success": True, "data": {"orderId": "123"}}
        mock_send_request.return_value = mock_response
        
        # Call with a size value
        result = client.place_market_order("BTCUSDT", "BUY", 0.1234)
        
        # Verify payload format
        call_args = mock_send_request.call_args
        body = call_args[1]['body']
        
        # Ensure size is a string
        assert isinstance(body['size'], str), "size must be a string"
        assert body['size'] == "0.1234"
        
        # Ensure match_price is strictly the string "1"
        assert body['match_price'] == "1", "match_price must be the string '1'"
        assert isinstance(body['match_price'], str), "match_price must be a string"
        
        # Ensure type is strictly the string "1" (MARKET order type in V2)
        assert body['type'] == "1", "type must be the string '1' for MARKET orders"
        assert isinstance(body['type'], str), "type must be a string"
        
        assert result is not None


class TestMarketDataMethods:
    """Test market data methods use clean_symbol"""
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_market_klines_uses_clean_symbol(self, mock_send_request):
        """Test get_market_klines uses clean_symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        client.get_market_klines("cmt_btcusdt", interval="1m", limit=100)
        
        # Verify query params use cleaned symbol
        call_args = mock_send_request.call_args
        query_params = call_args[0][2]
        assert "BTCUSDT" in query_params
        assert "cmt_" not in query_params
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_funding_rate_uses_clean_symbol(self, mock_send_request):
        """Test get_funding_rate uses clean_symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "data": {"fundingRate": "0.0001"}}
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        client.get_funding_rate("cmt_ethusdt")
        
        # Verify query params use cleaned symbol
        call_args = mock_send_request.call_args
        query_params = call_args[0][2]
        assert "ETHUSDT" in query_params
        assert "cmt_" not in query_params
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_order_book_uses_clean_symbol(self, mock_send_request):
        """Test get_order_book uses clean_symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "data": {"bids": [], "asks": []}}
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        client.get_order_book("cmt_solusdt", depth=5)
        
        # Verify query params use cleaned symbol
        call_args = mock_send_request.call_args
        query_params = call_args[0][2]
        assert "SOLUSDT" in query_params
        assert "cmt_" not in query_params
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_ticker_uses_clean_symbol(self, mock_send_request):
        """Test get_ticker uses clean_symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "data": {"last": "50000"}}
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        client.get_ticker("cmt_xrpusdt")
        
        # Verify query params use cleaned symbol
        call_args = mock_send_request.call_args
        query_params = call_args[0][2]
        assert "XRPUSDT" in query_params
        assert "cmt_" not in query_params


class TestGetAccountAssets:
    """Test get_account_assets method with V2 API format"""
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_account_assets_success(self, mock_send_request):
        """Test get_account_assets with successful V2 response"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock V2 response format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "data": [
                {
                    "coinName": "BTC",
                    "equity": "0.5",
                    "available": "0.4"
                },
                {
                    "coinName": "USDT",
                    "equity": "887.61",
                    "available": "500.00"
                }
            ]
        }
        mock_send_request.return_value = mock_response
        
        # Call method
        result = client.get_account_assets()
        
        # Verify correct endpoint was called (Official WEEX V2 Contract API)
        call_args = mock_send_request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/capi/v2/account/getAccounts"
        
        # Verify correct value returned (equity for USDT)
        assert result == 887.61
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_account_assets_missing_equity(self, mock_send_request):
        """Test get_account_assets returns 0.0 when equity is missing (Alpha-Evo Final: no fallback)"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock V2 response without equity field
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "data": [
                {
                    "coinName": "USDT",
                    "available": "750.25"
                }
            ]
        }
        mock_send_request.return_value = mock_response
        
        # Call method
        result = client.get_account_assets()
        
        # Verify returns 0.0 when equity is missing (no fallback to available)
        assert result == 0.0
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_account_assets_no_usdt(self, mock_send_request):
        """Test get_account_assets returns 0.0 when USDT not found"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock V2 response without USDT
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "data": [
                {
                    "coinName": "BTC",
                    "equity": "0.5"
                }
            ]
        }
        mock_send_request.return_value = mock_response
        
        # Call method
        result = client.get_account_assets()
        
        # Verify returns 0.0
        assert result == 0.0
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_account_assets_error_code(self, mock_send_request):
        """Test get_account_assets returns 0.0 on error code"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock V2 response with error code
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "40001",
            "msg": "Error"
        }
        mock_send_request.return_value = mock_response
        
        # Call method
        result = client.get_account_assets()
        
        # Verify returns 0.0
        assert result == 0.0
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_account_assets_exception(self, mock_send_request):
        """Test get_account_assets handles exceptions gracefully"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock exception
        mock_send_request.side_effect = Exception("Network error")
        
        # Call method
        result = client.get_account_assets()
        
        # Verify returns 0.0 on exception
        assert result == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
