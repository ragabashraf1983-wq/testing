import os
import sys
import time
import subprocess
import webbrowser

def launch_native_app(url="http://localhost:8501"):
    """
    Launches the Streamlit URL in native application window mode without browser address bars or toolbars.
    Supports Microsoft Edge (built into all Windows PCs) and Google Chrome.
    """
    print(f"🍏 [Apple Dark OS] Launching Research Agent in Native App Mode at {url}...")
    
    if sys.platform == "win32":
        # 1. Try Microsoft Edge App Mode (default on Windows 10/11)
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
        ]
        for path in edge_paths:
            if os.path.exists(path):
                print("Found Microsoft Edge. Opening Native App Window...")
                subprocess.Popen([path, f"--app={url}", "--window-size=1400,900"])
                return

        # 2. Try Google Chrome App Mode
        chrome_paths = [
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for path in chrome_paths:
            if os.path.exists(path):
                print("Found Google Chrome. Opening Native App Window...")
                subprocess.Popen([path, f"--app={url}", "--window-size=1400,900"])
                return

    # Fallback for standard browsers or non-Windows platforms
    print("Opening in default browser...")
    webbrowser.open(url)

if __name__ == "__main__":
    # Wait 2 seconds for Streamlit server to initialize
    time.sleep(2)
    launch_native_app()
