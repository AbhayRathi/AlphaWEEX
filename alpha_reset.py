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

def full_reset():
    base = "https://api-contract.weex.com"
    symbol = "cmt_btcusdt"

    # 1. Close All Positions (The endpoint you found)
    print(f"🧹 Force-closing all positions for {symbol}...")
    close_path = "/capi/v2/order/closePositions"
    close_body = {"symbol": symbol}
    res_close = requests.post(base + close_path, headers=get_headers("POST", close_path, close_body), json=close_body).json()
    print(f"   Response: {res_close.get('msg')} (Code: {res_close.get('code')})")

    # 2. Cancel All Orders (Tournament specific)
    print("🛑 Cancelling all normal/plan orders...")
    cancel_path = "/capi/v2/order/cancelAllOrders"
    cancel_body = {"symbol": symbol, "cancelOrderType": "normal"}
    requests.post(base + cancel_path, headers=get_headers("POST", cancel_path, cancel_body), json=cancel_body)

    # 3. Final Verification
    print("\n🔍 Checking if 'Available' balance has unlocked...")
    acc_path = "/capi/v2/account/accounts"
    res_acc = requests.get(base + acc_path, headers=get_headers("GET", acc_path)).json()
    
    for acc in res_acc.get('data', []) or []:
        if acc['marginCoin'] == 'USDT':
            print(f"💰 --- FINAL STATUS ---")
            print(f"💵 Available: {acc['available']} USDT")
            print(f"📊 Equity:    {acc['equity']} USDT")
            if float(acc['available']) > 0:
                print("✅ WE ARE GO! Your balance is now tradeable.")
            else:
                print("⚠️ Still locked. The system requires an initialization trade.")

if __name__ == "__main__":
    full_reset()
