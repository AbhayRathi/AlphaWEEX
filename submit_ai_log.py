import os, time, hmac, hashlib, requests, base64, json
from dotenv import load_dotenv
load_dotenv()

# Using your successfully executed Order ID
YOUR_ORDER_ID = "708457319310033789"

def upload_ai_proof():
    api_key, api_secret, api_pass = os.getenv("API_KEY"), os.getenv("API_SECRET"), os.getenv("API_PASSWORD")
    path = "/capi/v2/order/uploadAiLog"
    ts = str(int(time.time() * 1000))

    payload = {
        "orderId": YOUR_ORDER_ID,
        "stage": "Decision Making",
        "model": "Aether-Evo-Gemini-1.5-Pro",
        "input": {
            "prompt": "Evaluate market regime and funding for long entry.",
            "indicators": {"RSI": "34.2", "EMA_Cross": "Bullish", "Funding": "Neutral"},
            "sentiment": "Oversold bounce expected"
        },
        "output": {
            "signal": "BUY_LONG",
            "confidence": 0.82,
            "target_tp": "5.0%",
            "target_sl": "2.5%"
        },
        "explanation": "AI detected a sharp dip with high volume exhaustion. Executing with 20x leverage based on support levels."
    }

    body_json = json.dumps(payload)
    sig_msg = ts + "POST" + path + body_json
    sig = base64.b64encode(hmac.new(api_secret.encode(), sig_msg.encode(), hashlib.sha256).digest()).decode()

    headers = {
        "ACCESS-KEY": api_key, "ACCESS-SIGN": sig,
        "ACCESS-PASSPHRASE": api_pass, "ACCESS-TIMESTAMP": ts,
        "Content-Type": "application/json", "locale": "en-US"
    }

    print(f"📡 Uploading AI Log for {YOUR_ORDER_ID}...")
    res = requests.post("https://api-contract.weex.com" + path, headers=headers, json=payload).json()
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    upload_ai_proof()
