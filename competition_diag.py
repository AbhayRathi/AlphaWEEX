import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {"ACCESS-KEY":api_key,"ACCESS-SIGN":sig,"ACCESS-PASSPHRASE":api_pass,"ACCESS-TIMESTAMP":ts,"Content-Type":"application/json"}

def check():
    base = "https://api-contract.weex.com"
    
    # 1. Check account type 'USDT_MIX' specifically
    print("🛰️ Scanning USDT_MIX (Competition Account)...")
    path = "/capi/v2/account/accounts" # V2 List
    res = requests.get(base + path, headers=get_headers("GET", path)).json()
    
    if res.get('data'):
        for acc in res['data']:
            print(f"✅ Found {acc['marginCoin']} | Available: {acc['available']} | Equity: {acc['equity']}")
    else:
        # 2. Try the V1 Fallback (Sometimes used for managed sub-accounts)
        print("⚠️ V2 scan empty. Checking V1 legacy endpoint...")
        path_v1 = "/api/v1/contract/account/accounts"
        res_v1 = requests.get(base + path_v1, headers=get_headers("GET", path_v1)).json()
        print(f"V1 Result: {res_v1}")

if __name__ == "__main__":
    check()
