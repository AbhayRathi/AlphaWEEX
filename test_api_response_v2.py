#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/alphaWEEX')

import json
from core.weex_v2_client import WEEXv2Client

print("="*70)
print("DIAGNOSTIC: Raw API Response from /capi/v2/account/getAccounts")
print("="*70)

# Load credentials from environment variables
API_KEY = os.getenv('API_KEY') or os.getenv('WEEX_API_KEY')
API_SECRET = os.getenv('API_SECRET') or os.getenv('WEEX_API_SECRET')
API_PASSWORD = os.getenv('API_PASSWORD') or os.getenv('WEEX_API_PASSWORD')

if not API_KEY or not API_SECRET or not API_PASSWORD:
    print("❌ ERROR: Environment variables not set!")
    sys.exit(1)

print(f"✅ Credentials loaded")
print(f"   API_KEY: {API_KEY[:8]}***\n")

client = WEEXv2Client(API_KEY, API_SECRET, API_PASSWORD)

try:
    print("📡 Making API call to /capi/v2/account/getAccounts...\n")
    response = client.send_weex_request("GET", "/capi/v2/account/getAccounts")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ ERROR Response:\n{response.text}\n")
        sys.exit(1)
    
    data = response.json()
    print(f"✅ Status 200 OK")
    print(f"Response Type: {type(data).__name__}\n")
    print("="*70)
    print("FULL RAW RESPONSE:")
    print("="*70)
    print(json.dumps(data, indent=2))
    print("="*70)
    
    # Analyze
    print("\n📊 ANALYSIS:")
    print("="*70)
    
    if isinstance(data, list):
        print(f"Response is LIST with {len(data)} items\n")
        if len(data) > 0:
            print("All items:")
            for i, item in enumerate(data):
                cn = item.get('coinName', 'N/A')
                eq = item.get('equity', 'N/A')
                print(f"  [{i}] coinName={cn}, equity={eq}")
            
            usdt = [item for item in data if item.get('coinName') == 'USDT']
            if usdt:
                print(f"\n✅ FOUND USDT:\n{json.dumps(usdt[0], indent=2)}")
            else:
                print("\n❌ USDT NOT FOUND IN RESPONSE")
        else:
            print("❌ LIST IS EMPTY - NO ACCOUNTS RETURNED")
    elif isinstance(data, dict):
        print(f"Response is DICT")
        print(f"Keys: {list(data.keys())}\n")
        if 'data' in data:
            items = data['data']
            print(f"'data' key has {len(items)} items:")
            for i, item in enumerate(items):
                cn = item.get('coinName', 'N/A')
                eq = item.get('equity', 'N/A')
                print(f"  [{i}] coinName={cn}, equity={eq}")
    
    print("\n" + "="*70)
    print("Testing get_account_assets():")
    print("="*70)
    equity = client.get_account_assets()
    print(f"Result: ${equity:.2f}")
    if equity > 0:
        print("✅ SUCCESS - Method works!")
    else:
        print("❌ FAILED - Method returned 0.0")
        
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("END DIAGNOSTIC")
print("="*70)
