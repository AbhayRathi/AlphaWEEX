#!/usr/bin/env python3
"""
Verification script for WEEX balance API fixes.
Tests both get_account_balance() and get_account_assets() methods.
"""

import sys
import os
import json
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

from core.weex_v2_client import WEEXv2Client

def load_credentials():
    """Load API credentials from config.json"""
    config_path = repo_root / "config.json"
    if not config_path.exists():
        print("❌ ERROR: config.json not found")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return (
            config['weex']['api_key'],
            config['weex']['api_secret'],
            config['weex']['passphrase']
        )
    except KeyError as e:
        print(f"❌ ERROR: Missing required WEEX configuration in config.json: {e}")
        sys.exit(1)

def main():
    print("="*60)
    print("WEEX Balance API Verification Script")
    print("="*60)
    
    # Load credentials
    api_key, api_secret, passphrase = load_credentials()
    print("✅ Credentials loaded from config.json")
    
    # Initialize client
    client = WEEXv2Client(api_key, api_secret, passphrase)
    print("✅ WEEXv2Client initialized")
    
    # Test 1: get_account_assets()
    print("\n" + "="*60)
    print("TEST 1: get_account_assets()")
    print("="*60)
    try:
        equity = client.get_account_assets()
        if equity > 0:
            print(f"✅ SUCCESS: Equity = ${equity:.2f}")
        else:
            print(f"⚠️  WARNING: Equity = $0.00 (check if account has funds)")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: get_account_balance()
    print("\n" + "="*60)
    print("TEST 2: get_account_balance()")
    print("="*60)
    try:
        balance = client.get_account_balance()
        if balance:
            total_equity = balance.get('totalEquity') if balance.get('totalEquity') is not None else balance.get('equity', 0)
            print(f"✅ SUCCESS: Balance = {balance}")
            print(f"   Total Equity = ${float(total_equity):.2f}")
        else:
            print("❌ FAILED: Returned None")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Raw API endpoint test
    print("\n" + "="*60)
    print("TEST 3: Raw API Call to /capi/v2/account/getAccounts")
    print("="*60)
    try:
        response = client.send_weex_request("GET", "/capi/v2/account/getAccounts")
        print(f"✅ Status Code: {response.status_code}")
        print(f"   Response Type: {type(response.json())}")
        
        data = response.json()
        if isinstance(data, list):
            print(f"   Response Format: List with {len(data)} items")
        elif isinstance(data, dict):
            print(f"   Response Format: Dict")
            print(f"   Keys: {list(data.keys())}")
        
        print(f"   Raw Response (first 500 chars): {str(data)[:500]}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
    
    # Final verdict
    print("\n" + "="*60)
    print("FINAL VERDICT")
    print("="*60)
    try:
        equity = client.get_account_assets()
        if equity > 0:
            print("✅ ALL SYSTEMS GO - Bot can detect balance!")
            print(f"   Ready to trade with ${equity:.2f} equity")
            return 0
        else:
            print("⚠️  WARNING: Balance detected as $0.00")
            print("   - Check if account has funds")
            print("   - Verify API credentials have correct permissions")
            return 1
    except Exception as e:
        print("❌ CRITICAL FAILURE - Bot cannot detect balance")
        print(f"   Error: {str(e)}")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
