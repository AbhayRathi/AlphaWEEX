import os
import time
import hmac
import hashlib
import json
import requests
import uuid
import base64
from dotenv import load_dotenv

load_dotenv()

def generate_weex_signature(secret, method, path, timestamp, body=""):
    # WEEX V2 requires: timestamp + METHOD + path + body
    # The method MUST be uppercase (e.g., POST)
    message = str(timestamp) + method.upper() + path + body
    
    # 1. Create HMAC SHA256
    mac = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    
    # 2. WEEX requires the signature to be Base64 Encoded
    return base64.b64encode(mac.digest()).decode('utf-8')

def manual_test():
    # Credentials
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_pass = os.getenv("API_PASSWORD")
    
    url = "https://api-contract.weex.com"
    path = "/capi/v2/order/placeOrder"
    
    # Competition Payload
    payload = {
        "symbol": "cmt_btcusdt",
        "client_oid": str(uuid.uuid4()).replace("-", "")[:30],
        "side": "1",        # 1 = Buy
        "size": "0.001",    # Strings are safer for WEEX
        "type": "1",        # 1 = Market
        "order_type": "0",  # 0 = Normal
        "match_price": "1"  # 1 = Market
    }
    # No spaces in JSON for signature consistency
    body = json.dumps(payload, separators=(',', ':'))
    
    # Authentication
    timestamp = str(int(time.time() * 1000))
    signature = generate_weex_signature(api_secret, "POST", path, timestamp, body)
    
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-PASSPHRASE": api_pass,
        "ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json",
        "locale": "en-US"
    }

    print(f"🚀 Sending order to {path}...")
    
    try:
        response = requests.post(url + path, headers=headers, data=body)
        
        print(f"📡 Status: {response.status_code}")
        if response.text:
            data = response.json()
            print("✅ RESPONSE:", json.dumps(data, indent=2))
            
            if data.get('code') == '00000':
                print("\n💰 BOOM! Order placed. Check your competition dashboard.")
            else:
                print(f"\n❌ REJECTED: {data.get('msg')} (Code: {data.get('code')})")
        else:
            print("❌ Server returned empty response.")
            
    except Exception as e:
        print(f"🚨 ERROR: {str(e)}")

if __name__ == "__main__":
    manual_test()
