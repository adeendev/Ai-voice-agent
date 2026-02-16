# Vertiqx AI Booking Assistant - Batch Files Guide

This guide explains how to use the batch files to start and manage the Vertiqx AI Booking Assistant system.

## 📁 Available Batch Files

### 1. `start_all.bat` - Complete Setup & Start
**Use this for first-time setup or when dependencies need to be installed**

```bash
.\start_all.bat
```

**What it does:**
- ✅ Checks Python and Node.js installation
- 🔧 Creates virtual environment (if needed)
- 📦 Installs Python dependencies from requirements.txt
- 📦 Installs frontend dependencies (npm install)
- 🚀 Starts API Server on http://localhost:8000
- 🌐 Starts Frontend on http://localhost:3000
- 📝 Creates log files in `logs/` directory
- 🌐 Opens frontend in browser

**When to use:**
- First time running the application
- After updating dependencies
- When you want a complete setup

---

### 2. `quick_start.bat` - Fast Start (Dependencies Required)
**Use this when dependencies are already installed**

```bash
.\quick_start.bat
```

**What it does:**
- 🔧 Activates virtual environment
- 🚀 Starts API Server immediately
- 🌐 Starts Frontend immediately
- 🌐 Opens frontend in browser
- ⚡ Much faster than start_all.bat

**When to use:**
- Daily development work
- When dependencies are already installed
- For quick testing

---

### 3. `stop_all.bat` - Stop All Services
**Use this to cleanly stop all running services**

```bash
.\stop_all.bat
```

**What it does:**
- 🛑 Stops API Server (port 8000)
- 🛑 Stops Frontend (port 3000)
- 🛑 Terminates background processes
- 🧹 Cleans up running services

**When to use:**
- When you're done working
- Before shutting down your computer
- To restart services cleanly

---

### 4. `dev_start.bat` - Development Menu
**Use this for development and testing individual components**

```bash
.\dev_start.bat
```

**What it provides:**
- 🔧 Start API Server only (debug mode)
- 🌐 Start Frontend only
- 🎤 Test Voice Agent
- 💾 Test Booking Database
- 🚀 Run All Services
- 🚪 Exit

**When to use:**
- Development and debugging
- Testing individual components
- Troubleshooting issues

---

## 🚀 Quick Start Guide

### For First Time Users:
1. Run `.\start_all.bat`
2. Wait for setup to complete (may take 5-10 minutes)
3. Frontend will open automatically in your browser
4. API will be available at http://localhost:8000

### For Daily Development:
1. Run `.\quick_start.bat`
2. Services start immediately
3. Frontend opens in browser

### To Stop Everything:
1. Run `.\stop_all.bat`
2. All services will be terminated cleanly

---

## 📡 Service URLs

Once started, you can access:

- **Frontend Application**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Health Check**: http://localhost:8000/api/health
- **API Documentation**: http://localhost:8000/docs (if available)

---

## 📝 Log Files

All services create log files in the `logs/` directory:

- `logs/api_server.log` - API server logs
- `logs/frontend.log` - Frontend development server logs
- `logs/audio_processor.log` - Audio processing logs
- `logs/audio_performance.log` - Audio performance metrics

---

## 🔧 System Requirements

### Prerequisites:
- **Python 3.11+** (with pip)
- **Node.js 18+** (with npm)
- **Windows 10/11**

### Environment Variables (Optional):
- `GEMINI_API_KEY` - For Google Gemini AI integration
- `GOOGLE_APPLICATION_CREDENTIALS` - For Google Calendar integration

---

## 🛠️ Troubleshooting

### Common Issues:

#### 1. "Python is not installed or not in PATH"
- Install Python from https://python.org
- Make sure to check "Add Python to PATH" during installation

#### 2. "Node.js is not installed or not in PATH"
- Install Node.js from https://nodejs.org
- Restart your terminal after installation

#### 3. Services won't start
- Run `.\stop_all.bat` first
- Then try `.\start_all.bat` again
- Check log files in `logs/` directory

#### 4. Port already in use
- Run `.\stop_all.bat` to free up ports
- Or change ports in the batch files if needed

#### 5. Dependencies installation fails
- Check your internet connection
- Try running as administrator
- Delete `venv/` folder and run `.\start_all.bat` again

---

## 🎯 Features Available

Once running, the system provides:

- 🎤 **Voice Assistant** - AI-powered voice interaction
- 📅 **Google Calendar Integration** - Automatic appointment scheduling
- 💾 **Booking Management** - Complete booking system
- 🔊 **Real-time Audio Processing** - Voice recognition and synthesis
- 📱 **WhatsApp Integration** - Automated customer communication
- 🤖 **AI Customer Support** - Intelligent response system
- 🌐 **Modern Web Interface** - React-based frontend

---

## 📞 Support

If you encounter issues:

1. Check the log files in `logs/` directory
2. Run `.\dev_start.bat` to test individual components
3. Ensure all prerequisites are installed
4. Try running `.\stop_all.bat` then `.\start_all.bat`

---

**Happy coding! 🚀**