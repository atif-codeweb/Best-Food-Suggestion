"""
Islamabad/Rawalpindi Guide Starter

This module launches the Islamabad/Rawalpindi Restaurant & Picnic System by starting both the 
FastAPI backend server and Streamlit frontend application in the correct sequence.
It starts the API server in a background thread, confirms it's running,
then launches the Streamlit interface as the main process.

Usage:
   python starter.py

Dependencies:
   - uvicorn
   - streamlit
   - requests
   - fastapi
   - groq  (for AI assistant - free API key at console.groq.com)
"""

import subprocess
import threading
import time
import webbrowser
import os
from pathlib import Path

# ── Auto-load .env file so GROQ_API_KEY is always available ──────────────────
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

def start_fastapi_server():
    """Start the fastapi server in seperate process"""
    try:
        print("starting fastapi server....")
        subprocess.Popen(["uvicorn", "data.service:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    except Exception as e:
        print(f"Error starting fastapi server: {e}")
        return None
    
def start_streamlit_app():
    """Start the streamlit app"""
    try:
        print("starting the streamlit app....")
        subprocess.run(["streamlit","run","app_islamabad.py"])
    except Exception as e:
        print(f"Error starting streamlit app: {e}")


if __name__=="__main__":
    print("\n" + "="*50)
    print("🌳Islamabad/Rawalpindi Guide System")
    print("="*50 + "\n")

    #start fastapi server in seperate thread
    api_thread=threading.Thread(target=start_fastapi_server)
    api_thread.daemon=True
    api_thread.start()


    print("Waiting for api server to start")
    time.sleep(3)
    try:
        import requests
        response=requests.get("http://localhost:8000/api/health")
        if response.status_code==200:
            data=response.json()
            print(f"API server started successfully")
            print(f"   • Restaurants: {data.get('restaurants', 'N/A')}")
            print(f"   • Picnic Spots: {data.get('picnic_spots', 'N/A')}")
            webbrowser.open("http://localhost:8000/docs")
    except:
        print("Warning:Api server might not be running correctly")
    

    print(f"\n Launching streamlit interface...\n")
    start_streamlit_app()

