@echo off
cd /d "%~dp0"

echo ============================================================
echo DeepSeek GEO Collector - Build Portable Package
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv\Scripts\python.exe not found.
    echo Please run setup_new_pc.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" scripts\build_portable_package.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    echo [FAILED] Portable package build failed.
    pause
    exit /b %EXIT_CODE%
)

echo ============================================================
echo [SUCCESS] Portable package generated.
echo Check the dist folder.
echo ============================================================
echo.

pause
exit /b 0
