import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {"ACCESS-KEY":api_key,"ACCESS-SIGN":sig,"ACCESS-PASSPHRASE":api_pass,"ACCESS-TIMESTAMP":ts,"Content-Type":"application/json"}

def release_margin():
    base = "https://api-contract.weex.com"
    
    # 1. Kill all Plan/Trigger orders (The #1 cause of 'Available: 0')
    print("🧹 Step 1: Force-cancelling all Plan/Trigger orders...")
    p_path = "/capi/v2/order/cancelAllPlanOrder"
    p_body = {"symbol": "cmt_btcusdt"}
    res_p = requests.post(base + p_path, headers=get_headers("POST", p_path, p_body), json=p_body).json()
    print(f"   Plan Cancel: {res_p.get('msg')} ({res_p.get('code')})")

    # 2. Check for 'Hidden' Position on the most common trading pair
    print("\n🔍 Step 2: Querying specific BTC position status...")
    s_path = "/capi/v2/account/getPosition?symbol=cmt_btcusdt"
    res_s = requests.get(base + s_path, headers=get_headers("GET", s_path)).json()
    
    if res_s.get('data'):
        for pos in res_s['data']:
            side = pos.get('holdSide')
            print(f"   Found {side} position! Closing now...")
            c_path = "/capi/v2/order/closePosition"
            c_body = {"symbol": "cmt_btcusdt", "side": side}
            res_c = requests.post(base + c_path, headers=get_headers("POST", c_path, c_body), json=c_body).json()
            print(f"   Close Status: {res_c.get('msg')}")
    else:
        print("   No active BTC positions found via direct query.")

    # 3. Final Account Asset Verification
    print("\n💰 Step 3: Verifying final Available Balance...")
    a_path = "/capi/v2/account/accounts"
    res_a = requests.get(base + a_path, headers=get_headers("GET", a_path)).json()
    for item in res_a.get('data', []):
        if item['marginCoin'] == 'USDT':
            print(f"   Available: {item['available']} USDT")
            print(f"   Equity:    {item['equity']} USDT")

if __name__ == "__main__":
    release_margin()
