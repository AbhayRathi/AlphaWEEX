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
