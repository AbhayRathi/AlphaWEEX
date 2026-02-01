import os, time, hmac, hashlib, requests, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {"ACCESS-KEY":api_key, "ACCESS-SIGN":sig, "ACCESS-PASSPHRASE":api_pass, "ACCESS-TIMESTAMP":ts, "Content-Type":"application/json"}

def kill_everything():
    base = "https://api-contract.weex.com"
    # Step 1: Get all positions exactly as the API sees them
    path = "/capi/v2/account/position/allPosition"
    res = requests.get(base + path, headers=get_headers("GET", path)).json()
    data = res if isinstance(res, list) else res.get('data', [])
    
    if not data:
        print("❌ No active positions found in 'allPosition'. Checking Open Orders...")
    
    for p in data:
        sym = p.get('symbol')
        size = p.get('total', p.get('positionQty', '0'))
        if float(size) > 0:
            print(f"🧨 Killing {size} of {sym}...")
            order_path = "/capi/v2/order/placeOrder"
            side = "3" if "long" in p.get('holdSide', 'long').lower() else "4"
            body = {"symbol": sym, "side": side, "type": "1", "size": str(size), "match_price": "1"}
            requests.post(base + order_path, headers=get_headers("POST", order_path, body), json=body)

    # Step 2: Cancel all pending orders (this is why your 'Available' might be 0)
    cancel_path = "/capi/v2/order/cancelAllOrders"
    # Note: Some WEEX versions require a productType like 'umcbl'
    for p_type in ['umcbl', 'dmcbl', 'cmcbl']:
        body = {"productType": p_type}
        requests.post(base + cancel_path, headers=get_headers("POST", cancel_path, body), json=body)
        print(f"🧹 Cancelled all pending {p_type} orders.")

if __name__ == "__main__":
    kill_everything()
