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

if "%EXIT_CODE%"=="0" (
    echo [SUCCESS] DeepSeek GEO pipeline completed.
) else if "%EXIT_CODE%"=="1" (
    echo [WARNING] DeepSeek GEO pipeline completed with warnings.
    echo GEO package was generated successfully.
) else if "%EXIT_CODE%"=="4" (
    echo [PAUSED] DeepSeek GEO pipeline paused.
    echo Checkpoint saved. Run again later and choose R to resume.
) else (
    echo [FAILED] DeepSeek GEO pipeline failed.
)

echo.
pause
exit /b %EXIT_CODE%
