@echo off
TITLE Autonomous Academic Research Agent - Windows Launcher
COLOR 0A

echo ===============================================================================
echo     AUTO-ACADEMIC RESEARCH AGENT - 100%% OPEN SOURCE & FREE ARCHITECTURE
echo ===============================================================================
echo.
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b
)

echo [2/4] Setting up Python Virtual Environment (.venv)...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo [3/4] Activating Virtual Environment and Installing Dependencies...
call .venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt

echo.
echo [4/4] Checking Local Ollama Status (Optional for Live Local LLMs)...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Ollama local server detected at http://localhost:11434!
) else (
    echo [NOTICE] Ollama server not detected at http://localhost:11434.
    echo Don't worry! You can run the dashboard in 'Simulation / Demo Mode' right away,
    echo or start Ollama in another terminal with: ollama run llama3
)

echo.
echo ===============================================================================
echo   STARTING WEB UI DASHBOARD AT http://localhost:8501 ...
echo ===============================================================================
echo Press Ctrl+C in this command window to stop the server at any time.
echo.

streamlit run app.py
pause
