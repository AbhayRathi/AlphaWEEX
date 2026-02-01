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
    # 1. Check Futures (Contract) Assets
    print("📋 Checking Futures Account...")
    f_res = requests.get("https://api-contract.weex.com/capi/v2/account/accounts", headers=get_headers("GET", "/capi/v2/account/accounts")).json()
    for a in f_res.get('data', []) or []:
        if float(a.get('equity', 0)) > 0:
            print(f"   [Futures] {a['marginCoin']}: Available={a['available']}, Equity={a['equity']}")

    # 2. Check Spot Assets
    print("\n📋 Checking Spot Account...")
    s_res = requests.get("https://api-spot.weex.com/api/v2/account/assets", headers=get_headers("GET", "/api/v2/account/assets")).json()
    for a in s_res.get('data', []) or []:
        if float(a.get('equity', 0)) > 0:
            print(f"   [Spot] {a['coinName']}: Available={a['available']}, Equity={a['equity']}")

    # 3. Check for Active Positions (Universal Scan)
    print("\n📋 Scanning for ANY open positions...")
    p_res = requests.get("https://api-contract.weex.com/capi/v2/account/allPosition", headers=get_headers("GET", "/capi/v2/account/allPosition")).json()
    pos = p_res.get('data', [])
    if pos:
        for p in pos:
            print(f"   [Position] {p['symbol']} {p['holdSide']} | Margin: {p['margin']}")
    else:
        print("   No active trading positions found.")

if __name__ == "__main__":
    audit()
