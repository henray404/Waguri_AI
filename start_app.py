import os
import sys
import time
import subprocess
import threading
import re
from pyngrok import ngrok, conf

# --- Configuration ---
PORT = 8000
SCRIPT_JS_PATH = os.path.join("web", "script.js")

def update_frontend_url(new_url):
    """Update API_URL in web/script.js with the new Ngrok URL."""
    try:
        with open(SCRIPT_JS_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Regex to find API_URL
        # Matches: API_URL: 'http://...',
        pattern = r"(API_URL:\s*['\"])(.*?)(['\"])"
        replacement = f"\\1{new_url}/chat\\3"
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(SCRIPT_JS_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ Frontend updated: API_URL set to {new_url}/chat")
        else:
            print("⚠️  Warning: Could not find API_URL in script.js to update.")
            
    except Exception as e:
        print(f"❌ Error updating frontend: {e}")

def run_uvicorn():
    """Run Uvicorn server."""
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(PORT)]
    subprocess.run(cmd)

def main():
    print("\n" + "="*60)
    print("  🚀 Waguri AI - Auto Launcher (Server + Ngrok)")
    print("="*60 + "\n")

    # 1. Start Uvicorn in a separate thread
    print("⏳ Starting FastAPI Server...")
    server_thread = threading.Thread(target=run_uvicorn, daemon=True)
    server_thread.start()
    
    # Give it a moment to start
    time.sleep(3)

    # 2. Start Ngrok
    print("⏳ Starting Ngrok Tunnel...")
    try:
        # Get Ngrok Auth Token from env or ask user if missing
        # You can set it via: ngrok config add-authtoken <token>
        
        # Open a HTTP tunnel on the default port 8000
        public_url = ngrok.connect(PORT).public_url
        print(f"\n🎉 Ngrok Tunnel Active!")
        print(f"🌍 Public URL: {public_url}")
        print("-" * 60)
        
        # 3. Update Frontend
        update_frontend_url(public_url)
        
        print("-" * 60)
        print("📝 INSTRUCTIONS:")
        print("1. Copy the Public URL above.")
        print("2. If you are testing locally, open: http://localhost:8000")
        print("3. If you are testing from GitHub Pages/Public Internet:")
        print("   - The 'script.js' has been automatically updated.")
        print("   - Push the 'web/' folder changes to GitHub now if you want the live site to work.")
        print("-" * 60)
        print("Press CTRL+C to stop the server and tunnel.\n")

        # Keep main thread alive
        server_thread.join()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        ngrok.kill()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        ngrok.kill()
        sys.exit(1)

if __name__ == "__main__":
    main()
