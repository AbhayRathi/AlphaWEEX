"""
Tests for symbol resolution and contract discovery functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.weex_v2_client import WEEXv2Client


class TestContractDiscovery:
    """Test contract discovery and symbol resolution"""
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_load_contracts_success_market_endpoint(self, mock_send_request):
        """Test successful contract loading from market endpoint"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock successful response with contract data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "data": [
                {
                    "symbol": "BTCUSDT_UMCBL",
                    "baseCoin": "BTC",
                    "quoteCoin": "USDT"
                },
                {
                    "symbol": "ETHUSDT_UMCBL",
                    "baseCoin": "ETH",
                    "quoteCoin": "USDT"
                }
            ]
        }
        mock_send_request.return_value = mock_response
        
        # Load contracts
        contract_map = client.load_contracts()
        
        # Verify mapping
        assert "BTCUSDT" in contract_map
        assert contract_map["BTCUSDT"] == "BTCUSDT_UMCBL"
        assert "ETHUSDT" in contract_map
        assert contract_map["ETHUSDT"] == "ETHUSDT_UMCBL"
        
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_load_contracts_fallback_to_public_endpoint(self, mock_send_request):
        """Test fallback to public endpoint when market endpoint fails"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 404
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "code": "00000",
            "data": [
                {
                    "symbol": "SOLUSDT_UMCBL",
                    "baseCoin": "SOL",
                    "quoteCoin": "USDT"
                }
            ]
        }
        
        mock_send_request.side_effect = [mock_response_fail, mock_response_success]
        
        # Load contracts
        contract_map = client.load_contracts()
        
        # Verify mapping from second endpoint
        assert "SOLUSDT" in contract_map
        assert contract_map["SOLUSDT"] == "SOLUSDT_UMCBL"
        
    @patch.object(WEEXv2Client, 'send_weex_request')
    def test_load_contracts_handles_direct_list_response(self, mock_send_request):
        """Test handling of direct list response (no 'data' wrapper)"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock response with direct list (no data wrapper)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "symbol": "BTCUSDT_UMCBL",
                "baseCoin": "BTC",
                "quoteCoin": "USDT"
            }
        ]
        mock_send_request.return_value = mock_response
        
        # Load contracts
        contract_map = client.load_contracts()
        
        # Verify mapping
        assert "BTCUSDT" in contract_map
        assert contract_map["BTCUSDT"] == "BTCUSDT_UMCBL"
        
    def test_resolve_contract_symbol_with_mapping(self):
        """Test symbol resolution when mapping exists"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map
        client._contract_map = {
            "BTCUSDT": "BTCUSDT_UMCBL",
            "ETHUSDT": "ETHUSDT_UMCBL"
        }
        client._contract_map_timestamp = 999999999999  # Far future
        
        # Test resolution
        assert client.resolve_contract_symbol("BTCUSDT") == "BTCUSDT_UMCBL"
        assert client.resolve_contract_symbol("cmt_btcusdt") == "BTCUSDT_UMCBL"
        assert client.resolve_contract_symbol("btcusdt") == "BTCUSDT_UMCBL"
        
    def test_resolve_contract_symbol_fallback(self):
        """Test symbol resolution with fallback when no mapping exists"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Empty contract map
        client._contract_map = {}
        client._contract_map_timestamp = 999999999999  # Far future
        
        # Test fallback resolution
        result = client.resolve_contract_symbol("XRPUSDT")
        assert result == "XRPUSDT_UMCBL"  # Default fallback
        
    @patch.object(WEEXv2Client, 'load_contracts')
    def test_resolve_contract_symbol_loads_contracts_when_needed(self, mock_load):
        """Test that resolve_contract_symbol loads contracts if map is empty"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Clear contract map to force loading
        client._contract_map = {}
        client._contract_map_timestamp = 0
        
        # Mock load_contracts to populate the map
        def populate_map():
            client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
            client._contract_map_timestamp = 999999999999
            return client._contract_map
        
        mock_load.side_effect = populate_map
        
        # Resolve symbol - should trigger load_contracts
        result = client.resolve_contract_symbol("BTCUSDT")
        
        # Verify load_contracts was called
        mock_load.assert_called_once()
        assert result == "BTCUSDT_UMCBL"


class TestSymbolResolutionInMethods:
    """Test that methods use resolved symbols"""
    
    @patch.object(WEEXv2Client, 'send_weex_request')
    @patch.object(WEEXv2Client, 'resolve_contract_symbol')
    def test_get_market_klines_uses_resolved_symbol(self, mock_resolve, mock_send_request):
        """Test that get_market_klines uses resolved symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Mock resolution
        mock_resolve.return_value = "BTCUSDT_UMCBL"
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "data": [
                [1234567890, "50000", "51000", "49000", "50500", "100"]
            ]
        }
        mock_send_request.return_value = mock_response
        
        # Call method
        client.get_market_klines("BTCUSDT")
        
        # Verify resolve was called
        mock_resolve.assert_called_once_with("BTCUSDT")
        
    @patch.object(WEEXv2Client, 'send_weex_request')
    @patch.object(WEEXv2Client, 'resolve_contract_symbol')
    def test_place_market_order_uses_resolved_symbol(self, mock_resolve, mock_send_request):
        """Test that place_market_order uses resolved symbol"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Clear active symbols to avoid AI Wars check
        client.active_symbols = set()
        
        # Mock resolution
        mock_resolve.return_value = "ETHUSDT_UMCBL"
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "00000",
            "order_id": "12345"
        }
        mock_send_request.return_value = mock_response
        
        # Call method
        client.place_market_order("ETHUSDT", "BUY", 0.01)
        
        # Verify resolve was called
        mock_resolve.assert_called_once_with("ETHUSDT")
        
        # Verify the resolved symbol was used in the request body
        call_args = mock_send_request.call_args
        body = call_args[1]['body']
        assert body['symbol'] == "ETHUSDT_UMCBL", "Resolved symbol should be used in API request"


class TestCentralSymbolRewrite:
    """Test central symbol rewrite in send_weex_request"""
    
    def test_symbol_rewrite_payload_and_query(self):
        """Test that send_weex_request rewrites symbols in payload and query params"""
        from unittest.mock import Mock, patch
        
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map to avoid network calls
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        # Mock the session to capture the actual request
        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"code": "00000"}
            mock_post.return_value = mock_response
            
            # Test payload rewrite
            response = client.send_weex_request(
                "POST", 
                "/capi/v2/order/placeOrder",
                body={"symbol": "BTCUSDT", "size": "0.01"}
            )
            
            # Verify the symbol was rewritten in the request body
            call_args = mock_post.call_args
            body_str = call_args[1]['data']
            assert "BTCUSDT_UMCBL" in body_str, f"Symbol should be rewritten to contract format, got: {body_str}"
    
    def test_symbol_rewrite_query_params(self):
        """Test that send_weex_request rewrites symbols in query parameters"""
        from unittest.mock import Mock, patch
        
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"code": "00000", "data": []}
            mock_get.return_value = mock_response
            
            # Test query param rewrite
            response = client.send_weex_request(
                "GET", 
                "/capi/v2/market/candles",
                query_params="?symbol=BTCUSDT&interval=1m"
            )
            
            # Verify the URL contains the rewritten symbol
            call_args = mock_get.call_args
            url = call_args[0][0]  # First positional arg is URL
            assert "BTCUSDT_UMCBL" in url, f"Symbol in URL should be rewritten to contract format, got: {url}"


class TestSymbolFormatFallback:
    """Test 40020 error fallback handling"""
    
    def test_40020_fallback_to_cmt(self):
        """Test that 40020 error triggers fallback to cmt_ format"""
        from unittest.mock import Mock, patch, call
        import json
        
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        # Create mock responses: first fails with 40020, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 400
        mock_response_fail.json.return_value = {"code": "40020", "msg": "Parameter symbol is invalid"}
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"code": "00000", "order_id": "12345"}
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = [mock_response_fail, mock_response_success]
            
            response = client.send_weex_request(
                "POST",
                "/capi/v2/order/placeOrder",
                body={"symbol": "BTCUSDT", "size": "0.01"}
            )
            
            # Verify we got the success response
            assert response.status_code == 200
            
            # Verify cache was updated with 'cmt' format
            cache_key = ("/capi/v2/order/placeOrder", "BTCUSDT")
            assert cache_key in client._symbol_format_cache
            assert client._symbol_format_cache[cache_key] == "cmt"
            
            # Verify second call used cmt_ format
            second_call = mock_post.call_args_list[1]
            body_str = second_call[1]['data']
            assert "cmt_btcusdt" in body_str, f"Second attempt should use cmt_ format, got: {body_str}"
    
    def test_cache_applied(self):
        """Test that cached format is used for subsequent calls"""
        from unittest.mock import Mock, patch
        
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        # Pre-seed the cache with 'cmt' format
        import time
        cache_key = ("/capi/v2/order/placeOrder", "BTCUSDT")
        client._symbol_format_cache[cache_key] = "cmt"
        client._symbol_format_cache_timestamp[cache_key] = time.time()
        
        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"code": "00000", "order_id": "12345"}
            mock_post.return_value = mock_response
            
            response = client.send_weex_request(
                "POST",
                "/capi/v2/order/placeOrder",
                body={"symbol": "BTCUSDT", "size": "0.01"}
            )
            
            # Verify only one call was made (no fallback needed)
            assert mock_post.call_count == 1
            
            # Verify cached cmt_ format was used immediately
            call_args = mock_post.call_args
            body_str = call_args[1]['data']
            assert "cmt_btcusdt" in body_str, f"Cached cmt_ format should be used, got: {body_str}"
    
    def test_non_symbol_400_no_retry(self):
        """Test that non-40020 400 errors don't trigger symbol fallback"""
        from unittest.mock import Mock, patch
        
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        # Create mock response with non-40020 error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"code": "40001", "msg": "Invalid parameter"}
        
        with patch.object(client.session, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            response = client.send_weex_request(
                "POST",
                "/capi/v2/order/placeOrder",
                body={"symbol": "BTCUSDT", "size": "0.01"}
            )
            
            # Verify only one call was made (no fallback)
            assert mock_post.call_count == 1
            
            # Verify we got the error response back
            assert response.status_code == 400
            
    def test_symbol_format_hint_loading(self):
        """Test WEEX_SYMBOL_FORMAT_HINT environment variable loading"""
        import os
        from unittest.mock import patch
        
        hint_json = '{"path":"/capi/v2/order/placeOrder","symbol":"BTCUSDT","format":"cmt"}'
        
        with patch.dict(os.environ, {"WEEX_SYMBOL_FORMAT_HINT": hint_json}):
            client = WEEXv2Client("test_key", "test_secret", "test_pass")
            
            # Verify the hint was loaded into cache
            cache_key = ("/capi/v2/order/placeOrder", "BTCUSDT")
            assert cache_key in client._symbol_format_cache
            assert client._symbol_format_cache[cache_key] == "cmt"


class TestSymbolHelperMethods:
    """Test symbol format helper methods"""
    
    def test_path_base(self):
        """Test _path_base extracts path without query string"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        assert client._path_base("/capi/v2/order/placeOrder") == "/capi/v2/order/placeOrder"
        assert client._path_base("/capi/v2/market/candles?symbol=BTC") == "/capi/v2/market/candles"
        assert client._path_base("/api?a=1&b=2") == "/api"
    
    def test_to_cmt(self):
        """Test _to_cmt converts to legacy cmt_ format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        assert client._to_cmt("BTCUSDT") == "cmt_btcusdt"
        assert client._to_cmt("btcusdt") == "cmt_btcusdt"
        assert client._to_cmt("ETHUSDT") == "cmt_ethusdt"
    
    def test_to_plain(self):
        """Test _to_plain converts to uppercase and strips exchange suffixes"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        assert client._to_plain("btcusdt") == "BTCUSDT"
        assert client._to_plain("BTCUSDT") == "BTCUSDT"
        assert client._to_plain("cmt_btcusdt") == "BTCUSDT"
        # Test stripping exchange suffixes (verifies clean_symbol integration)
        assert client._to_plain("BTCUSDT_UMCBL") == "BTCUSDT"
        assert client._to_plain("ETHUSDT-PERP") == "ETHUSDT"
        assert client._to_plain("SOLUSDT_PERP") == "SOLUSDT"
    
    def test_encode_symbol(self):
        """Test _encode_symbol encodes to specified format"""
        client = WEEXv2Client("test_key", "test_secret", "test_pass")
        
        # Pre-populate contract map
        client._contract_map = {"BTCUSDT": "BTCUSDT_UMCBL"}
        client._contract_map_timestamp = 999999999999
        
        assert client._encode_symbol("BTCUSDT", "contract") == "BTCUSDT_UMCBL"
        assert client._encode_symbol("BTCUSDT", "cmt") == "cmt_btcusdt"
        assert client._encode_symbol("BTCUSDT", "plain") == "BTCUSDT"
