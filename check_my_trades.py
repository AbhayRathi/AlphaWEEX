import os, time, hmac, hashlib, json, requests, base64
from dotenv import load_dotenv

load_dotenv()

def weex_request(path):
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_pass = os.getenv("API_PASSWORD")
    url = "https://api-contract.weex.com" + path
    timestamp = str(int(time.time() * 1000))
    
    # Signature
    message = timestamp + "GET" + path
    signature = base64.b64encode(hmac.new(
        api_secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256
    ).digest()).decode('utf-8')

    headers = {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": signature,
        "ACCESS-PASSPHRASE": api_pass, "ACCESS-TIMESTAMP": timestamp
    }
    
    try:
        response = requests.get(url, headers=headers)
        res_json = response.json()
        # Handle if WEEX returns a list directly or a dict with 'data'
        if isinstance(res_json, list):
            return res_json
        return res_json.get('data', [])
    except:
        return []

print("🔍 Checking WEEX for active trades...")

# 1. Check Positions
positions = weex_request("/capi/v2/account/position/allPosition")
if positions and len(positions) > 0:
    print("\n✅ ACTIVE POSITIONS:")
    for p in positions:
        # The keys might be different depending on the specific V2 version
        sym = p.get('symbol', 'Unknown').upper()
        side = p.get('holdSide', p.get('side', 'N/A'))
        size = p.get('total', p.get('positionQty', '0'))
        pnl = p.get('unrealizedPL', p.get('unrealizedProfit', '0'))
        print(f"💰 {sym} | {side} | Size: {size} | PnL: {pnl} USDT")
else:
    print("❌ No active positions found.")

# 2. Check Open Orders
orders = weex_request("/capi/v2/order/currentOrders")
if orders and len(orders) > 0:
    print("\n⏳ PENDING ORDERS:")
    for o in orders:
        print(f"📝 {o.get('symbol','').upper()} | {o.get('side','')} | Price: {o.get('price','')} | Size: {o.get('size','')}")
else:
    print("❌ No pending orders found.")
