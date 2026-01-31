#!/usr/bin/env python3
"""
Verification script to test the WEEX API balance endpoint fix.
This script verifies that the updated WeexClient can successfully fetch balances
using the /capi/v2/account/getAccounts endpoint (official WEEX V2 Contract API).
"""
import os
import sys
from dotenv import load_dotenv
from core.weex_v2_client import WEEXv2Client

load_dotenv()

def verify_balance_fix():
    """
    Test the updated balance retrieval logic.
    """
    print("=" * 60)
    print("🔍 WEEX Balance Endpoint Verification")
    print("=" * 60)
    
    # Get API credentials
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    api_password = os.getenv('API_PASSWORD')
    
    if not all([api_key, api_secret, api_password]):
        print("❌ Error: Missing API credentials in .env file")
        print("   Required: API_KEY, API_SECRET, API_PASSWORD")
        return False
    
    print(f"\n✅ API credentials loaded")
    print(f"   API Key: {api_key[:8]}...")
    
    # Initialize WeexClient with updated endpoint
    try:
        print("\n🔄 Initializing WEEX v2 Client...")
        client = WEEXv2Client(api_key, api_secret, api_password)
        print("✅ Client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test 1: get_account_balance (using /capi/v2/account/getAccounts)
    print("\n" + "-" * 60)
    print("Test 1: Fetching balance using get_account_balance()")
    print(f"Endpoint: /capi/v2/account/getAccounts")
    print("-" * 60)
    
    try:
        balance_data = client.get_account_balance()
        
        if balance_data is None:
            print("❌ Balance retrieval returned None (zero balance or error)")
            print("   This indicates the 'Zero balance detected' issue may still exist")
            return False
        
        # Extract equity value
        equity = balance_data.get('equity', 0.0)
        available = balance_data.get('availableBalance', 0.0)
        
        print(f"✅ Balance retrieved successfully!")
        print(f"   Total Equity: ${equity:.2f}")
        print(f"   Available Balance: ${available:.2f}")
        
        if equity > 0:
            print(f"\n🎉 SUCCESS: Zero balance issue is RESOLVED!")
            print(f"   Account has ${equity:.2f} USDT")
        else:
            print(f"\n⚠️  WARNING: Balance is still zero")
            print(f"   This could indicate:")
            print(f"   1. Account genuinely has no funds")
            print(f"   2. Response format is different than expected")
            
    except ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print(f"   This indicates a 521/403 error or network issue")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: get_account_assets (also using /capi/v2/account/getAccounts)
    print("\n" + "-" * 60)
    print("Test 2: Fetching balance using get_account_assets()")
    print(f"Endpoint: /capi/v2/account/getAccounts")
    print("-" * 60)
    
    try:
        assets_balance = client.get_account_assets()
        print(f"✅ Assets retrieved successfully!")
        print(f"   USDT Equity: ${assets_balance:.2f}")
        
        if assets_balance > 0:
            print(f"\n🎉 SUCCESS: get_account_assets() working correctly!")
        else:
            print(f"\n⚠️  WARNING: Assets balance is zero")
            
    except Exception as e:
        print(f"❌ Failed to get assets: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Verification Complete!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = verify_balance_fix()
    sys.exit(0 if success else 1)
