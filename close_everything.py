import os, time, hmac, hashlib, requests, base64, json
from dotenv import load_dotenv

load_dotenv()

def get_headers(method, path, body_str=""):
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_pass = os.getenv("API_PASSWORD")
    ts = str(int(time.time() * 1000))
    
    # WEEX Signature: timestamp + METHOD + path + body
    message = ts + method.upper() + path + body_str
    sig = base64.b64encode(hmac.new(
        api_secret.encode('utf-8'), 
        message.encode('utf-8'), 
        hashlib.sha256
    ).digest()).decode('utf-8')

    return {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": sig,
        "ACCESS-PASSPHRASE": api_pass,
        "ACCESS-TIMESTAMP": ts,
        "Content-Type": "application/json"
    }

def close_all():
    base_url = "https://api-contract.weex.com"
    path_pos = "/capi/v2/account/position/allPosition"
    
    print("🔍 Fetching all active positions...")
    headers = get_headers("GET", path_pos)
    res = requests.get(base_url + path_pos, headers=headers).json()
    
    # Handle both list and dict response formats
    positions = res if isinstance(res, list) else res.get('data', [])
    
    if not positions or len(positions) == 0:
        print("🤷 No active positions found to close.")
        return

    for p in positions:
        symbol = p.get('symbol')
        side = p.get('holdSide', p.get('side', '')).lower()
        # Some API versions use 'total', others 'positionQty'
        size = p.get('total', p.get('positionQty', '0'))
        
        if float(size) <= 0:
            print(f"skipping {symbol} (size is 0)")
            continue
            
        print(f"🧨 Attempting to close {size} of {symbol} ({side})...")
        
        # side 3 = close long, side 4 = close short
        close_side = "3" if "long" in side else "4"
        path_order = "/capi/v2/order/placeOrder"
        
        body = {
            "symbol": symbol,
            "side": close_side,
            "type": "1",          # Market Order
            "order_type": "0",    # Normal
            "size": str(size),
            "match_price": "1"    # Market price
        }
        
        body_json = json.dumps(body)
        post_headers = get_headers("POST", path_order, body_json)
        
        order_res = requests.post(base_url + path_order, headers=post_headers, json=body).json()
        
        status = order_res.get('msg', 'Error')
        code = order_res.get('code', 'Unknown')
        print(f"✅ Result: {status} (Code: {code})")

if __name__ == "__main__":
    close_all()
