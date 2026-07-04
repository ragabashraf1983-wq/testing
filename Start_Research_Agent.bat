@echo off
TITLE Autonomous Research Agent (Apple Dark OS Edition) - Windows Launcher
COLOR 0B

echo ===============================================================================
echo     🍏 APPLE DARK OS EDITION - AUTONOMOUS ACADEMIC RESEARCH AGENT
echo     100%% Open-Source • Free Academic APIs • Windows Native App Mode
echo ===============================================================================
echo.

echo [1/4] Verifying Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please download Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b
)

echo [2/4] Checking Python Virtual Environment (.venv)...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo [3/4] Activating Environment and Installing Packages...
call .venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo.
echo [4/4] Checking Local Ollama Status (Optional for Live Local LLMs)...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Ollama detected at http://localhost:11434!
) else (
    echo [NOTICE] Ollama server not running. Running in Simulation Mode by default!
)

echo.
echo ===============================================================================
echo   STARTING APPLE DARK OS DESKTOP APPLICATION...
echo ===============================================================================
echo Press Ctrl+C in this console window to shut down the backend server.
echo.

:: Launch desktop app window opener in background after 2 seconds
start /b python desktop_launcher.py

:: Start Streamlit server without auto-opening default browser tabs
streamlit run app.py --server.headless true
pause
