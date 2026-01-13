import time
import json
from weex_qualifier import send_weex_request 

def finish_tasks():
    print("🎯 Finishing final Gateway task: Get Trade Details...")
    
    # Corrected Order ID from your successful trade
    order_id = "702893678267466621"
    
    # Param names must match the weex_qualifier.py definition (query_params)
    query = f"?symbol=cmt_btcusdt&orderId={order_id}"
    
    print(f"🔍 Fetching details for Order: {order_id}...")
    try:
        # Changed 'query_string' to 'query_params' to match your function
        resp_detail = send_weex_request("GET", "/capi/v2/order/fills", query_params=query)
        
        print(f"Response Status: {resp_detail.status_code}")
        print(f"Response Body: {resp_detail.text}")

        if "list" in resp_detail.text:
            print("\n🏆 GATEWAY TESTING COMPLETE!")
            print("You have successfully performed:")
            print("1. Balance Check")
            print("2. Price Check")
            print("3. Leverage Setting")
            print("4. Order Placement")
            print("5. Trade Detail Retrieval")
            print("\nYour account is now fully ready for the official start.")
        else:
            print("\n⚠️ The request went through, but the trade list was empty.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    finish_tasks()
