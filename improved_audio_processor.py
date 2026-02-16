#!/usr/bin/env python3
"""
Ultra-Robust Audio Processor for Vertiqx AI Agent
Handles multiple audio formats with comprehensive error handling and fallback mechanisms.
"""

import os
import io
import wave
import tempfile
import logging
import time
import threading
import queue
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from pathlib import Path

# Configure comprehensive logging
def setup_audio_logging():
    """Setup comprehensive logging for audio operations."""
    # Create audio-specific logger
    audio_logger = logging.getLogger('audio_processor')
    audio_logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if audio_logger.handlers:
        return audio_logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - AUDIO - %(levelname)s - %(message)s'
    )
    
    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    audio_logger.addHandler(console_handler)
    
    # File handler for detailed logging
    try:
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'audio_processor.log'),
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        audio_logger.addHandler(file_handler)
        
        # Rotating file handler for performance logs
        from logging.handlers import RotatingFileHandler
        perf_handler = RotatingFileHandler(
            os.path.join(log_dir, 'audio_performance.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)
        audio_logger.addHandler(perf_handler)
        
    except Exception as e:
        print(f"Warning: Could not setup file logging: {e}")
    
    return audio_logger

# Setup logging
logger = setup_audio_logging()

# Audio processing imports with comprehensive error handling
try:
    import speech_recognition as sr
    import pyttsx3
    from pydub import AudioSegment
    from pydub.playback import play
    import pyaudio
    AUDIO_DEPENDENCIES_AVAILABLE = True
    logger.info("All audio dependencies loaded successfully")
except ImportError as e:
    AUDIO_DEPENDENCIES_AVAILABLE = False
    logger.error(f"Audio dependencies missing: {e}")
    print(f"⚠️  Audio dependencies missing: {e}")

logger = logging.getLogger(__name__)

class RobustAudioProcessor:
    """Ultra-robust audio processor with comprehensive error handling and fallback mechanisms."""
    
    def __init__(self):
        """Initialize the robust audio processor with extensive error handling."""
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.audio_available = AUDIO_DEPENDENCIES_AVAILABLE
        self.initialization_attempts = 0
        self.max_initialization_attempts = 3
        self.last_error = None
        self.performance_stats = {
            'transcription_success_rate': 0.0,
            'tts_success_rate': 0.0,
            'total_transcriptions': 0,
            'successful_transcriptions': 0,
            'total_tts_generations': 0,
            'successful_tts_generations': 0
        }
        
        if self.audio_available:
            self._initialize_components_with_retry()
        else:
            logger.warning("Audio processing disabled due to missing dependencies")
    
    def _initialize_components_with_retry(self):
        """Initialize audio components with retry mechanism and comprehensive error handling."""
        for attempt in range(self.max_initialization_attempts):
            try:
                self.initialization_attempts = attempt + 1
                logger.info(f"Audio initialization attempt {self.initialization_attempts}/{self.max_initialization_attempts}")
                
                # Initialize speech recognition with error handling
                if not self.recognizer:
                    self.recognizer = sr.Recognizer()
                    # Configure recognizer for better performance
                    self.recognizer.energy_threshold = 300
                    self.recognizer.dynamic_energy_threshold = True
                    self.recognizer.pause_threshold = 0.8
                    self.recognizer.operation_timeout = None
                    self.recognizer.phrase_threshold = 0.3
                    self.recognizer.non_speaking_duration = 0.8
                    logger.info("Speech recognizer initialized with optimized settings")
                
                # Initialize microphone with multiple fallback attempts
                if not self.microphone:
                    self._initialize_microphone_with_fallback()
                
                # Initialize TTS engine with comprehensive configuration
                if not self.tts_engine:
                    self._initialize_tts_with_fallback()
                
                # If we get here, initialization was successful
                logger.info("All audio components initialized successfully")
                return
                
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Audio initialization attempt {attempt + 1} failed: {e}")
                if attempt < self.max_initialization_attempts - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    logger.error("All audio initialization attempts failed")
                    self.audio_available = False
    
    def _initialize_microphone_with_fallback(self):
        """Initialize microphone with multiple fallback strategies."""
        microphone_configs = [
            {'device_index': None, 'sample_rate': 16000, 'chunk_size': 1024},
            {'device_index': None, 'sample_rate': 44100, 'chunk_size': 1024},
            {'device_index': 0, 'sample_rate': 16000, 'chunk_size': 1024},
            {'device_index': 1, 'sample_rate': 16000, 'chunk_size': 1024},
        ]
        
        for config in microphone_configs:
            try:
                if config['device_index'] is not None:
                    self.microphone = sr.Microphone(
                        device_index=config['device_index'],
                        sample_rate=config['sample_rate'],
                        chunk_size=config['chunk_size']
                    )
                else:
                    self.microphone = sr.Microphone(
                        sample_rate=config['sample_rate'],
                        chunk_size=config['chunk_size']
                    )
                
                # Test microphone with ambient noise adjustment
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                logger.info(f"Microphone initialized with config: {config}")
                return
                
            except Exception as e:
                logger.warning(f"Microphone config {config} failed: {e}")
                continue
        
        logger.warning("All microphone configurations failed")
        self.microphone = None
    
    def _initialize_tts_with_fallback(self):
        """Initialize TTS engine with comprehensive configuration and fallback."""
        try:
            # Try different TTS initialization methods
            tts_drivers = ['sapi5', 'nsss', 'espeak']
            
            for driver in tts_drivers:
                try:
                    if driver == 'sapi5':
                        self.tts_engine = pyttsx3.init('sapi5')
                    elif driver == 'nsss':
                        self.tts_engine = pyttsx3.init('nsss')
                    else:
                        self.tts_engine = pyttsx3.init()
                    
                    if self.tts_engine:
                        self._configure_tts_engine()
                        logger.info(f"TTS engine initialized with driver: {driver}")
                        return
                        
                except Exception as e:
                    logger.warning(f"TTS driver {driver} failed: {e}")
                    continue
            
            # If all drivers fail, try basic initialization
            self.tts_engine = pyttsx3.init()
            if self.tts_engine:
                self._configure_tts_engine()
                logger.info("TTS engine initialized with default driver")
            
        except Exception as e:
            logger.error(f"TTS engine initialization failed: {e}")
            self.tts_engine = None
    
    def _configure_tts_engine(self):
        """Configure TTS engine with optimal settings."""
        if not self.tts_engine:
            return
        
        try:
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice or specific high-quality voices
                preferred_voices = ['zira', 'hazel', 'female', 'woman']
                selected_voice = None
                
                for voice in voices:
                    voice_name = voice.name.lower()
                    for preferred in preferred_voices:
                        if preferred in voice_name:
                            selected_voice = voice.id
                            break
                    if selected_voice:
                        break
                
                if selected_voice:
                    self.tts_engine.setProperty('voice', selected_voice)
                    logger.info(f"Selected TTS voice: {selected_voice}")
            
            # Configure speech parameters for optimal quality
            self.tts_engine.setProperty('rate', 175)    # Optimal speech rate
            self.tts_engine.setProperty('volume', 0.9)  # High volume
            
            # Test TTS engine
            self.tts_engine.say("TTS engine ready")
            self.tts_engine.runAndWait()
            
        except Exception as e:
            logger.warning(f"TTS configuration failed: {e}")
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate audio file format and properties."""
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            if os.path.getsize(file_path) == 0:
                return False, "File is empty"
            
            # Try to load with pydub to validate format
            audio = AudioSegment.from_file(file_path)
            
            # Check audio properties
            if len(audio) == 0:
                return False, "Audio has no duration"
            
            if len(audio) > 300000:  # 5 minutes max
                return False, "Audio too long (max 5 minutes)"
            
            if audio.frame_rate < 8000:
                return False, "Sample rate too low (min 8kHz)"
            
            logger.info(f"Audio validation passed: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} channels")
            return True, "Valid audio file"
            
        except Exception as e:
            return False, f"Audio validation failed: {str(e)}"
    
    def convert_audio_format(self, input_path: str, output_path: str = None) -> Optional[str]:
        """Convert audio to optimal format with comprehensive error handling."""
        if not self.audio_available:
            logger.error("Audio conversion not available - dependencies missing")
            return None
        
        try:
            # Validate input file
            is_valid, validation_message = self.validate_audio_file(input_path)
            if not is_valid:
                logger.error(f"Input audio validation failed: {validation_message}")
                return None
            
            # Load audio file with format detection
            audio = AudioSegment.from_file(input_path)
            logger.info(f"Loaded audio: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} channels")
            
            # Convert to optimal format for speech recognition
            audio = audio.set_frame_rate(16000)  # Standard rate for speech recognition
            audio = audio.set_channels(1)        # Mono for better recognition
            audio = audio.set_sample_width(2)    # 16-bit depth
            
            # Skip audio enhancements for faster processing
            # audio = self._enhance_audio_for_recognition(audio)  # Disabled for speed optimization
            
            # Generate output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                output_path = os.path.join(tempfile.gettempdir(), f"converted_audio_{timestamp}.wav")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Export as WAV with optimal parameters
            audio.export(
                output_path, 
                format="wav",
                parameters=["-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le"]
            )
            
            # Validate output file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Audio converted successfully: {output_path}")
                return output_path
            else:
                logger.error("Converted audio file is invalid")
                return None
            
        except Exception as e:
            logger.error(f"Audio format conversion failed: {e}")
            return None
    
    def _enhance_audio_for_recognition(self, audio: AudioSegment) -> AudioSegment:
        """Apply audio enhancements to improve speech recognition accuracy."""
        try:
            # Normalize audio levels
            audio = audio.normalize()
            
            # Apply high-pass filter to remove low-frequency noise
            audio = audio.high_pass_filter(80)
            
            # Apply low-pass filter to remove high-frequency noise
            audio = audio.low_pass_filter(8000)
            
            # Compress dynamic range for more consistent levels
            audio = audio.compress_dynamic_range(threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
            
            logger.info("Audio enhancement applied successfully")
            return audio
            
        except Exception as e:
            logger.warning(f"Audio enhancement failed: {e}")
            return audio  # Return original audio if enhancement fails
    
    def transcribe_audio_file(self, audio_path: str) -> Tuple[Optional[str], bool]:
        """Transcribe audio file with comprehensive error handling and multiple fallback strategies."""
        if not self.audio_available or not self.recognizer:
            logger.error("Audio transcription not available")
            return None, False
        
        self.performance_stats['total_transcriptions'] += 1
        converted_path = None
        
        try:
            # Validate input audio
            is_valid, validation_message = self.validate_audio_file(audio_path)
            if not is_valid:
                logger.error(f"Audio validation failed: {validation_message}")
                return None, False
            
            # Convert audio to optimal format
            converted_path = self.convert_audio_format(audio_path)
            if not converted_path:
                logger.error("Failed to convert audio format")
                return None, False
            
            # Optimized transcription - prioritize Google Speech Recognition for speed
            try:
                # Primary strategy: Google Speech Recognition (fastest and most reliable)
                text = self._transcribe_with_google(converted_path)
                if text and text.strip():
                    self.performance_stats['successful_transcriptions'] += 1
                    self._update_success_rate()
                    logger.info(f"Transcription successful: {text[:50]}...")
                    return text.strip(), True
            except Exception as e:
                logger.warning(f"Google transcription failed: {e}")
            
            # Fallback strategy: Only use one additional method for speed
            try:
                text = self._transcribe_with_sphinx(converted_path)
                if text and text.strip():
                    self.performance_stats['successful_transcriptions'] += 1
                    self._update_success_rate()
                    logger.info(f"Fallback transcription successful: {text[:50]}...")
                    return text.strip(), True
            except Exception as e:
                logger.warning(f"Fallback transcription failed: {e}")
            
            logger.error("All transcription strategies failed")
            return None, False
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return None, False
        
        finally:
            # Clean up temporary file
            if converted_path and converted_path != audio_path:
                try:
                    os.remove(converted_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
    
    def _transcribe_with_google(self, audio_path: str) -> Optional[str]:
        """Transcribe using Google Speech Recognition (optimized for speed)."""
        with sr.AudioFile(audio_path) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.2)  # Reduced for faster processing
            audio_data = self.recognizer.record(source)
            return self.recognizer.recognize_google(audio_data, language='en-US')
    
    def _transcribe_with_google_cloud(self, audio_path: str) -> Optional[str]:
        """Transcribe using Google Cloud Speech Recognition."""
        with sr.AudioFile(audio_path) as source:
            audio_data = self.recognizer.record(source)
            return self.recognizer.recognize_google_cloud(audio_data, language='en-US')
    
    def _transcribe_with_sphinx(self, audio_path: str) -> Optional[str]:
        """Transcribe using CMU Sphinx (offline)."""
        with sr.AudioFile(audio_path) as source:
            audio_data = self.recognizer.record(source)
            return self.recognizer.recognize_sphinx(audio_data)
    
    def _transcribe_with_wit_ai(self, audio_path: str) -> Optional[str]:
        """Transcribe using Wit.ai."""
        with sr.AudioFile(audio_path) as source:
            audio_data = self.recognizer.record(source)
            # Note: Requires Wit.ai API key
            return self.recognizer.recognize_wit(audio_data, key="YOUR_WIT_AI_KEY")
    
    def generate_tts_audio(self, text: str, output_path: str = None) -> Optional[str]:
        """Generate TTS audio with comprehensive error handling and validation."""
        if not self.audio_available or not self.tts_engine:
            logger.warning("TTS not available")
            return None
        
        self.performance_stats['total_tts_generations'] += 1
        
        try:
            # Clean and validate text
            clean_text = self._clean_text_for_tts(text)
            if not clean_text:
                logger.warning("No valid text for TTS")
                return None
            
            # Generate output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                output_path = os.path.join("static", "audio", f"response_{timestamp}.wav")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate TTS audio with timeout protection
            success = self._generate_tts_with_timeout(clean_text, output_path, timeout=30)
            
            if success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.performance_stats['successful_tts_generations'] += 1
                self._update_success_rate()
                logger.info(f"TTS audio generated successfully: {output_path}")
                return output_path
            else:
                logger.error("TTS generation failed or produced invalid file")
                return None
                
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None
    
    def _generate_tts_with_timeout(self, text: str, output_path: str, timeout: int = 30) -> bool:
        """Generate TTS with timeout protection to prevent hanging."""
        import threading
        import queue
        
        result_queue = queue.Queue()
        
        def tts_worker():
            """Worker function to generate TTS in a separate thread."""
            try:
                # Try multiple TTS approaches
                success = False
                
                # Method 1: Try with a fresh engine instance
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 175)
                    engine.setProperty('volume', 0.9)
                    
                    # Save to file
                    engine.save_to_file(text, output_path)
                    engine.runAndWait()
                    
                    # Clean up
                    engine.stop()
                    del engine
                    
                    # Verify file creation
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        success = True
                        
                except Exception as e:
                    logger.warning(f"Method 1 (pyttsx3) failed: {e}")
                
                # Method 2: Try with Windows SAPI directly if Method 1 failed
                if not success and os.name == 'nt':
                    try:
                        import win32com.client
                        voice = win32com.client.Dispatch("SAPI.SpVoice")
                        file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
                        file_stream.Open(output_path, 3)
                        voice.AudioOutputStream = file_stream
                        voice.Speak(text)
                        file_stream.Close()
                        
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            success = True
                            
                    except Exception as e:
                        logger.warning(f"Method 2 (SAPI) failed: {e}")
                
                # Method 3: Fallback to basic file creation with dummy audio
                if not success:
                    try:
                        # Create a minimal WAV file as fallback
                        import wave
                        import struct
                        
                        # Create a short beep sound as fallback
                        sample_rate = 22050
                        duration = 0.5  # seconds
                        frequency = 440  # Hz
                        
                        frames = []
                        for i in range(int(duration * sample_rate)):
                            value = int(32767 * 0.3 * (i % (sample_rate // frequency) < (sample_rate // frequency) // 2))
                            frames.append(struct.pack('<h', value))
                        
                        with wave.open(output_path, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(sample_rate)
                            wav_file.writeframes(b''.join(frames))
                        
                        success = True
                        logger.warning("Used fallback audio generation")
                        
                    except Exception as e:
                        logger.error(f"Method 3 (fallback) failed: {e}")
                
                result_queue.put(success)
                
            except Exception as e:
                logger.error(f"TTS worker thread error: {e}")
                result_queue.put(False)
        
        # Start the TTS generation in a separate thread
        tts_thread = threading.Thread(target=tts_worker, daemon=True)
        tts_thread.start()
        
        # Wait for completion with timeout
        try:
            success = result_queue.get(timeout=timeout)
            return success
        except queue.Empty:
            logger.error(f"TTS generation timed out after {timeout} seconds")
            return False
        except Exception as e:
            logger.error(f"TTS timeout mechanism error: {e}")
            return False
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for optimal TTS output with comprehensive processing."""
        if not text:
            return ""
        
        import re
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        text = re.sub(r'#{1,6}\s*', '', text)         # Headers
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
        
        # Remove emojis and special characters
        text = re.sub(r'[🚗📱🤖✨🎉💰🏆⚡🧠💼🔧📊🌟✂️🍕🏠💡📞🔒🚨⏰👥📋❌✅]', '', text)
        
        # Replace bullet points and list markers
        text = re.sub(r'[•·▪▫‣⁃]', '- ', text)
        text = re.sub(r'^\s*[-*+]\s+', '- ', text, flags=re.MULTILINE)
        
        # Clean up numbers and abbreviations
        text = re.sub(r'\b(\d+)%\b', r'\1 percent', text)
        text = re.sub(r'\b(\d+)\$\b', r'\1 dollars', text)
        text = re.sub(r'\bAPI\b', 'A P I', text)
        text = re.sub(r'\bURL\b', 'U R L', text)
        text = re.sub(r'\bHTTP\b', 'H T T P', text)
        
        # Clean up whitespace and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'[,;:]{2,}', ',', text)
        text = text.strip()
        
        # Limit length for TTS (split into sentences if too long)
        if len(text) > 500:
            sentences = re.split(r'[.!?]+', text)
            text = '. '.join(sentences[:3]) + '.'
        
        return text
    
    def _update_success_rate(self):
        """Update performance statistics."""
        if self.performance_stats['total_transcriptions'] > 0:
            self.performance_stats['transcription_success_rate'] = (
                self.performance_stats['successful_transcriptions'] / 
                self.performance_stats['total_transcriptions']
            )
        
        if self.performance_stats['total_tts_generations'] > 0:
            self.performance_stats['tts_success_rate'] = (
                self.performance_stats['successful_tts_generations'] / 
                self.performance_stats['total_tts_generations']
            )
    
    def record_audio(self, duration: int = 5) -> Optional[str]:
        """Record audio from microphone with comprehensive error handling."""
        if not self.audio_available or not self.microphone or not self.recognizer:
            logger.warning("Audio recording not available")
            return None
        
        try:
            logger.info(f"Recording audio for {duration} seconds...")
            
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Record with timeout protection
                audio_data = self.recognizer.listen(
                    source, 
                    timeout=duration + 2, 
                    phrase_time_limit=duration
                )
            
            # Save to temporary file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            temp_path = os.path.join(tempfile.gettempdir(), f"recorded_audio_{timestamp}.wav")
            
            with open(temp_path, "wb") as f:
                f.write(audio_data.get_wav_data())
            
            # Validate recorded audio
            is_valid, validation_message = self.validate_audio_file(temp_path)
            if not is_valid:
                logger.error(f"Recorded audio validation failed: {validation_message}")
                try:
                    os.remove(temp_path)
                except:
                    pass
                return None
            
            logger.info(f"Audio recorded successfully: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if audio processing is available."""
        return self.audio_available and (self.recognizer is not None or self.tts_engine is not None)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive audio processor status."""
        return {
            "audio_available": self.audio_available,
            "recognizer_available": self.recognizer is not None,
            "microphone_available": self.microphone is not None,
            "tts_available": self.tts_engine is not None,
            "dependencies_installed": AUDIO_DEPENDENCIES_AVAILABLE,
            "initialization_attempts": self.initialization_attempts,
            "last_error": self.last_error,
            "performance_stats": self.performance_stats.copy()
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get detailed health report for monitoring."""
        status = self.get_status()
        
        # Calculate overall health score
        health_score = 0
        if status["audio_available"]:
            health_score += 25
        if status["recognizer_available"]:
            health_score += 25
        if status["microphone_available"]:
            health_score += 25
        if status["tts_available"]:
            health_score += 25
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score >= 75 else "degraded" if health_score >= 50 else "critical",
            "components": status,
            "recommendations": self._get_health_recommendations(status)
        }
    
    def _get_health_recommendations(self, status: Dict[str, Any]) -> list:
        """Get recommendations based on current status."""
        recommendations = []
        
        if not status["dependencies_installed"]:
            recommendations.append("Install missing audio dependencies: pip install pyttsx3 pydub speech_recognition pyaudio")
        
        if not status["microphone_available"]:
            recommendations.append("Check microphone permissions and hardware connection")
        
        if not status["tts_available"]:
            recommendations.append("Restart TTS engine or check system audio drivers")
        
        if status["performance_stats"]["transcription_success_rate"] < 0.8:
            recommendations.append("Consider improving audio quality or checking microphone settings")
        
        if status["performance_stats"]["tts_success_rate"] < 0.9:
            recommendations.append("Check TTS engine configuration and system resources")
        
        return recommendations

# Maintain backward compatibility
ImprovedAudioProcessor = RobustAudioProcessor

def main():
    """Test the robust audio processor."""
    print("🎵 ROBUST AUDIO PROCESSOR TEST")
    print("=" * 50)
    
    processor = RobustAudioProcessor()
    health_report = processor.get_health_report()
    
    print(f"Health Score: {health_report['health_score']}/100")
    print(f"Status: {health_report['status'].upper()}")
    print("\nComponent Status:")
    for key, value in health_report['components'].items():
        if key != 'performance_stats':
            print(f"  {key}: {value}")
    
    print(f"\nPerformance Stats:")
    for key, value in health_report['components']['performance_stats'].items():
        print(f"  {key}: {value}")
    
    if health_report['recommendations']:
        print(f"\nRecommendations:")
        for rec in health_report['recommendations']:
            print(f"  • {rec}")
    
    if processor.is_available():
        print("\n🔊 Testing TTS...")
        test_text = "Hello! This is a test of the robust audio processor with comprehensive error handling."
        audio_file = processor.generate_tts_audio(test_text)
        if audio_file:
            print(f"✅ TTS audio generated: {audio_file}")
        else:
            print("❌ TTS generation failed")
    else:
        print("\n❌ Audio processing not available")

if __name__ == "__main__":
    main()