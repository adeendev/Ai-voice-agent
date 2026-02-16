# AI Voice Assistant Frontend

A modern React/Next.js frontend for the AI Booking Assistant with real-time voice interaction capabilities.

## Features

- 🎤 **Continuous Voice Recording**: Automatically listens and processes voice input
- 💬 **Real-time Chat Interface**: Displays conversation history with timestamps
- 🔊 **Audio Playback**: Plays AI responses with TTS
- 🔗 **Backend Integration**: Seamless connection to the Python backend
- 📱 **Responsive Design**: Modern UI with Tailwind CSS
- ⚡ **Performance Optimized**: Lightweight and fast audio processing
- 🛡️ **Error Handling**: Graceful handling of connection and audio errors

## Quick Start

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   ```

3. **Make sure the backend is running**:
   ```bash
   cd ..
   python main.py --text-only
   ```

4. **Open in Browser**:
   Navigate to `http://localhost:3000`

## Usage

1. **Connect**: Click the microphone button to connect to the backend
2. **Start Listening**: The assistant will continuously listen for your voice
3. **Speak**: Say commands like "Book a car wash at 3 PM tomorrow"
4. **View Responses**: See the conversation history and hear AI responses
5. **Stop**: Click the microphone button again to stop listening

## Architecture

### Components

- **VoiceAssistant**: Main component handling voice recording and chat
- **Audio Processing**: Web Audio API integration for recording
- **Chat Interface**: Real-time conversation display
- **Backend Communication**: API integration with the Python backend

### Key Features

- **Automatic Audio Chunking**: Records 4-second audio chunks
- **Continuous Listening**: Seamless voice interaction loop
- **Real-time Updates**: Instant conversation history updates
- **Audio Playback**: Automatic TTS response playback
- **Connection Management**: Robust backend connection handling

## Configuration

The VoiceAssistant component accepts these props:

```typescript
interface VoiceAssistantProps {
  backendUrl?: string;     // Default: 'http://localhost:8000'
  autoStart?: boolean;     // Default: false
}
```

## API Endpoints

The frontend communicates with these backend endpoints:

- `GET /health` - Health check
- `POST /api/process-audio` - Audio processing

## Browser Requirements

- Modern browser with Web Audio API support
- Microphone access permission
- HTTPS (for production deployment)

## Development

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Technologies

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Web Audio API** - Audio recording
- **Fetch API** - Backend communication

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**:
   - Allow microphone permissions in browser
   - Use HTTPS in production

2. **Backend Connection Failed**:
   - Ensure backend server is running on port 8000
   - Check CORS settings

3. **Audio Not Playing**:
   - Check browser audio permissions
   - Verify TTS audio URLs from backend

### Browser Compatibility

- Chrome 66+
- Firefox 60+
- Safari 11.1+
- Edge 79+

## Production Deployment

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Configure environment variables**:
   ```bash
   NEXT_PUBLIC_BACKEND_URL=https://your-backend-url.com
   ```

3. **Deploy to your preferred platform** (Vercel, Netlify, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the AI Booking Assistant system.