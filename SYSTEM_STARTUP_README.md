# Vertiqx AI Booking Assistant - System Startup Guide

## 🚀 Quick Start

The fastest way to start the system is using the provided batch files:

### Option 1: Quick Start (Recommended)
```bash
# For quick startup (dependencies must be pre-installed)
quick_start.bat
```

### Option 2: Complete Setup
```bash
# For first-time setup or complete installation
start_all.bat
```

### Option 3: Development Mode
```bash
# For development with debugging options
dev_start.bat
```

## 📋 System Requirements

- **Python 3.8+** with pip
- **Node.js 18.0+** with npm
- **Windows OS** (batch files are Windows-specific)

## 🔧 Manual Startup Instructions

If you prefer to start services manually or need to troubleshoot:

### 1. Backend API Server

```bash
# Navigate to project directory
cd d:\Adeen\Projects\Tuning

# Activate virtual environment
call venv\Scripts\activate.bat

# Start API server
python api_server.py --host localhost --port 8000
```

**Expected Output:**
```
🚀 Starting AI Booking Assistant API Server
📡 Server: http://localhost:8000
🤖 Model: phi3:mini
🎤 Audio: Enabled
* Running on http://localhost:8000
```

### 2. Frontend Application

```bash
# Navigate to frontend directory
cd d:\Adeen\Projects\Tuning\frontend

# Start development server
npm run dev
```

**Expected Output:**
```
▲ Next.js 14.0.0
- Local: http://localhost:3000
✓ Ready in 2.6s
```

## 🌐 Access Points

Once both services are running:

- **Frontend Application**: http://localhost:3000
- **API Server**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health
- **API Documentation**: Available through the API endpoints

## 📁 Project Structure

```
d:\Adeen\Projects\Tuning\
├── api_server.py              # Main API server
├── vertiqx_voice_agent.py     # AI voice agent
├── booking_database.py        # Database management
├── booking_manager.py         # Booking logic
├── google_calendar_integration.py # Calendar integration
├── frontend/                  # Next.js frontend application
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   └── package.json          # Frontend dependencies
├── venv/                     # Python virtual environment
├── logs/                     # Application logs
├── static/audio/             # Generated audio files
└── *.bat                     # Startup batch files
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Python Not Found
```
❌ Python is not installed or not in PATH
```
**Solution**: Install Python 3.8+ and ensure it's in your system PATH.

#### 2. Node.js Not Found
```
❌ Node.js is not installed or not in PATH
```
**Solution**: Install Node.js 18.0+ from https://nodejs.org/

#### 3. Virtual Environment Issues
```
⚠️ Virtual environment not found. Run start_all.bat first.
```
**Solution**: Run `start_all.bat` to create and set up the virtual environment.

#### 4. Port Already in Use
```
Address already in use
```
**Solution**: 
- Check if services are already running
- Use `stop_all.bat` to stop existing services
- Or change ports in the startup commands

#### 5. Missing Dependencies
```
ModuleNotFoundError: No module named 'flask'
```
**Solution**: 
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### Environment Variables

The system uses several environment variables for enhanced functionality:

- `GOOGLE_API_KEY`: For Gemini AI functionality
- `GEMINI_API_KEY`: Alternative for Gemini AI
- Google Calendar credentials in `token.pickle`

## 📊 Service Status Monitoring

### Check if Services are Running

1. **API Server**: Visit http://localhost:8000/api/health
2. **Frontend**: Visit http://localhost:3000
3. **Process Check**: Use Task Manager to look for Python and Node processes

### Log Files

Monitor these log files for debugging:
- `logs/api_server.log` - API server logs
- `logs/frontend.log` - Frontend development server logs
- `logs/audio_processor.log` - Audio processing logs

## 🛑 Stopping Services

### Using Batch File
```bash
stop_all.bat
```

### Manual Stop
- Press `Ctrl+C` in each terminal window
- Or close the terminal windows

## 🔄 Restart Services

To restart after code changes:
1. Stop all services (`stop_all.bat` or `Ctrl+C`)
2. Start again (`quick_start.bat`)

## 🎯 Development Tips

### For Backend Development
- Use `dev_start.bat` and select option 1 for API-only debugging
- API runs with debug mode for detailed error messages
- Check `logs/api_server.log` for detailed logging

### For Frontend Development
- Use `dev_start.bat` and select option 2 for frontend-only development
- Hot reload is enabled for instant updates
- Check browser console for frontend errors

### For Full Stack Development
- Use `quick_start.bat` for both services
- Both services support hot reload/auto-restart

## 📞 Support

If you encounter issues not covered in this guide:
1. Check the log files in the `logs/` directory
2. Ensure all dependencies are installed
3. Verify Python and Node.js versions meet requirements
4. Try running `start_all.bat` for a complete fresh setup

---

**Last Updated**: November 2024
**System Version**: 1.0.0