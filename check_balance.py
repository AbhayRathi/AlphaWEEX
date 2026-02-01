import os, time, hmac, hashlib, requests, base64, json
from dotenv import load_dotenv

load_dotenv()

def get_balance():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    api_pass = os.getenv("API_PASSWORD")
    
    # Using the standardized assets endpoint for a clearer view of USDT
    path = "/capi/v2/account/assets" 
    timestamp = str(int(time.time() * 1000))
    message = timestamp + "GET" + path
    
    signature = base64.b64encode(hmac.new(
        api_secret.encode('utf-8'), 
        message.encode('utf-8'), 
        hashlib.sha256
    ).digest()).decode('utf-8')

    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-PASSPHRASE": api_pass,
        "ACCESS-TIMESTAMP": timestamp,
        "Content-Type": "application/json"
    }
    
    try:
        url = "https://api-contract.weex.com" + path
        response = requests.get(url, headers=headers)
        res_json = response.json()
        print("\n💰 --- ACCOUNT ASSETS --- 💰")
        print(json.dumps(res_json, indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_balance()
