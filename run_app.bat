@echo off
cd /d "%~dp0"
if exist "..\.venv\Scripts\python.exe" (
    set "PYTHON=..\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)
echo Starting Emergency Ambulance Route System...
echo Python: %PYTHON%
"%PYTHON%" -c "import flask, requests; print('Dependencies OK')" > startup.log 2>&1
if errorlevel 1 (
    echo Dependency check failed. See startup.log
    type startup.log
    pause
    exit /b 1
)
start "Emergency Ambulance Route Server" cmd /k ""%PYTHON%" app.py"
timeout /t 3 /nobreak >nul
start "Emergency Ambulance Route Browser" http://127.0.0.1:5000/login
echo Flask server started in a separate window.
echo Close that server window to stop the website.
pause
