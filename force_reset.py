import os, time, hmac, hashlib, requests, base64, json
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

def nuke():
    base = "https://api-contract.weex.com"
    
    print("🧹 1. Clearing all pending orders...")
    c_path = "/capi/v2/order/cancelAllOrder"
    c_res = requests.post(base + c_path, headers=get_headers("POST", c_path, {"symbol":"cmt_btcusdt"}), json={"symbol":"cmt_btcusdt"}).json()
    print(f"   Status: {c_res.get('msg', 'No response')}")

    print("\n⚡ 2. Attempting Global Close-All...")
    # This is a specialized shortcut for AI Wars participants
    ga_path = "/capi/v2/order/closeAllPosition"
    ga_res = requests.post(base + ga_path, headers=get_headers("POST", ga_path, {"symbol":"cmt_btcusdt"}), json={"symbol":"cmt_btcusdt"}).json()
    print(f"   Status: {ga_res.get('msg', 'Not supported or already closed')}")

    print("\n🔍 3. Scanning Account for hidden positions...")
    # Try the Account-level position endpoint
    p_path = "/capi/v2/account/allPosition"
    p_res = requests.get(base + p_path, headers=get_headers("GET", p_path)).json()
    
    positions = p_res.get('data', [])
    if not positions:
        # Fallback to secondary endpoint
        p_path = "/capi/v2/account/positions"
        p_res = requests.get(base + p_path, headers=get_headers("GET", p_path)).json()
        positions = p_res.get('data', [])

    if positions:
        print(f"   Found {len(positions)} active positions. Executing market terminations...")
        for pos in positions:
            symbol = pos.get('symbol')
            side = pos.get('holdSide')
            print(f"   🔪 Terminating {side} on {symbol}...")
            
            close_path = "/capi/v2/order/closePosition"
            close_body = {"symbol": symbol, "side": side}
            res = requests.post(base + close_path, headers=get_headers("POST", close_path, close_body), json=close_body).json()
            print(f"      Result: {res.get('msg')}")
    else:
        print("   No positions found in account scan. Balance should be freeing up.")

    print("\n✅ Final Check: If 'Available' is still 0, check WEEX App to see if funds are in 'Isolated' margin mode.")

if __name__ == "__main__":
    nuke()
