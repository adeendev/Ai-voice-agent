@echo off
echo ========================================
echo    Vertiqx AI Booking Assistant
echo    Stopping All Services
echo ========================================
echo.

:: Kill processes by window title
echo 🛑 Stopping API Server...
taskkill /FI "WINDOWTITLE eq API Server*" /T /F >nul 2>&1

echo 🛑 Stopping Frontend...
taskkill /FI "WINDOWTITLE eq Frontend*" /T /F >nul 2>&1

:: Kill processes by port (backup method)
echo 🛑 Stopping processes on port 8000 (API Server)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo 🛑 Stopping processes on port 3000 (Frontend)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Kill any remaining Node.js processes (be careful with this)
echo 🛑 Stopping remaining Node.js processes...
taskkill /IM node.exe /F >nul 2>&1

:: Kill any remaining Python processes related to our app
echo 🛑 Stopping Python processes...
wmic process where "name='python.exe' and commandline like '%%api_server.py%%'" delete >nul 2>&1

echo.
echo ✅ All services stopped successfully!
echo.
echo 📝 Service status:
echo    - API Server (port 8000): Stopped
echo    - Frontend (port 3000): Stopped
echo    - Background processes: Terminated
echo.
echo 💡 To restart services, run 'start_all.bat'
echo.
pause