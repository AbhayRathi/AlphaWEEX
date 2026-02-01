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
    base = "https://api-contract.weex.com"
    # Testing 3 different V2 position endpoints
    endpoints = ["/capi/v2/account/allPosition", "/capi/v2/account/positions", "/capi/v2/order/currentOrder"]
    
    print("🔍 Searching for locked margin...")
    for path in endpoints:
        res = requests.get(base + path, headers=get_headers("GET", path)).json()
        data = res.get('data', [])
        if data:
            print(f"\n✅ FOUND DATA in {path}:")
            print(json.dumps(data, indent=2))
            return
    print("\n❌ No active positions found in standard endpoints. Check if funds are in 'Copy Trading'.")

if __name__ == "__main__":
    scan()
