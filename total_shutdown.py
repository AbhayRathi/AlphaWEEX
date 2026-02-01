import os, requests, time, hmac, hashlib, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_headers(method, path, body=""):
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASS")
    ts = str(int(time.time() * 1000))
    msg = ts + method.upper() + path + (json.dumps(body) if body else "")
    sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
    return {"ACCESS-KEY":api_key,"ACCESS-SIGN":sig,"ACCESS-PASSPHRASE":api_pass,"ACCESS-TIMESTAMP":ts,"Content-Type":"application/json"}

def kill_everything():
    base = "https://api-contract.weex.com"
    
    # 1. Broadest possible Position Search
    print("🛰️ Scanning all account types (USDT-M and USD-M)...")
    all_pos_path = "/capi/v2/account/allPosition"
    res = requests.get(base + all_pos_path, headers=get_headers("GET", all_pos_path)).json()
    
    positions = res.get('data', [])
    if positions:
        print(f"🔥 Found {len(positions)} hidden positions. Nunking them now...")
        for pos in positions:
            symbol = pos['symbol']
            side = pos['holdSide']
            print(f"   - Closing {side} on {symbol}...")
            close_path = "/capi/v2/order/closePosition"
            close_body = {"symbol": symbol, "side": side}
            requests.post(base + close_path, headers=get_headers("POST", close_path, close_body), json=close_body)
    
    # 2. Broadest possible Order Cancel
    print("🛑 Cancelling all pending orders for ALL symbols...")
    cancel_path = "/capi/v2/order/cancelAllOrder"
    # We use an empty dict to signal 'all symbols'
    requests.post(base + cancel_path, headers=get_headers("POST", cancel_path, {}), json={})

    # 3. Final Margin Check (Where is the money?)
    print("\n💰 FINAL ASSET RECONCILIATION:")
    assets_path = "/capi/v2/account/assets"
    res_assets = requests.get(base + assets_path, headers=get_headers("GET", assets_path)).json()
    
    found_usdt = False
    for asset in res_assets.get('data', []):
        if float(asset.get('equity', 0)) > 0:
            found_usdt = True
            print(f"   [{asset.get('marginCoin')}] Equity: {asset.get('equity')} | Available: {asset.get('available')}")
            if float(asset.get('available')) == 0:
                print(f"   ⚠️ WARNING: Money is in {asset.get('marginCoin')} account but locked. Check for 'Copy Trading'.")

    if not found_usdt:
        print("   ❌ No assets found in Futures account. Checking Spot...")
        # Check spot as a last resort
        spot_res = requests.get("https://api-spot.weex.com/api/v2/account/assets", headers=get_headers("GET", "/api/v2/account/assets")).json()
        print(f"   Spot Result: {spot_res}")

if __name__ == "__main__":
    kill_everything()
