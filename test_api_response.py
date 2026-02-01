#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/alphaWEEX')

import json
from core.weex_v2_client import WEEXv2Client

# Load credentials from wherever competition_bot.py loads them
try:
    # Try method 1: config.json in various locations
    import os
    config_paths = [
        '/root/alphaWEEX/config.json',
        '/root/config.json',
        'config.json'
    ]
    config = None
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded config from: {path}\n")
            break
    
    if not config:
        # Try method 2: Check how competition_bot imports
        import competition_bot
        # Config might be loaded there
        print("Attempting to use competition_bot credentials...\n")
    
    if config:
        api_key = config['weex']['api_key']
        api_secret = config['weex']['api_secret']
        passphrase = config['weex']['passphrase']
    else:
        raise Exception("Could not find config")
        
except Exception as e:
    print(f"❌ Could not load credentials: {e}")
    print("\nPlease edit this script and add your credentials manually:")
    print('  api_key = "your_key_here"')
    print('  api_secret = "your_secret_here"')
    print('  passphrase = "your_passphrase_here"')
    sys.exit(1)

print("="*70)
print("DIAGNOSTIC: Raw API Response from /capi/v2/account/getAccounts")
print("="*70)

client = WEEXv2Client(api_key, api_secret, passphrase)

try:
    print("\n📡 Making API call...\n")
    response = client.send_weex_request("GET", "/capi/v2/account/getAccounts")
    
    print(f"Status Code: {response.status_code}")
    print(f"Status: {'✅ OK' if response.status_code == 200 else '❌ ERROR'}\n")
    
    if response.status_code != 200:
        print(f"Error Response Text:\n{response.text}\n")
    else:
        data = response.json()
        print(f"Response Type: {type(data)}")
        print(f"\n{'='*70}")
        print("FULL RAW RESPONSE:")
        print('='*70)
        print(json.dumps(data, indent=2))
        print('='*70)
        
        # Analyze structure
        print("\n📊 RESPONSE ANALYSIS:")
        print('='*70)
        
        if isinstance(data, list):
            print(f"✅ Response is a LIST with {len(data)} items")
            if len(data) > 0:
                print(f"\nFirst item keys: {list(data[0].keys())}")
                print(f"\nAll coinName values:")
                for i, item in enumerate(data):
                    coin_name = item.get('coinName') or item.get('coin_name') or item.get('symbol')
                    equity = item.get('equity') or item.get('balance') or item.get('amount')
                    print(f"  [{i}] coinName: {coin_name}, equity/balance: {equity}")
                    
                # Check for USDT specifically
                usdt_found = False
                for item in data:
                    if item.get('coinName') == 'USDT':
                        usdt_found = True
                        print(f"\n✅ FOUND USDT: {item}")
                        break
                
                if not usdt_found:
                    print("\n❌ USDT NOT FOUND in response")
                    print("   Checking case variations...")
                    for item in data:
                        cn = item.get('coinName', '').upper()
                        if 'USDT' in cn or 'USD' in cn:
                            print(f"   Found similar: {item}")
            else:
                print("❌ List is EMPTY")
                
        elif isinstance(data, dict):
            print(f"✅ Response is a DICT")
            print(f"Keys: {list(data.keys())}")
            
            if 'data' in data:
                items = data['data']
                print(f"\n'data' key contains {len(items)} items")
                if len(items) > 0:
                    print(f"First item: {items[0]}")
            
            if 'code' in data:
                print(f"Code: {data['code']}")
                if data['code'] != '00000':
                    print(f"❌ API returned error code: {data['code']}")
                    
except Exception as e:
    print(f"\n❌ EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("END DIAGNOSTIC")
print("="*70)
