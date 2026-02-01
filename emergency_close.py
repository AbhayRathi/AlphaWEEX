import os
import json
import time
import requests
import hmac
import hashlib
import base64
from dotenv import load_dotenv

load_dotenv()

def final_ai_wars_close():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    passphrase = os.getenv("API_PASSWORD")
    base_url = "https://api-contract.weex.com"

    symbols = ["cmt_btcusdt", "cmt_ethusdt"]
    
    for symbol in symbols:
        print(f"🚀 Closing {symbol}...")
        
        timestamp = str(int(time.time() * 1000))
        method = "POST"
        request_path = "/capi/v2/order/closePositions"
        body = json.dumps({"symbol": symbol}, separators=(',', ':'))
        
        # Signature: TIMESTAMP + METHOD + PATH + QUERY(empty) + BODY
        sign_str = timestamp + method + request_path + "" + body
        
        hash_obj = hmac.new(api_secret.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256)
        signature = base64.b64encode(hash_obj.digest()).decode('utf-8')

        headers = {
            "ACCESS-KEY": api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-PASSPHRASE": passphrase,
            "ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
            "locale": "en-US"
        }

        try:
            response = requests.post(base_url + request_path, headers=headers, data=body)
            data = response.json()
            
            # Since WEEX returned a list, we handle it here:
            if isinstance(data, list):
                for item in data:
                    if item.get("success"):
                        print(f"✅ SUCCESS: Position {item.get('positionId')} closed.")
                    else:
                        print(f"❌ Failed: {item.get('errorMessage')}")
            elif isinstance(data, dict):
                if data.get("code") == "00000" or data.get("success"):
                    print(f"✅ SUCCESS: {symbol} closed.")
                else:
                    print(f"❌ Error: {data.get('msg', 'Unknown Error')}")
                    
        except Exception as e:
            print(f"❌ Parsing Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    final_ai_wars_close()
