import os, requests, time, hmac, hashlib, base64, json, uuid
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    # Note: Body must be empty string for signature if it's a GET, or JSON string for POST
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-PASSPHRASE": api_pass, 
        "ACCESS-TIMESTAMP": ts, "Content-Type": "application/json"
    }

def execute_test_trade():
    base = "https://api-contract.weex.com"
    
    # 1. Generate a unique Client Order ID (Mandatory for Error 40019)
    client_oid = "AIWARS_" + str(uuid.uuid4())[:8] + "_" + str(int(time.time()))
    
    # 2. Structure the order with Competition-specific fields
    body = {
        "symbol": "cmt_btcusdt",
        "marginCoin": "USDT",
        "size": "0.0001",           # ~10 USDT notional value
        "side": "buy",               # Buy/Sell
        "tradeSide": "open",         # open/close
        "orderType": "market",       # market/limit
        "client_oid": client_oid,    # The fix for 40019
        "leverage": "20"             # Competition Max
    }
    
    path = "/capi/v2/order/placeOrder"
    print(f"🚀 Attempting Mandatory Test Trade (OID: {client_oid})...")
    
    try:
        res = requests.post(base + path, headers=get_headers("POST", path, body), json=body).json()
        
        if res.get('code') == '00000':
            print("✅ SUCCESS! Gateway Passed.")
            print(f"OrderId: {res['data']['orderId']}")
            print("\nYour AI Wars dashboard should now reflect active status.")
        else:
            print(f"❌ Failed: {res.get('msg')} (Code: {res.get('code')})")
            if res.get('code') == '40015':
                print("💡 Tip: Check if you need to manually set 20x leverage in the App first.")
    except Exception as e:
        print(f"🔥 Script Error: {e}")

if __name__ == "__main__":
    execute_test_trade()
