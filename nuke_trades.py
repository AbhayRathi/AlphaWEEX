import os, time, hmac, hashlib, requests, base64, json
from dotenv import load_dotenv

load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-PASSPHRASE": api_pass, 
        "ACCESS-TIMESTAMP": ts, "Content-Type": "application/json", "locale": "en-US"
    }

def emergency_nuke():
    base_url = "https://api-contract.weex.com"
    
    # 1. CANCEL PENDING ORDERS
    print("🛑 Step 1: Cancelling all pending BTC orders...")
    cancel_path = "/capi/v2/order/cancelAllOrder"
    cancel_body = {"symbol": "cmt_btcusdt"}
    res_cancel = requests.post(base_url + cancel_path, headers=get_headers("POST", cancel_path, cancel_body), json=cancel_body).json()
    print(f"Result: {res_cancel.get('msg')} ({res_cancel.get('code')})")

    # 2. CLOSE ACTIVE POSITIONS
    print("\n🧨 Step 2: Closing all active positions to free margin...")
    pos_path = "/capi/v2/order/allPosition"
    res_pos = requests.get(base_url + pos_path, headers=get_headers("GET", pos_path)).json()
    
    if res_pos.get('code') == '00000' and res_pos.get('data'):
        for pos in res_pos['data']:
            symbol = pos['symbol']
            side = pos['holdSide'] # 'long' or 'short'
            print(f"Found {side} position on {symbol}. Executing market close...")
            
            close_path = "/capi/v2/order/closePosition"
            close_body = {"symbol": symbol, "side": side}
            res_close = requests.post(base_url + close_path, headers=get_headers("POST", close_path, close_body), json=close_body).json()
            print(f"-> Close Result: {res_close.get('msg')} ({res_close.get('code')})")
    else:
        print("No active positions found.")

if __name__ == "__main__":
    emergency_nuke()
