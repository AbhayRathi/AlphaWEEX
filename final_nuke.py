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
        "ACCESS-TIMESTAMP": ts, "Content-Type": "application/json"
    }

def nuke_all():
    base = "https://api-contract.weex.com"
    
    # 1. Cancel ALL pending orders for ALL symbols
    print("📡 Step 1: Broad-spectrum order cancellation...")
    # Passing an empty body to target all symbols
    cancel_path = "/capi/v2/order/cancelAllOrder"
    requests.post(base + cancel_path, headers=get_headers("POST", cancel_path, {}), json={})

    # 2. Get Positions from the USDT-M Mix Account
    # Endpoint: /capi/v2/account/allPosition
    print("🔍 Step 2: Fetching USDT-M Perpetual positions...")
    pos_path = "/capi/v2/account/allPosition"
    res = requests.get(base + pos_path, headers=get_headers("GET", pos_path)).json()
    
    positions = res.get('data', [])
    if not positions:
        print("⚠️ No positions found. Checking backup endpoint...")
        # Fallback to the 'settings' view which sometimes lists active margins
        pos_path = "/capi/v2/account/getAccounts"
        res = requests.get(base + pos_path, headers=get_headers("GET", pos_path)).json()
        # Find coins with non-zero locked/margin amounts
        for acc in res.get('data', []):
            if float(acc.get('frozen', 0)) > 0 or float(acc.get('available', 0)) == 0:
                print(f"📍 Detected active margin in {acc.get('marginCoin')} account.")

    # 3. Forced Market Close
    print("🧨 Step 3: Executing Market Termination...")
    # WEEX V2 "Close All" command
    close_all_path = "/capi/v2/order/closeAllPosition"
    # cmt_btcusdt is your primary, but we'll try to trigger a generic close
    body = {"symbol": "cmt_btcusdt"} 
    final_res = requests.post(base + close_all_path, headers=get_headers("POST", close_all_path, body), json=body).json()
    
    print(f"🏁 Result: {final_res.get('msg')} (Code: {final_res.get('code')})")
    
    if final_res.get('code') == '00000':
        print("\n✅ POSITIONS NUKED. Available balance is being released.")
    else:
        print("\n❌ API refused the close command. If your balance is still 0, check if you have 'Isolated' positions open in the WEEX app.")

if __name__ == "__main__":
    nuke_all()
