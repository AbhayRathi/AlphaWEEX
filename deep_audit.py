import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {"ACCESS-KEY":api_key,"ACCESS-SIGN":sig,"ACCESS-PASSPHRASE":api_pass,"ACCESS-TIMESTAMP":ts,"Content-Type":"application/json"}

def audit():
    base = "https://api-contract.weex.com"
    
    # 1. Check Plan Orders (TP/SL)
    print("🔎 Checking for hidden 'Plan Orders' (TP/SL)...")
    plan_path = "/capi/v2/order/currentPlanOrder?symbol=cmt_btcusdt"
    res = requests.get(base + plan_path, headers=get_headers("GET", plan_path)).json()
    if res.get('data'):
        print(f"⚠️ FOUND {len(res['data'])} PLAN ORDERS! These are freezing your margin.")
        for order in res['data']:
            print(f"   - OrderID: {order['order_id']} | Symbol: {order['symbol']}")
    
    # 2. Check Copy Trade Account
    print("\n🔎 Checking Copy Trading Sub-Account...")
    copy_path = "/capi/v2/copytrade/currentOrder"
    res_copy = requests.get(base + copy_path, headers=get_headers("GET", copy_path)).json()
    if res_copy.get('data'):
        print(f"⚠️ FOUND ACTIVE COPY TRADES! Balance is locked here.")
    else:
        print("   Copy Trading is empty.")

    # 3. Specific Symbol Force-Check
    print("\n🔎 Force-checking BTCUSDT Position directly...")
    direct_path = "/capi/v2/account/getPosition?symbol=cmt_btcusdt"
    res_direct = requests.get(base + direct_path, headers=get_headers("GET", direct_path)).json()
    if res_direct.get('data'):
        print(f"✅ FOUND HIDDEN POSITION: {json.dumps(res_direct['data'])}")
    else:
        print("   Direct symbol scan: No position.")

if __name__ == "__main__":
    audit()
