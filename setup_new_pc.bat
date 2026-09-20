@echo off
cd /d "%~dp0"

echo ============================================================
echo DeepSeek GEO Collector - New PC Setup
echo ============================================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo [OK] Existing virtual environment found.
    goto INSTALL
)

echo [1/4] Looking for Python 3.11...

py -3.11 --version >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] Python 3.11 found.
    py -3.11 -m venv .venv
    goto INSTALL
)

python --version >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo [ERROR] Python was not found.
    echo Please install Python 3.11 first.
    pause
    exit /b 1
)

echo [WARN] Python 3.11 launcher was not found.
echo Using system Python instead.
python -m venv .venv

:INSTALL

echo.
echo [2/4] Upgrading pip...

".venv\Scripts\python.exe" -m pip install --upgrade pip

if not %ERRORLEVEL%==0 (
    echo [ERROR] pip upgrade failed.
    pause
    exit /b 1
)

echo.
echo [3/4] Installing project dependencies...

".venv\Scripts\python.exe" -m pip install -e ".[dev]"

if not %ERRORLEVEL%==0 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [4/4] Running environment configuration...

".venv\Scripts\python.exe" scripts\setup_new_pc.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo [FAILED] Environment setup failed.
    pause
    exit /b %EXIT_CODE%
)

echo ============================================================
echo [SUCCESS] DeepSeek GEO Collector environment is ready.
echo ============================================================
echo.
echo Next:
echo 1. Make sure DeepSeek is logged in.
echo 2. Run run_deepseek_geo.bat
echo.

pause
exit /b 0
