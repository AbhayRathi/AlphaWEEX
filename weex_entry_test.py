import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

def debug_connection():
    print("🔍 --- WEEX CONNECTION DEBUGGER ---")
    
    # 1. Check Public IP (What WEEX sees)
    try:
        ip = requests.get("https://api64.ipify.org").text
        print(f"📡 Your Server Public IP: {ip}")
        print("👉 ACTION: Ensure this IP is exactly what you submitted for the whitelist.")
    except:
        print("❌ Could not determine Public IP.")

    # 2. Check Public Market API (No Auth Required)
    # If this fails, your server is blocked from reaching WEEX entirely.
    url_time = "https://api-contract.weex.com/capi/v2/market/time"
    print(f"\n🌐 Testing Public Endpoint: {url_time}")
    try:
        resp = requests.get(url_time, timeout=10)
        print(f"✅ Status: {resp.status_code}")
        print(f"✅ Response: {resp.text}")
    except Exception as e:
        print(f"❌ Public API Failed: {e}")
        print("💡 Check your firewall or if this cloud region is blocked.")

    # 3. Check Account API (Auth Required)
    # This will show us the EXACT error code (like 521 for IP issues)
    print("\n🔐 Testing Private Endpoint (Assets)...")
    # (Re-using logic from the previous script but with raw printing)
    from weex_entry_test import send_weex_request
    try:
        resp = send_weex_request("GET", "/capi/v2/account/assets")
        print(f"HTTP Status: {resp.status_code}")
        print(f"Raw Body: '{resp.text}'")
        
        if resp.status_code == 521:
            print("🚩 ERROR 521: Your IP is definitely NOT whitelisted yet.")
        elif resp.status_code == 403:
            print("🚩 ERROR 403: Forbidden. Usually an IP or API Key permission issue.")
        elif resp.status_code == 401:
            print("🚩 ERROR 401: Unauthorized. Check your API Key and Passphrase.")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    debug_connection()
