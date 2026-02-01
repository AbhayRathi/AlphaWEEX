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
    url = "https://api-contract.weex.com/capi/v2/account/accounts"
    res = requests.get(url, headers=get_headers("GET", "/capi/v2/account/accounts")).json()
    
    if res.get('data'):
        for acc in res['data']:
            if acc['marginCoin'] == 'USDT':
                print(f"\n💰 --- CURRENT WALLET STATUS ---")
                print(f"💵 Available: {acc['available']} USDT")
                print(f"📊 Total Equity: {acc['equity']} USDT")
                print(f"❄️ Frozen/Locked: {acc['frozen']} USDT")
    else:
        print("❌ No account data found. Check your API permissions.")

if __name__ == "__main__":
    check()
