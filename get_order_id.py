import os, time, hmac, hashlib, requests, base64, json
from dotenv import load_dotenv
load_dotenv()

def get_ids():
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    base_url = "https://api-contract.weex.com"
    # Testing the most likely symbols for your BTC/ETH trades
    symbols = ["cmt_btcusdt", "cmt_ethusdt", "btcusdt_umcbl", "ethusdt_umcbl"]
    
    print("🔎 Searching for Order IDs...")
    for sym in symbols:
        path = f"/capi/v2/order/history?symbol={sym}"
        ts = str(int(time.time() * 1000))
        msg = ts + "GET" + path
        sig = base64.b64encode(hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).digest()).decode()
        headers = {"ACCESS-KEY": api_key, "ACCESS-SIGN": sig, "ACCESS-PASSPHRASE": api_pass, "ACCESS-TIMESTAMP": ts}
        
        try:
            res = requests.get(base_url + path, headers=headers).json()
            # Safety check for NoneType
            data = res if isinstance(res, list) else res.get('data', [])
            if not data: data = []
            
            for o in data[:3]:
                print(f"✅ FOUND | ID: {o.get('orderId')} | Sym: {o.get('symbol')} | Side: {o.get('side')}")
        except:
            continue

if __name__ == "__main__":
    get_ids()
