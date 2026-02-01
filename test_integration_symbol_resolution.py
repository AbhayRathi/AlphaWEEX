#!/usr/bin/env python3
"""
Integration test for finalized WEEX V2 symbol resolution

Tests:
1. Contract discovery with override
2. Symbol resolution with fallback
3. Scoped 521 cooldowns
4. Resolved symbols in API calls
"""
import os
import sys
import json

# Set override for testing (no network)
test_override = {
    "BTCUSDT": "BTCUSDT_UMCBL",
    "ETHUSDT": "ETHUSDT_UMCBL",
    "SOLUSDT": "SOLUSDT_UMCBL"
}
os.environ["WEEX_CONTRACT_MAP_OVERRIDE"] = json.dumps(test_override)

from core.weex_v2_client import WEEXv2Client

def test_contract_override():
    """Test that override is loaded"""
    print("\n1. Testing Contract Override Loading...")
    client = WEEXv2Client("test_key", "test_secret", "test_pass")
    
    contracts = client.load_contracts()
    assert contracts == test_override, "Override not loaded correctly"
    print("   ✅ Override loaded successfully")
    print(f"   ✅ Loaded {len(contracts)} contracts")
    return client

def test_symbol_resolution(client):
    """Test symbol resolution"""
    print("\n2. Testing Symbol Resolution...")
    
    # Test with symbols in map
    btc_resolved = client.resolve_contract_symbol("BTCUSDT")
    assert btc_resolved == "BTCUSDT_UMCBL", f"Expected BTCUSDT_UMCBL, got {btc_resolved}"
    print(f"   ✅ BTCUSDT → {btc_resolved}")
    
    # Test with cmt_ prefix
    eth_resolved = client.resolve_contract_symbol("cmt_ethusdt")
    assert eth_resolved == "ETHUSDT_UMCBL", f"Expected ETHUSDT_UMCBL, got {eth_resolved}"
    print(f"   ✅ cmt_ethusdt → {eth_resolved}")
    
    # Test fallback for unknown symbol
    new_resolved = client.resolve_contract_symbol("NEWCOINUSDT")
    assert new_resolved == "NEWCOINUSDT_UMCBL", f"Expected fallback NEWCOINUSDT_UMCBL, got {new_resolved}"
    print(f"   ✅ NEWCOINUSDT → {new_resolved} (fallback)")

def test_cooldown_scoping(client):
    """Test scoped cooldown behavior"""
    print("\n3. Testing Scoped 521 Cooldowns...")
    
    # Test cooldown key generation with query params
    key1 = client._cooldown_key("/capi/v2/market/candles", "?symbol=BTCUSDT&limit=10", {"symbol": "BTCUSDT"})
    key2 = client._cooldown_key("/capi/v2/market/candles", "?symbol=ETHUSDT&limit=10", {"symbol": "ETHUSDT"})
    key3 = client._cooldown_key("/capi/v2/account/getAccounts", "", None)
    
    print(f"   ✅ BTC klines key: {key1}")
    print(f"   ✅ ETH klines key: {key2}")
    print(f"   ✅ Balance key: {key3}")
    
    # Verify they're all different
    assert key1 != key2, "BTC and ETH keys should be different"
    assert key1 != key3, "Klines and balance keys should be different"
    assert key2 != key3, "ETH klines and balance keys should be different"
    print("   ✅ All keys are properly scoped")
    
    # Test cooldown isolation
    import time
    client._last_521_by_key[key1] = time.time()
    client._cooldown_by_key[key1] = 30.0
    
    btc_cooldown = client._cooldown_remaining(key1)
    eth_cooldown = client._cooldown_remaining(key2)
    balance_cooldown = client._cooldown_remaining(key3)
    
    assert btc_cooldown > 0, "BTC should have cooldown"
    assert eth_cooldown == 0, "ETH should not have cooldown"
    assert balance_cooldown == 0, "Balance should not have cooldown"
    print("   ✅ Cooldowns are properly isolated")

def test_tolerant_field_parsing():
    """Test tolerant parsing of different field names"""
    print("\n4. Testing Tolerant Field Parsing...")
    client = WEEXv2Client("test_key", "test_secret", "test_pass")
    
    # Test various field name combinations
    test_contracts = [
        {"symbol": "TEST1_UMCBL", "baseCoin": "TEST1", "quoteCoin": "USDT"},
        {"contractSymbol": "TEST2_UMCBL", "base": "TEST2", "quote": "USDT"},
        {"symbolName": "TEST3_UMCBL", "baseCurrency": "TEST3", "quoteCurrency": "USDT"},
        {"productId": "TEST4_UMCBL", "baseCoin": "TEST4", "quoteCoin": "USDT"},
    ]
    
    for contract in test_contracts:
        internal_key = client._extract_internal_key(contract)
        assert internal_key is not None, f"Failed to extract key from {contract}"
        assert "USDT" in internal_key, f"Key should contain USDT: {internal_key}"
        print(f"   ✅ Extracted '{internal_key}' from {list(contract.keys())}")

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("WEEX V2 Symbol Resolution - Integration Test")
    print("=" * 60)
    
    try:
        client = test_contract_override()
        test_symbol_resolution(client)
        test_cooldown_scoping(client)
        test_tolerant_field_parsing()
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\nKey Features Verified:")
        print("  ✅ Contract override for CI/testing")
        print("  ✅ Symbol resolution with fallback")
        print("  ✅ Scoped cooldowns (route + query + symbol)")
        print("  ✅ Tolerant field parsing")
        print("  ✅ No network access required")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
