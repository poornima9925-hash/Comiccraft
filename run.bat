@echo off
cd /d "%~dp0"

:: 1. Create and activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    python -m venv "venv"
)
call "venv\Scripts\activate.bat"

:: 2. Check .env and API credentials
if not exist ".env" (
    echo [ERROR] .env file not found.
    pause
    exit /b 1
)

findstr /i "your_gemini_api_key_here" ".env" >nul
if %errorlevel% equ 0 (
    echo [ERROR] Please set your real GEMINI_API_KEY in .env
    pause
    exit /b 1
)

findstr /i "your_huggingface_api_key_here" ".env" >nul
if %errorlevel% equ 0 (
    echo [ERROR] Please set your real HF_API_KEY in .env
    pause
    exit /b 1
)

:: 3. Upgrade pip and install prebuilt wheels
python -m pip install --upgrade pip wheel setuptools
pip install --prefer-binary -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Package installation failed.
    pause
    exit /b 1
)

:: 4. Run FastAPI Server
python -m uvicorn app.main:app --reload
pause