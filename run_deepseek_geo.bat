@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv\Scripts\python.exe not found.
    echo Please create the virtual environment first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" scripts\run_deepseek_geo.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo [FAILED] DeepSeek GEO pipeline failed.
) else (
    echo [SUCCESS] DeepSeek GEO pipeline completed.
)

echo.
pause
exit /b %EXIT_CODE%
