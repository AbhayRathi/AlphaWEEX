import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {"ACCESS-KEY":api_key,"ACCESS-SIGN":sig,"ACCESS-PASSPHRASE":api_pass,"ACCESS-TIMESTAMP":ts,"Content-Type":"application/json"}

def check_status():
    # Attempt to pull account configuration - if this is null, the API key is revoked.
    base = "https://api-contract.weex.com"
    path = "/capi/v2/account/config"
    
    print("🛰️ Verifying Competition API Key Status...")
    try:
        res = requests.get(base + path, headers=get_headers("GET", path)).json()
        if res.get('code') == '00000':
            print("✅ API Key is ACTIVE.")
            print(f"📊 Account Config: {json.dumps(res.get('data'), indent=2)}")
        else:
            print(f"❌ API Key REJECTED or REVOKED: {res.get('msg')} (Code: {res.get('code')})")
    except Exception as e:
        print(f"🔥 Connection Failed: {e}")

if __name__ == "__main__":
    check_status()
