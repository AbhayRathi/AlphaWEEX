import os, requests, time, hmac, hashlib, base64, json, uuid
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body) if body else ""
    msg = ts + method.upper() + path + body_str
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-PASSPHRASE": api_pass, 
        "ACCESS-TIMESTAMP": ts, "Content-Type": "application/json"
    }

def initialize_and_trade():
    base = "https://api-contract.weex.com"
    symbol = "cmt_btcusdt"
    
    # 1. Force Leverage to 20x (Initializes the margin for this pair)
    print(f"⚙️ Setting leverage for {symbol} to 20x...")
    lev_path = "/capi/v2/account/setLeverage"
    lev_body = {"symbol": symbol, "leverage": "20", "marginCoin": "USDT"}
    requests.post(base + lev_path, headers=get_headers("POST", lev_path, lev_body), json=lev_body)

    # 2. Place the Mandatory 10 USDT Test Order
    path = "/capi/v2/order/placeOrder"
    client_oid = "ALPHA_" + str(int(time.time()))
    
    body = {
        "symbol": symbol,
        "client_oid": client_oid,
        "size": "0.0001",       # Base coin amount (~10 USDT)
        "type": "1",            # 1 = Open Long
        "order_type": "0",      # 0 = Normal
        "match_price": "1",     # 1 = Market Price
        "price": "0",
        "leverage": "20"
    }
    
    print(f"🚀 Executing Mandatory Test Trade (OID: {client_oid})...")
    res = requests.post(base + path, headers=get_headers("POST", path, body), json=body).json()
    
    if res.get('code') == '00000':
        print("✅ SUCCESS! Gateway Passed.")
        print(f"OrderId: {res['data']['order_id']}")
    else:
        print(f"❌ Failed: {res.get('msg')} (Code: {res.get('code')})")
        if res.get('code') == '40015':
            print("\n🚨 STILL INSUFFICIENT BALANCE?")
            print("This means the 1,000 USDT is likely in your 'Spot' wallet.")
            print("Please run: python3 transfer_to_futures.py")

if __name__ == "__main__":
    initialize_and_trade()
