#!/usr/bin/env python3
"""
Quick validation script to test WEEX API fixes.
Run: python validate_api_fixes.py

This script validates that the API endpoint fixes are working correctly.
It uses mock responses to test the client behavior without making real API calls.
"""
import os
import sys
from unittest.mock import Mock, patch
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.weex_v2_client import WEEXv2Client


def test_leverage_endpoint():
    """Test 1: Verify leverage endpoint uses correct path and body format"""
    print("🧪 Test 1: Leverage endpoint format...")
    
    client = WEEXv2Client("test_key", "test_secret", "test_pass")
    
    # Mock the session.post method instead of requests.post
    with patch.object(client.session, 'post') as mock_post:
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 0, 'success': True}
        mock_post.return_value = mock_response
        
        # Call set_leverage
        result = client.set_leverage("cmt_btcusdt", 10)
        
        # Verify the call was made
        if not mock_post.called:
            print("   ❌ FAILED: set_leverage did not make POST request")
            return False
        
        # Check the URL contains correct path
        call_args = mock_post.call_args
        url = call_args[0][0]
        
        if "/capi/v2/account/leverage" not in url:
            print(f"   ❌ FAILED: Wrong endpoint path: {url}")
            return False
        
        # Check body format
        body_data = json.loads(call_args[1]['data'])
        
        if body_data.get('symbol') != "cmt_btcusdt":
            print(f"   ❌ FAILED: Wrong symbol: {body_data.get('symbol')}")
            return False
        
        if body_data.get('marginMode') != "isolated":
            print(f"   ❌ FAILED: Missing or wrong marginMode: {body_data.get('marginMode')}")
            return False
        
        if body_data.get('leverage') != "10":
            print(f"   ❌ FAILED: Leverage should be string '10', got: {body_data.get('leverage')}")
            return False
        
        if not isinstance(body_data.get('leverage'), str):
            print(f"   ❌ FAILED: Leverage should be string type, got: {type(body_data.get('leverage'))}")
            return False
        
        if not result:
            print("   ❌ FAILED: set_leverage returned False")
            return False
        
        print("   ✅ PASSED: Leverage endpoint format correct")
        return True


def test_already_set_handling():
    """Test 2: Verify 'already set' message is handled as success"""
    print("🧪 Test 2: 'Already set' error handling...")
    
    client = WEEXv2Client("test_key", "test_secret", "test_pass")
    
    # Mock the session.post method instead of requests.post
    with patch.object(client.session, 'post') as mock_post:
        # Setup mock response with "already set" message
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 1,
            'message': 'Leverage already set to 10x',
            'success': False
        }
        mock_post.return_value = mock_response
        
        # Call set_leverage
        result = client.set_leverage("cmt_btcusdt", 10)
        
        if not result:
            print("   ❌ FAILED: 'already set' message should return True, got False")
            return False
        
        print("   ✅ PASSED: 'Already set' handled as success")
        return True


def test_granularity_parameter():
    """Test 3: Verify candles endpoint uses granularity parameter"""
    print("🧪 Test 3: Candles endpoint with granularity...")
    
    client = WEEXv2Client("test_key", "test_secret", "test_pass")
    
    # Mock the session.get method instead of requests.get
    with patch.object(client.session, 'get') as mock_get:
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            [1234567890, '50000', '51000', '49000', '50500', '100'],
            [1234567900, '50500', '51500', '50000', '51000', '150']
        ]
        mock_get.return_value = mock_response
        
        # Call get_market_klines
        klines = client.get_market_klines("cmt_btcusdt", "1m", limit=2)
        
        if not mock_get.called:
            print("   ❌ FAILED: get_market_klines did not make GET request")
            return False
        
        # Check the URL
        call_args = mock_get.call_args
        url = call_args[0][0]
        
        if "granularity=1m" not in url:
            print(f"   ❌ FAILED: URL should contain 'granularity=1m': {url}")
            return False
        
        if "interval=" in url:
            print(f"   ❌ FAILED: URL should not contain 'interval=': {url}")
            return False
        
        if len(klines) != 2:
            print(f"   ❌ FAILED: Expected 2 candles, got {len(klines)}")
            return False
        
        print("   ✅ PASSED: Candles endpoint uses granularity parameter")
        return True


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("WEEX API Fixes Validation")
    print("=" * 60)
    print()
    
    tests = [
        test_leverage_endpoint,
        test_already_set_handling,
        test_granularity_parameter
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All validation tests passed!")
        return 0
    else:
        print("❌ Some validation tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
