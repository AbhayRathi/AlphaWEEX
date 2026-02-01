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
    message = str(timestamp) + method.upper() + path + body
    mac = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode('utf-8')

def manual_sell():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_pass = os.getenv("API_PASSWORD")
    
    url = "https://api-contract.weex.com"
    path = "/capi/v2/order/placeOrder"
    
    # --- CRITICAL CHANGES FOR SELLING ---
    payload = {
        "symbol": "cmt_btcusdt",
        "client_oid": str(uuid.uuid4()).replace("-", "")[:30],
        "side": "2",        # 2 = Sell
        "size": "0.001",    # Match the size of your open position
        "type": "3",        # 3 = CLOSE LONG (Specific to WEEX V2)
        "order_type": "0",  
        "match_price": "1"  
    }
    
    body = json.dumps(payload, separators=(',', ':'))
    timestamp = str(int(time.time() * 1000))
    signature = generate_weex_signature(api_secret, "POST", path, timestamp, body)
    
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-PASSPHRASE": api_pass,
        "ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }

    print(f"🚨 Sending CLOSE order for cmt_btcusdt...")
    
    try:
        response = requests.post(url + path, headers=headers, data=body)
        if response.text:
            data = response.json()
            print("✅ RESPONSE:", json.dumps(data, indent=2))
            # WEEX returns the order_id on success
            if "order_id" in data:
                print("\n💰 SUCCESS! Position closed.")
        else:
            print("❌ Empty response.")
    except Exception as e:
        print(f"🚨 ERROR: {str(e)}")

if __name__ == "__main__":
    manual_sell()
