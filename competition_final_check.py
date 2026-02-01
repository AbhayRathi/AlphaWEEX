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

def verify_competition_fund():
    base = "https://api-contract.weex.com"
    
    # Competition accounts use /capi/v2/account/getAccounts for the main list
    path = "/capi/v2/account/getAccounts"
    print("🛰️ Querying WEEX Competition Account...")
    
    try:
        res = requests.get(base + path, headers=get_headers("GET", path)).json()
        if res.get('data'):
            for acc in res['data']:
                # The 'marginCoin' for competition is always USDT
                if acc.get('marginCoin') == 'USDT':
                    print("\n💰 --- COMPETITION WALLET FOUND ---")
                    print(f"💵 Available Balance: {acc.get('available')} USDT")
                    print(f"📊 Total Equity:      {acc.get('equity')} USDT")
                    print(f"❄️ Frozen/Locked:     {acc.get('frozen')} USDT")
                    return
            print("⚠️ USDT balance not found in the account list.")
        else:
            print(f"❌ Error: {res.get('msg')} (Code: {res.get('code')})")
    except Exception as e:
        print(f"🔥 Request Error: {e}")

if __name__ == "__main__":
    verify_competition_fund()
