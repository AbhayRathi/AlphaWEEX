import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {"ACCESS-KEY":api_key,"ACCESS-SIGN":sig,"ACCESS-PASSPHRASE":api_pass,"ACCESS-TIMESTAMP":ts,"Content-Type":"application/json"}

def scan():
    # Check USDT_MIX (Futures)
    res_f = requests.get("https://api-contract.weex.com/capi/v2/account/accounts", headers=get_headers("GET", "/capi/v2/account/accounts")).json()
    # Check Spot
    res_s = requests.get("https://api-spot.weex.com/api/v2/account/assets", headers=get_headers("GET", "/api/v2/account/assets")).json()
    
    print("\n--- 🛰️ DEEP SCAN RESULTS ---")
    print(f"Futures Data: {json.dumps(res_f.get('data'), indent=2)}")
    print(f"Spot Data:    {json.dumps(res_s.get('data'), indent=2)}")

if __name__ == "__main__":
    scan()
