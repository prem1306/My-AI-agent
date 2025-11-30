import google.generativeai as genai
import os

# The key provided by the user
API_KEY = "YOUR_API_KEY"

def test_key():
    print(f"Testing API Key: {API_KEY[:10]}...")
    
    try:
        os.environ["GOOGLE_API_KEY"] = API_KEY
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        print("Sending request to Gemini (gemini-2.0-flash)...")
        response = model.generate_content("Say 'Hello' if you can hear me.")
        
        print("\nSUCCESS!")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print("\nFAILED!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        
        if "400" in str(e):
            print("\nPossible Cause: Bad Request (Invalid Key or Project not found).")
        elif "403" in str(e):
            print("\nPossible Cause: Permission Denied (API not enabled in Google Cloud Console).")
            print("Action: Go to https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com and enable it.")
        elif "429" in str(e):
            print("\nPossible Cause: Quota Exceeded.")
        
        return False

if __name__ == "__main__":
    import sys
    # Redirect stdout and stderr to a file
    with open("api_test_result.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        sys.stderr = f
        test_key()
