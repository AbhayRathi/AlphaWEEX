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

def pass_gateway():
    base = "https://api-contract.weex.com"
    symbol = "cmt_btcusdt"
    
    # 1. First, Cancel any "ghost" orders that might be freezing your 1,000 USDT
    print("🧹 Cleaning environment: Cancelling all existing orders...")
    c_path = "/capi/v2/order/cancelAllOrders"
    c_body = {"symbol": symbol, "cancelOrderType": "normal"} # From your API log discovery
    requests.post(base + c_path, headers=get_headers("POST", c_path, c_body), json=c_body)

    # 2. Place the Mandatory 10 USDT Test Order (Gateway Requirement)
    print(f"🚀 Attempting Mandatory Test Trade on {symbol}...")
    p_path = "/capi/v2/order/placeOrder"
    p_body = {
        "symbol": symbol,
        "client_oid": "ALPHA_" + str(int(time.time())),
        "size": "0.0001",   # Notional value ~10 USDT
        "type": "1",        # 1: Open Long (Tournament Standard)
        "order_type": "0",  # 0: Normal
        "match_price": "1", # 1: Market Price
        "price": "0",       # Required placeholder
        "leverage": "20"    # Competition Cap
    }
    
    res = requests.post(base + p_path, headers=get_headers("POST", p_path, p_body), json=p_body).json()
    
    if res.get('code') == '00000':
        print("✅ SUCCESS! Gateway Passed.")
        print(f"OrderId: {res['data'].get('order_id')}")
    else:
        print(f"❌ Failed: {res.get('msg')} (Code: {res.get('code')})")
        print("\n💡 If still 40015, verify your UID has been fully provisioned by WEEX staff.")

if __name__ == "__main__":
    pass_gateway()
