"""
Focused tests for WEEX V2 API alignment fixes.

Tests cover:
1. Symbol formatting (remove 'cmt_' prefix, convert to UPPERCASE)
2. Position parsing (handle list and dict formats)
3. Leverage endpoint path
4. Integer types for leverage and marginMode
"""
import os
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
    @patch.object(WEEXv2Client, 'resolve_contract_symbol')
    def test_set_leverage_uses_clean_symbol(self, mock_resolve, mock_send_request):
        """Test that set_leverage uses resolved symbol for API call"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock symbol resolution
        mock_resolve.return_value = "BTCUSDT_UMCBL"
        
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
        
        # Check the body contains resolved symbol (BTCUSDT_UMCBL)
        body = call_args[1]['body']
        assert body['symbol'] == "BTCUSDT_UMCBL"
        assert body['leverage'] == "20"  # WEEX V2 API requires string format
        assert body['marginMode'] == "isolated"  # WEEX V2 API requires string format
        assert result is True
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    @patch.object(WEEXv2Client, 'resolve_contract_symbol')
    def test_set_leverage_endpoint_path(self, mock_resolve, mock_send_request):
        """Test that set_leverage uses correct endpoint path"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock symbol resolution
        mock_resolve.return_value = "BTCUSDT_UMCBL"
        
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
    @patch.object(WEEXv2Client, 'resolve_contract_symbol')
    def test_place_market_order_uses_clean_symbol(self, mock_resolve, mock_send_request, mock_check_spread):
        """Test that place_market_order uses resolved symbol for API call"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        # Clear any active symbols from previous tests
        client.active_symbols.clear()
        
        # Mock symbol resolution
        mock_resolve.return_value = "BTCUSDT_UMCBL"
        
        # Mock spread check
        mock_check_spread.return_value = True
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "success": True, "data": {"orderId": "123"}}
        mock_send_request.return_value = mock_response
        
        # Call with cmt_ prefix
        result = client.place_market_order("cmt_btcusdt", "BUY", 0.1)
        
        # Verify body contains resolved symbol
        call_args = mock_send_request.call_args
        body = call_args[1]['body']
        assert body['symbol'] == "BTCUSDT_UMCBL"
        assert "cmt_" not in body['symbol']
        assert result is not None
    
    @patch.object(WEEXv2Client, 'check_spread')
    @patch.object(WEEXv2Client, 'send_weex_request')
    @patch.object(WEEXv2Client, 'resolve_contract_symbol')
    def test_place_market_order_payload_format(self, mock_resolve, mock_send_request, mock_check_spread):
        """Test that place_market_order has correct payload format to avoid 40020 error"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        # Clear any active symbols from previous tests
        client.active_symbols.clear()
        
        # Mock symbol resolution
        mock_resolve.return_value = "BTCUSDT_UMCBL"
        
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
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_account_assets_list_response(self, mock_send_request):
        """Test get_account_assets with direct list response format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock direct list response format (no dict wrapper)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "coinName": "BTC",
                "equity": "0.5",
                "available": "0.4"
            },
            {
                "coinName": "USDT",
                "equity": "1250.75",
                "available": "900.00"
            }
        ]
        mock_send_request.return_value = mock_response
        
        # Call method
        result = client.get_account_assets()
        
        # Verify correct value returned (equity for USDT)
        assert result == 1250.75
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_get_account_assets_list_response_no_usdt(self, mock_send_request):
        """Test get_account_assets returns 0.0 when list response has no USDT"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock direct list response without USDT
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "coinName": "BTC",
                "equity": "0.5"
            },
            {
                "coinName": "ETH",
                "equity": "10.0"
            }
        ]
        mock_send_request.return_value = mock_response
        
        # Call method
        result = client.get_account_assets()
        
        # Verify returns 0.0 when USDT not found
        assert result == 0.0


class TestPendingOrdersCache:
    """Test pending-orders TTL cache and cooldown-aware reuse"""
    
    def test_pending_orders_cache_uses_snapshot_on_cooldown(self):
        """Test that get_pending_orders_cached reuses cached snapshot on cooldown error"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Seed cache with a fake snapshot
        fake_snapshot = {"data": {"positions": [{"initialMargin": "10.5"}]}}
        client._cache_put("pending-orders:umcbl", fake_snapshot)
        
        # Simulate send_weex_request raising "Cooldown active" exception
        with patch.object(WEEXv2Client, 'send_weex_request') as mock_send:
            mock_send.side_effect = Exception("Cooldown active for /capi/v2/positions/pending-orders: 15.2s remaining")
            
            # Should return cached snapshot (no exception raised)
            result = client.get_pending_orders_cached(productType="umcbl")
            
            assert result == fake_snapshot
            assert result["data"]["positions"][0]["initialMargin"] == "10.5"
    
    def test_pending_orders_cache_returns_empty_on_error_without_cache(self):
        """Test that get_pending_orders_cached returns empty list on error with no cache"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # No cache seeded - should return empty list on error
        with patch.object(WEEXv2Client, 'send_weex_request') as mock_send:
            mock_send.side_effect = Exception("Network error")
            
            result = client.get_pending_orders_cached(productType="umcbl")
            
            assert result == []
    
    def test_pending_orders_cache_stores_on_success(self):
        """Test that successful fetch stores data in cache"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"positions": [{"initialMargin": "25.0"}]}}
        
        with patch.object(WEEXv2Client, 'send_weex_request') as mock_send:
            mock_send.return_value = mock_response
            
            result = client.get_pending_orders_cached(productType="umcbl")
            
            assert result == {"data": {"positions": [{"initialMargin": "25.0"}]}}
            
            # Verify cache was populated
            cached = client._cache_get("pending-orders:umcbl")
            assert cached == {"data": {"positions": [{"initialMargin": "25.0"}]}}
    
    def test_pending_orders_cache_ttl_expiry(self):
        """Test that cache expires after TTL"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        client._pending_orders_ttl = 0.1  # 100ms TTL for testing
        
        # Seed cache
        client._cache_put("pending-orders:umcbl", {"test": "data"})
        
        # Should return cached data immediately
        assert client._cache_get("pending-orders:umcbl") == {"test": "data"}
        
        # Wait for TTL to expire
        import time
        time.sleep(0.15)
        
        # Should return None after expiry
        assert client._cache_get("pending-orders:umcbl") is None


class TestLiquidCapitalTolerantShapes:
    """Test _calculate_liquid_capital with various response shapes"""
    
    def test_liquid_capital_dict_with_data_positions(self):
        """Test liquid capital with dict containing data.positions shape"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock get_pending_orders_cached to return dict with data.positions
        with patch.object(WEEXv2Client, 'get_pending_orders_cached') as mock_cached:
            mock_cached.return_value = {
                "data": {
                    "positions": [
                        {"initialMargin": "10.0"},
                        {"initialMargin": "15.5"}
                    ]
                }
            }
            
            result = client._calculate_liquid_capital(100.0)
            
            # 100.0 - (10.0 + 15.5) = 74.5
            assert result == 74.5
    
    def test_liquid_capital_list_format(self):
        """Test liquid capital with raw list response format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock get_pending_orders_cached to return list directly
        with patch.object(WEEXv2Client, 'get_pending_orders_cached') as mock_cached:
            mock_cached.return_value = [
                {"initialMargin": "5.0"},
                {"initMargin": "3.5"}  # Different field name
            ]
            
            result = client._calculate_liquid_capital(50.0)
            
            # 50.0 - (5.0 + 3.5) = 41.5
            assert result == 41.5
    
    def test_liquid_capital_dict_with_positions_key(self):
        """Test liquid capital with dict containing positions key directly"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        with patch.object(WEEXv2Client, 'get_pending_orders_cached') as mock_cached:
            mock_cached.return_value = {
                "positions": [
                    {"margin": "8.0"}  # Uses 'margin' field name
                ]
            }
            
            result = client._calculate_liquid_capital(30.0)
            
            # 30.0 - 8.0 = 22.0
            assert result == 22.0
    
    def test_liquid_capital_clamps_to_zero(self):
        """Test liquid capital never returns negative"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        with patch.object(WEEXv2Client, 'get_pending_orders_cached') as mock_cached:
            mock_cached.return_value = [
                {"initialMargin": "200.0"}  # More than available
            ]
            
            result = client._calculate_liquid_capital(100.0)
            
            # Should clamp to 0, not -100
            assert result == 0.0
    
    def test_liquid_capital_fallback_on_error(self):
        """Test liquid capital returns available on error"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        with patch.object(WEEXv2Client, 'get_pending_orders_cached') as mock_cached:
            mock_cached.side_effect = Exception("Unexpected error")
            
            result = client._calculate_liquid_capital(75.0)
            
            # Should fallback to available balance
            assert result == 75.0
    
    def test_liquid_capital_disabled_via_env(self):
        """Test liquid capital can be disabled via environment variable"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        with patch.dict('os.environ', {'WEEX_DISABLE_LIQUID_CAPITAL': 'true'}):
            # Should return available directly without calling pending-orders
            with patch.object(WEEXv2Client, 'get_pending_orders_cached') as mock_cached:
                result = client._calculate_liquid_capital(100.0)
                
                # Should not call get_pending_orders_cached
                mock_cached.assert_not_called()
                
                # Should return available directly
                assert result == 100.0
    
    def test_liquid_capital_handles_empty_positions(self):
        """Test liquid capital handles empty positions list"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        with patch.object(WEEXv2Client, 'get_pending_orders_cached') as mock_cached:
            mock_cached.return_value = {"data": {"positions": []}}
            
            result = client._calculate_liquid_capital(50.0)
            
            # No positions = no reserved margin
            assert result == 50.0


class TestJitterEnvConfiguration:
    """Test that jitter values are configurable via environment variables"""
    
    def test_jitter_defaults(self):
        """Test default jitter values when env vars not set"""
        # Save original values
        orig_min = os.environ.pop('WEEX_521_MIN_JITTER', None)
        orig_max = os.environ.pop('WEEX_521_MAX_JITTER', None)
        
        try:
            client = WEEXv2Client("test_key", "test_secret", "test_pass")
            
            assert client._jitter_min == 5.0
            assert client._jitter_max == 25.0
        finally:
            # Restore original values if they existed
            if orig_min is not None:
                os.environ['WEEX_521_MIN_JITTER'] = orig_min
            if orig_max is not None:
                os.environ['WEEX_521_MAX_JITTER'] = orig_max
    
    def test_jitter_from_env(self):
        """Test jitter values from environment variables"""
        with patch.dict('os.environ', {
            'WEEX_521_MIN_JITTER': '3.0',
            'WEEX_521_MAX_JITTER': '15.0'
        }):
            client = WEEXv2Client("test_key", "test_secret", "test_pass")
            
            assert client._jitter_min == 3.0
            assert client._jitter_max == 15.0
    
    def test_pending_orders_ttl_from_env(self):
        """Test pending orders TTL from environment variable"""
        with patch.dict('os.environ', {'WEEX_PENDING_ORDERS_TTL': '30'}):
            client = WEEXv2Client("test_key", "test_secret", "test_pass")
            
            assert client._pending_orders_ttl == 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
