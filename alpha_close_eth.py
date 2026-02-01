import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    body_str = json.dumps(body) if body else ""
    msg = ts + method.upper() + path + body_str
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-PASSPHRASE": api_pass, 
        "ACCESS-TIMESTAMP": ts, "Content-Type": "application/json"
    }

def close_eth():
    base = "https://api-contract.weex.com"
    symbol = "cmt_ethusdt" # Designated tournament symbol

    print(f"🧹 Force-closing all ETH positions...")
    close_path = "/capi/v2/order/closePositions"
    close_body = {"symbol": symbol}
    
    try:
        res = requests.post(base + close_path, headers=get_headers("POST", close_path, close_body), json=close_body).json()
        
        # Handling list response
        if isinstance(res, list):
            if not res:
                print("✅ No open ETH positions found.")
            for item in res:
                status = "Success" if item.get('success') else "Failed"
                print(f"   Position {item.get('positionId')}: {status} {item.get('errorMessage', '')}")
        else:
            print(f"   Response: {res.get('msg')} (Code: {res.get('code')})")
            
    except Exception as e:
        print(f"🔥 Error: {e}")

if __name__ == "__main__":
    close_eth()
