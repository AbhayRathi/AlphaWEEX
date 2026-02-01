import os, requests, time, hmac, hashlib, base64, json
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

def wake_up_account():
    base = "https://api-contract.weex.com"
    symbol = "cmt_btcusdt"
    
    # 1. Set Leverage (Mandatory for Tournament)
    print(f"⚙️ Initializing {symbol} at 20x Leverage...")
    lev_path = "/capi/v2/account/setLeverage"
    lev_body = {"symbol": symbol, "leverage": "20", "marginCoin": "USDT"}
    requests.post(base + lev_path, headers=get_headers("POST", lev_path, lev_body), json=lev_body)

    # 2. Set Margin Mode to CROSS (Mandatory for Tournament)
    print("⚙️ Switching to CROSS margin mode...")
    mode_path = "/capi/v2/account/modifyMarginMode"
    mode_body = {"symbol": symbol, "marginMode": "cross", "marginCoin": "USDT"}
    requests.post(base + mode_path, headers=get_headers("POST", mode_path, mode_body), json=mode_body)

    # 3. Mandatory 10 USDT Test Trade
    path = "/capi/v2/order/placeOrder"
    body = {
        "symbol": symbol,
        "client_oid": "WAKEUP_" + str(int(time.time())),
        "size": "0.0001",   # ~10 USDT
        "type": "1",        # Open Long
        "order_type": "0",  # Normal
        "match_price": "1", # Market
        "price": "0",
        "leverage": "20"
    }
    
    print("🚀 Sending Alpha-Gateway Test Order...")
    res = requests.post(base + path, headers=get_headers("POST", path, body), json=body).json()
    
    if res.get('code') == '00000':
        print("✅ SUCCESS! Your competition account is now ACTIVE.")
    else:
        print(f"❌ Failed: {res.get('msg')} (Code: {res.get('code')})")

if __name__ == "__main__":
    wake_up_account()
