@echo off
echo ========================================
echo    Vertiqx AI Booking Assistant
echo    Starting All Services
echo ========================================
echo.

:: Set the project directory
cd /d "%~dp0"

:: Check if Python is available
echo 🔍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

:: Check if Node.js is available
echo 🔍 Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js and try again
    pause
    exit /b 1
) else (
    echo ✅ Node.js found
)

:: Install Python dependencies if needed
echo 📦 Setting up Python environment...
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

:: Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install requirements
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

:: Install frontend dependencies if needed
echo 📦 Setting up Frontend environment...
cd frontend
if not exist "node_modules\" (
    echo Installing frontend dependencies...
    npm install
    if errorlevel 1 (
        echo ❌ Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    echo ✅ Frontend dependencies installed
) else (
    echo ✅ Frontend dependencies already installed
)
cd ..

echo.
echo 🚀 Starting services...
echo.

:: Create log directory if it doesn't exist
if not exist "logs\" mkdir logs

:: Start API Server in background
echo 🔧 Starting API Server on http://localhost:8000...
start "API Server" cmd /c "call venv\Scripts\activate.bat && python api_server.py --host localhost --port 8000 > logs\api_server.log 2>&1"

:: Wait a moment for API server to start
timeout /t 3 /nobreak >nul

:: Start Frontend in background
echo 🌐 Starting Frontend on http://localhost:3000...
start "Frontend" cmd /c "cd frontend && npm run dev > ..\logs\frontend.log 2>&1"

:: Wait a moment for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo ✅ All services started successfully!
echo.
echo 📡 API Server: http://localhost:8000
echo 🌐 Frontend:   http://localhost:3000
echo 📋 API Health: http://localhost:8000/api/health
echo.
echo 📝 Logs are saved in the 'logs' directory:
echo    - API Server: logs\api_server.log
echo    - Frontend:   logs\frontend.log
echo.
echo 🔧 Available Services:
echo    - Voice Assistant with Google Calendar integration
echo    - Booking management system
echo    - Real-time audio processing
echo    - WhatsApp automation
echo    - AI customer support
echo.
echo ⚠️  Important Notes:
echo    - Make sure to set GOOGLE_API_KEY in your environment for Gemini AI
echo    - Google Calendar integration requires proper OAuth setup
echo    - Audio features require microphone permissions
echo.
echo 🛑 To stop all services, close this window or press Ctrl+C
echo    Then run 'stop_all.bat' to ensure clean shutdown
echo.
echo Press any key to open the frontend in your browser...
pause >nul

:: Open frontend in default browser
start http://localhost:3000

echo.
echo 🎉 Setup complete! The application is now running.
echo.
echo 💡 Quick Start:
echo    1. Open http://localhost:3000 in your browser
echo    2. Test the voice assistant
echo    3. Try booking an appointment
echo    4. Check the booking management features
echo.
echo Press any key to exit this setup window...
pause >nul