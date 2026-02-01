import os, requests, time, hmac, hashlib, base64, json, uuid
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    # The signature requires the body as a JSON string for POST
    body_str = json.dumps(body) if body else ""
    msg = ts + method.upper() + path + body_str
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-PASSPHRASE": api_pass, 
        "ACCESS-TIMESTAMP": ts, "Content-Type": "application/json"
    }

def execute_test_trade():
    base = "https://api-contract.weex.com"
    path = "/capi/v2/order/placeOrder"
    client_oid = "AIWARS_" + str(int(time.time()))
    
    # 🏆 Official AI Wars V2 Place Order Body
    body = {
        "symbol": "cmt_btcusdt",
        "client_oid": client_oid,
        "size": "0.0001",       # ~10 USDT notional
        "type": "1",            # 1 = Open Long (This fixes Error 40019)
        "order_type": "0",      # 0 = Normal
        "match_price": "1",     # 1 = Market Price
        "price": "0",           # Not used for market orders but often required as placeholder
        "leverage": "20"        # Competition Max
    }
    
    print(f"🚀 Attempting Mandatory Test Trade (OID: {client_oid})...")
    
    try:
        res = requests.post(base + path, headers=get_headers("POST", path, body), json=body).json()
        
        if res.get('code') == '00000':
            print("✅ SUCCESS! Gateway Passed.")
            print(f"OrderId: {res['data']['order_id']}")
        else:
            print(f"❌ Failed: {res.get('msg')} (Code: {res.get('code')})")
            if res.get('code') == '40015':
                print("💡 Tip: Check if you have set your account to 'Cross Margin' in the app.")
    except Exception as e:
        print(f"🔥 Script Error: {e}")

if __name__ == "__main__":
    execute_test_trade()
