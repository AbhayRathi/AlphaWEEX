import os
import time
import hmac
import hashlib
import base64
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG FROM OFFICIAL GUIDE ---
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
API_PASS = os.getenv('API_PASSWORD')
BASE_URL = "https://api-contract.weex.com" 

def generate_signature(timestamp, method, request_path, query_string, body_str):
    # Official Formula: timestamp + method + request_path + query_string + body
    message = timestamp + method.upper() + request_path + query_string + body_str
    signature = hmac.new(
        API_SECRET.encode('utf-8'), 
        message.encode('utf-8'), 
        hashlib.sha256
    ).digest()
    return base64.b64encode(signature).decode()

def send_weex_request(method, path, query_params="", body=None):
    timestamp = str(int(time.time() * 1000))
    body_str = json.dumps(body) if body else ""
    signature = generate_signature(timestamp, method, path, query_params, body_str)
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": API_PASS,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    url = f"{BASE_URL}{path}{query_params}"
    
    if method.upper() == "GET":
        return requests.get(url, headers=headers)
    else:
        return requests.post(url, headers=headers, data=body_str)

def run_test():
    print("🛰️ Connecting to WEEX Private Gateway...")
    
    try:
        # 1. Check Balance
        asset_resp = send_weex_request("GET", "/capi/v2/account/assets")
        if asset_resp.status_code != 200:
            print(f"❌ Auth Failed! Check your API Keys/Passphrase. (Status: {asset_resp.status_code})")
            print(f"Response: {asset_resp.text}")
            return
        
        assets = asset_resp.json()
        print("✅ Connection Authenticated.")

        # 2. Get BTC Price
        ticker_resp = requests.get(f"{BASE_URL}/capi/v2/market/ticker?symbol=cmt_btcusdt")
        ticker_data = ticker_resp.json()
        # The API returns a list in 'data' or a direct object
        price = float(ticker_data[0]['last']) if isinstance(ticker_data, list) else float(ticker_data['last'])
        print(f"✅ Current BTC Price: ${price}")

        # 3. Calculate Quantity for ~10 USDT
        # cmt_btcusdt contract size is 0.0001 BTC. 
        # We want $10 worth. 10 / Price = Qty in BTC.
        qty_btc = round(10 / price, 4)
        
        # 4. Place Market Order (Place Order API)
        order_body = {
            "symbol": "cmt_btcusdt",
            "size": str(qty_btc),
            "type": "1",        # 1 = Market Order
            "order_type": "0",  # 0 = Normal
            "match_price": "1", # 1 = Market price match
            "client_oid": f"test_{int(time.time())}"
        }

        print(f"🚀 Executing Qualification Trade: {qty_btc} BTC...")
        order_resp = send_weex_request("POST", "/capi/v2/order/placeOrder", body=order_body)
        res = order_resp.json()

        if res.get('order_id') or res.get('code') == '200':
            print("\n🏆 *******************************")
            print("🏆   QUALIFICATION SUCCESSFUL!   ")
            print(f"🏆   ORDER ID: {res.get('order_id')}")
            print("🏆 *******************************")
        else:
            print(f"❌ Order Rejected: {res}")

    except Exception as e:
        print(f"❌ script Error: {str(e)}")

if __name__ == "__main__":
    run_test()
