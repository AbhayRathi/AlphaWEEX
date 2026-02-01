import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_pass = os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "ACCESS-KEY": api_key, 
        "ACCESS-SIGN": sig, 
        "ACCESS-PASSPHRASE": api_pass, 
        "ACCESS-TIMESTAMP": ts, 
        "Content-Type": "application/json"
    }

def find_funds():
    base = "https://api-contract.weex.com"
    # This is the specific endpoint for USDT-M Futures accounts
    path = "/capi/v2/account/accounts"
    
    try:
        res = requests.get(base + path, headers=get_headers("GET", path)).json()
        if res.get('code') == '00000' and res.get('data'):
            print("✅ Found Futures Account Data:")
            for account in res['data']:
                if account['marginCoin'] == 'USDT':
                    print(f"💰 Asset: {account['marginCoin']}")
                    print(f"📉 Available: {account['available']}")
                    print(f"📈 Equity: {account['equity']}")
                    print(f"🔒 Frozen: {account['frozen']}")
        else:
            print(f"❌ Error or No Data: {res.get('msg')} (Code: {res.get('code')})")
    except Exception as e:
        print(f"⚠️ Request failed: {e}")

if __name__ == "__main__":
    find_funds()
