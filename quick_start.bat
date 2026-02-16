@echo off
echo ========================================
echo    Vertiqx AI - Quick Start
echo    (Dependencies must be pre-installed)
echo ========================================
echo.

:: Set the project directory
cd /d "%~dp0"

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found. Using system Python.
)

:: Create log directory if it doesn't exist
if not exist "logs\" mkdir logs

echo.
echo 🚀 Starting services...
echo.

:: Start API Server in background
echo 🔧 Starting API Server on http://localhost:8000...
start "API Server" cmd /c "call venv\Scripts\activate.bat && python api_server.py --host localhost --port 8000 > logs\api_server.log 2>&1"

:: Wait a moment for API server to start
timeout /t 2 /nobreak >nul

:: Start Frontend in background
echo 🌐 Starting Frontend on http://localhost:3000...
start "Frontend" cmd /c "cd frontend && npm run dev > ..\logs\frontend.log 2>&1"

:: Wait a moment for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo ✅ Services started!
echo.
echo 📡 API Server: http://localhost:8000
echo 🌐 Frontend:   http://localhost:3000
echo 📋 Health:     http://localhost:8000/api/health
echo.
echo 📝 Logs: logs\api_server.log, logs\frontend.log
echo.
echo 🛑 To stop services, run: stop_all.bat
echo.

:: Open frontend in browser
echo Opening frontend in browser...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo 🎉 Vertiqx AI Booking Assistant is ready!
echo.
pause