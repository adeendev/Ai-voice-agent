#!/usr/bin/env python3
"""
API Server for AI Booking Assistant
Provides REST API endpoints for the frontend to interact with the booking system.
"""

import os
import io
import json
import logging
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any

# Load environment variables from .env.local file
from dotenv import load_dotenv
load_dotenv('.env.local')

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import speech_recognition as sr

from booking_database import BookingDatabase
from vertiqx_voice_agent import VertiqxReceptionistAgent
from booking_manager import BookingManager
from google_calendar_integration import GoogleCalendarIntegration

# Optional audio processor import
try:
    from improved_audio_processor import RobustAudioProcessor
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️  Audio dependencies not installed. Audio features will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global variables for the application# Global components
db = None
ai_agent = None
audio_processor = None
recognizer = None
google_calendar = None

def initialize_components(model_name="gemma2:2b"):
    """Initialize all application components."""
    global db, ai_agent, audio_processor, recognizer, google_calendar
    
    try:
        # Initialize database
        db = BookingDatabase()
        logger.info("Database initialized")
        
        # Initialize Google Calendar integration
        try:
            google_calendar = GoogleCalendarIntegration()
            logger.info("Google Calendar integration initialized")
        except Exception as e:
            logger.warning(f"Google Calendar initialization failed: {e}")
            google_calendar = None
        
        # Initialize Vertiqx Voice Agent with Gemini
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables. Please set it for Gemini AI functionality.")
        
        ai_agent = VertiqxReceptionistAgent()
        ai_agent.model_name = model_name  # Set model name for compatibility
        logger.info("Vertiqx Voice Agent initialized with Gemini AI")
        
        # Initialize audio processor if available
        if AUDIO_AVAILABLE:
            try:
                audio_processor = RobustAudioProcessor()
                recognizer = sr.Recognizer()
                logger.info("Robust audio processing enabled")
            except Exception as e:
                logger.warning(f"Audio initialization failed: {e}")
                audio_processor = None
                recognizer = None
        
        logger.info("All components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'database': db is not None,
            'ai_agent': ai_agent is not None,
            'audio_processor': audio_processor is not None,
            'google_calendar': google_calendar is not None,
            'model_name': ai_agent.model_name if ai_agent else None
        }
    })

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """Process audio file and return transcription and AI response."""
    try:
        logger.info("Received audio processing request")
        
        # Check if audio components are available
        if not AUDIO_AVAILABLE:
            logger.error("Audio processing not available - dependencies missing")
            return jsonify({'error': 'Audio processing not available'}), 400
        
        if not recognizer:
            logger.error("Speech recognizer not initialized")
            return jsonify({'error': 'Speech recognition not available'}), 400
        
        # Check if audio file is provided
        if 'audio' not in request.files:
            logger.error("No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            logger.error("Empty audio filename")
            return jsonify({'error': 'No audio file selected'}), 400
        
        logger.info(f"Processing audio file: {audio_file.filename}")
        
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name
        
        try:
            # Transcribe audio
            transcription = transcribe_audio(temp_audio_path)
            
            if not transcription or not transcription.strip():
                return jsonify({
                    'transcription': '',
                    'response': '',
                    'message': 'No speech detected'
                })
            
            # Process through Vertiqx Enhanced Agent
            ai_response = ai_agent.process_message(transcription)
            
            # Generate TTS audio for response
            audio_url = None
            if audio_processor and ai_response:
                try:
                    audio_url = generate_tts_audio(ai_response)
                except Exception as e:
                    logger.warning(f"TTS generation failed: {e}")
            
            return jsonify({
                'transcription': transcription,
                'response': ai_response,
                'audio_url': audio_url,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return jsonify({'error': 'Failed to process audio'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process text input and return AI response."""
    try:
        logger.info("Received chat request")
        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        if not data or 'message' not in data:
            logger.error("No message provided in request")
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            logger.error("Empty message provided")
            return jsonify({'error': 'Empty message'}), 400
        
        logger.info(f"Processing message: {user_message}")
        
        # Check if AI agent is available
        if not ai_agent:
            logger.error("AI agent not initialized")
            return jsonify({'error': 'AI agent not available'}), 500
        
        # Process through Vertiqx Enhanced Agent
        ai_response = ai_agent.process_message(user_message)
        logger.info(f"AI response: {ai_response}")
        
        # Generate TTS audio for response
        audio_url = None
        if audio_processor and ai_response:
            try:
                audio_url = generate_tts_audio(ai_response)
                logger.info(f"Generated TTS audio: {audio_url}")
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")
        
        response_data = {
            'response': ai_response,
            'audio_url': audio_url,
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Sending response: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500

@app.route('/api/voice-agent', methods=['POST'])
def voice_agent():
    """Ultra-fast voice agent endpoint with memory management."""
    try:
        import time
        start_time = time.time()
        logger.info("Received voice agent request")
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Handle session management
        session_id = data.get('session_id', 'default')
        action = data.get('action', 'chat')  # chat, reset, status
        
        if not ai_agent:
            return jsonify({'error': 'Voice agent not available'}), 500
        
        # Handle different actions
        if action == 'reset':
            ai_agent.reset_conversation()
            response_time = (time.time() - start_time) * 1000
            return jsonify({
                'response': 'Memory reset. How can I help you today?',
                'booking_status': ai_agent.get_booking_status(),
                'response_time_ms': round(response_time, 1),
                'timestamp': datetime.now().isoformat()
            })
        
        elif action == 'status':
            response_time = (time.time() - start_time) * 1000
            return jsonify({
                'booking_status': ai_agent.get_booking_status(),
                'response_time_ms': round(response_time, 1),
                'timestamp': datetime.now().isoformat()
            })
        
        # Process message through voice agent
        ai_response = ai_agent.process_message(user_message)
        
        # Generate TTS audio for response if available
        audio_url = None
        if audio_processor and ai_response:
            try:
                audio_url = generate_tts_audio(ai_response)
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")
        
        response_time = (time.time() - start_time) * 1000
        
        response_data = {
            'response': ai_response,
            'audio_url': audio_url,
            'booking_status': ai_agent.get_booking_status(),
            'response_time_ms': round(response_time, 1),
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        }
        
        logger.info(f"Voice agent response in {response_time:.1f}ms")
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in voice agent endpoint: {e}")
        return jsonify({'error': 'Failed to process voice agent request'}), 500

@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files from static directory."""
    try:
        audio_dir = os.path.join("static", "audio")
        audio_path = os.path.join(audio_dir, filename)
        
        if os.path.exists(audio_path):
            return send_file(audio_path, mimetype='audio/wav')
        else:
            logger.warning(f"Audio file not found: {audio_path}")
            return jsonify({'error': 'Audio file not found'}), 404
            
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        return jsonify({'error': 'Failed to serve audio'}), 500

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings or bookings for a specific customer."""
    try:
        customer_name = request.args.get('customer_name')
        
        if customer_name:
            # Get bookings for specific customer
            bookings = db.get_bookings(customer_name=customer_name)
        else:
            # Get all bookings using BookingManager
            booking_manager = BookingManager()
            all_bookings = booking_manager.get_all_bookings()
            # Convert Booking objects to dictionaries
            bookings = [booking.to_dict() for booking in all_bookings]
        
        return jsonify({'bookings': bookings})
        
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        return jsonify({'error': 'Failed to get bookings'}), 500

@app.route('/api/services', methods=['GET'])
def get_services():
    """Get all available services."""
    try:
        services = db.get_services()
        return jsonify({'services': services})
        
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        return jsonify({'error': 'Failed to get services'}), 500

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file to text using improved audio processor."""
    if not audio_processor:
        raise Exception("Audio processor not available")
    
    try:
        # Use improved audio processor with format conversion support
        text, success = audio_processor.transcribe_audio_file(audio_path)
        
        if success and text:
            logger.info(f"Audio transcription successful: {text[:50]}...")
            return text
        else:
            logger.warning("Audio transcription failed or returned empty result")
            return ""
            
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return ""

def generate_tts_audio(text: str) -> Optional[str]:
    """Generate TTS audio and return URL using improved audio processor."""
    if not audio_processor:
        return None
    
    try:
        # Create audio directory if it doesn't exist
        audio_dir = os.path.join("static", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"response_{timestamp}.wav"
        audio_path = os.path.join(audio_dir, filename)
        
        # Generate TTS audio using improved processor
        result_path = audio_processor.generate_tts_audio(text, audio_path)
        
        if result_path and os.path.exists(result_path):
            # Return URL for the audio file
            return f"/api/audio/{filename}"
        else:
            logger.error("TTS audio generation failed")
            return None
        
    except Exception as e:
        logger.error(f"Error generating TTS audio: {e}")
        return None

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Main entry point for the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Booking Assistant API Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--model-name', default='phi3:mini', help='Ollama model name to use')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        app.debug = True
    
    # Initialize components
    if not initialize_components(args.model_name):
        print("❌ Failed to initialize components")
        return
    
    print(f"🚀 Starting AI Booking Assistant API Server")
    print(f"📡 Server: http://{args.host}:{args.port}")
    print(f"🤖 Model: {args.model_name}")
    print(f"🎤 Audio: {'Enabled' if AUDIO_AVAILABLE else 'Disabled'}")
    print("=" * 50)
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()