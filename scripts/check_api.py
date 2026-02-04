import requests
import sys

def check_api():
    url = "http://localhost:10086/api/llm/presets"
    print(f"Checking API endpoint: {url}")
    try:
        # Try GET first
        resp = requests.get(url)
        print(f"GET status: {resp.status_code}")
        
        if resp.status_code == 404:
            print("Error: Endpoint not found (404). Backend not updated?")
            return False
        
        # Try POST (with invalid data to check if method is allowed)
        # We expect 422 (Validation Error) or 200/400, but NOT 405
        resp = requests.post(url, json={})
        print(f"POST status: {resp.status_code}")
        
        if resp.status_code == 405:
            print("Error: Method Not Allowed (405). POST method missing!")
            return False
            
        print("Success: API endpoint exists and accepts POST.")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    if check_api():
        sys.exit(0)
    else:
        sys.exit(1)