@echo off
setlocal enabledelayedexpansion

:: Load environment variables from .env file
if exist .env (
    echo Loading environment variables from .env...
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
) else (
    echo Warning: .env file not found
)

:: Check if required variables are set
if "%NGROK_AUTHTOKEN%"=="" (
    echo Error: NGROK_AUTHTOKEN not found in .env file
    pause
    exit /b 1
)

if "%FLASK_PORT%"=="" (
    set FLASK_PORT=5000
    echo Using default Flask port: !FLASK_PORT!
)

:: Authenticate ngrok
echo Authenticating ngrok...
ngrok config add-authtoken %NGROK_AUTHTOKEN%

:: Start Flask server in background
echo Starting Flask server on port %FLASK_PORT%...
start /b python app.py

:: Wait for Flask to start
timeout /t 3 /nobreak >nul

:: Start ngrok tunnel
echo Starting ngrok tunnel...
start /b ngrok http %FLASK_PORT%

echo.
echo Your Flask app should now be accessible via ngrok!
echo Check the ngrok web interface at: http://127.0.0.1:4040
echo.
echo Press any key to stop both servers...
pause >nul

:: Kill Flask and ngrok processes
taskkill /f /im python.exe 2>nul
taskkill /f /im ngrok.exe 2>nul

echo Servers stopped.
pause