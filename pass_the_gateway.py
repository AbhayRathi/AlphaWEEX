import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-PASSPHRASE": api_pass, 
        "ACCESS-TIMESTAMP": ts, "Content-Type": "application/json"
    }

def execute_test_trade():
    base = "https://api-contract.weex.com"
    
    # Mandatory competition parameters
    symbol = "cmt_btcusdt"  # MUST use cmt_ prefix
    side = "buy"           # Open a Long
    trade_side = "open"    
    order_type = "market"  # Competition test requires Market or Limit
    margin_coin = "USDT"
    
    # We use a small size (0.0001 BTC is ~10 USDT at 100k price)
    # Adjust 'size' to ensure notional value is exactly >= 10 USDT
    body = {
        "symbol": symbol,
        "side": side,
        "tradeSide": trade_side,
        "orderType": order_type,
        "marginCoin": margin_coin,
        "size": "0.0001", 
        "leverage": "20" # Competition limit
    }
    
    path = "/capi/v2/order/placeOrder"
    print(f"🚀 Attempting Mandatory 10 USDT Test Trade on {symbol}...")
    
    res = requests.post(base + path, headers=get_headers("POST", path, body), json=body).json()
    
    if res.get('code') == '00000':
        print("✅ SUCCESS! Gateway Passed.")
        print(f"OrderId: {res['data']['orderId']}")
        print("Your 1,000 USDT balance should now be visible in your dashboard.")
    else:
        print(f"❌ Failed: {res.get('msg')} (Code: {res.get('code')})")
        print("If you see 'Insufficient Balance', the WEEX team may still be provisioning your UID.")

if __name__ == "__main__":
    execute_test_trade()
