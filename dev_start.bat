@echo off
echo ========================================
echo    Vertiqx AI - Development Mode
echo ========================================
echo.

:: Set the project directory
cd /d "%~dp0"

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
) else (
    echo ⚠️  Virtual environment not found. Run start_all.bat first.
)

echo.
echo 🔧 Development Options:
echo.
echo 1. Start API Server only (debug mode)
echo 2. Start Frontend only
echo 3. Test Voice Agent
echo 4. Test Booking Database
echo 5. Run All Services
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto api_only
if "%choice%"=="2" goto frontend_only
if "%choice%"=="3" goto test_voice
if "%choice%"=="4" goto test_db
if "%choice%"=="5" goto all_services
if "%choice%"=="6" goto exit

:api_only
echo.
echo 🔧 Starting API Server in debug mode...
python api_server.py --host localhost --port 8000 --debug
goto end

:frontend_only
echo.
echo 🌐 Starting Frontend development server...
cd frontend
npm run dev
goto end

:test_voice
echo.
echo 🎤 Testing Voice Agent...
python vertiqx_voice_agent.py
goto end

:test_db
echo.
echo 💾 Testing Booking Database...
python -c "from booking_database import BookingDatabase; db = BookingDatabase(); print('✅ Database connection successful'); db.close()"
goto end

:all_services
echo.
echo 🚀 Starting all services...
call start_all.bat
goto end

:exit
echo.
echo 👋 Goodbye!
goto end

:end
echo.
pause