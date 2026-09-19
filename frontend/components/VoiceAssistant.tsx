'use client';

import React, { useState, useEffect, useRef } from 'react';
import GoogleCalendar from './GoogleCalendar';
import {
  Waves, Server, Cpu, Mic, MicOff, Database, Check, Zap, Globe,
  Building2, MessageSquare, CalendarDays, RotateCw, AlertTriangle,
} from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  type?: 'text' | 'voice';
  audioUrl?: string;
}

interface SystemStatus {
  apiConnected: boolean;
  model: string;
  audioEnabled: boolean;
  sttStatus: 'idle' | 'listening' | 'processing' | 'error';
  ttsStatus: 'idle' | 'generating' | 'playing' | 'error';
  databaseConnected: boolean;
  lastError?: string;
  responseTime?: number;
}

interface AICapabilities {
  name: string;
  model: string;
  provider: string;
  capabilities: string[];
  trainedFor: string[];
  responseTime: string;
  languages: string[];
}

type AppMode = 'status' | 'chat' | 'voice' | 'calendar';

interface VoiceAssistantProps {
  backendUrl: string;
  autoStart?: boolean;
}

export default function VoiceAssistant({ backendUrl, autoStart = false }: VoiceAssistantProps) {
  const [currentMode, setCurrentMode] = useState<AppMode>('status');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [memoryStatus, setMemoryStatus] = useState<any>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    apiConnected: false,
    model: 'Unknown',
    audioEnabled: false,
    sttStatus: 'idle',
    ttsStatus: 'idle',
    databaseConnected: false
  });

  const [aiCapabilities] = useState<AICapabilities>({
    name: 'Vertiqx AI Assistant',
    model: 'phi3:mini',
    provider: 'Ollama',
    capabilities: [
      'Natural Language Understanding',
      'Voice Recognition (STT)',
      'Text-to-Speech (TTS)',
      'Booking Management',
      'Customer Support',
      'Service Information'
    ],
    trainedFor: [
      'Car Detailing Services',
      'WhatsApp Automation',
      'AI Customer Support',
      'Appointment Booking',
      'Service Inquiries',
      'General Business Support'
    ],
    responseTime: '< 3 seconds',
    languages: ['English']
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Check system health
  const checkSystemHealth = async () => {
    const startTime = Date.now();
    try {
      const response = await fetch(`${backendUrl}/api/health`);
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(prev => ({
          ...prev,
          apiConnected: true,
          model: data.components?.model_name || 'phi3:mini',
          audioEnabled: data.components?.audio_processor || false,
          databaseConnected: data.components?.database || false,
          responseTime,
          lastError: undefined
        }));
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      setSystemStatus(prev => ({
        ...prev,
        apiConnected: false,
        databaseConnected: false,
        lastError: error instanceof Error ? error.message : 'Connection failed'
      }));
    }
  };

  // Reset agent memory
  const resetMemory = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/voice-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          session_id: 'web-session',
          action: 'reset'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMemoryStatus(null);
        setMessages([]);
        console.log('🧠 Memory reset successfully');
      }
    } catch (error) {
      console.error('❌ Error resetting memory:', error);
    }
  };

  // Send text message
  const sendTextMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsProcessing(true);

    try {
      const startTime = Date.now();
      const response = await fetch(`${backendUrl}/api/voice-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: inputText,
          session_id: 'web-session',
          action: 'chat'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const responseTime = Date.now() - startTime;
        
        // Update system status with response time
        setSystemStatus(prev => ({ 
          ...prev, 
          responseTime: data.response_time_ms || responseTime 
        }));

        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          sender: 'ai',
          timestamp: new Date(),
          type: 'text',
          audioUrl: data.audio_url ? `${backendUrl}${data.audio_url}` : undefined
        };
        setMessages(prev => [...prev, aiMessage]);

        // Update memory status
        if (data.memory_status) {
          setMemoryStatus(data.memory_status);
          console.log('🧠 Memory Status:', data.memory_status);
        }

        // Auto-play TTS if available and in voice mode
        if (data.audio_url && currentMode === 'voice') {
          playTTSAudio(data.audio_url);
        }
      } else {
        throw new Error(`Server error (${response.status})`);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'ai',
        timestamp: new Date(),
        type: 'text'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };



  // Start voice recording
  const startRecording = async () => {
    if (isRecording) {
      console.log('⚠️ Already recording');
      return;
    }

    try {
      console.log('🎤 Starting recording...');
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        }
      });

      // Determine the best supported MIME type
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4';
      }
      
      console.log(`🎵 Using MIME type: ${mimeType}`);
      
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      audioChunksRef.current = [];
      streamRef.current = stream;

      mediaRecorderRef.current.ondataavailable = (event) => {
        console.log('📦 Audio chunk received:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        console.log('🛑 Recording stopped, creating audio blob...');
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: mimeType 
        });
        console.log('🎵 Audio blob created:', audioBlob.type, audioBlob.size, 'bytes');
        processAudio(audioBlob);
        
        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      mediaRecorderRef.current.onerror = (event) => {
        console.error('❌ MediaRecorder error:', event);
        setIsRecording(false);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      console.log('✅ Recording started successfully');
    } catch (error) {
      console.error('❌ Error starting recording:', error);
      setIsRecording(false);
    }
  };

  // Stop voice recording
  const stopRecording = () => {
    if (!isRecording || !mediaRecorderRef.current) {
      console.log('⚠️ Cannot stop recording - no active recording');
      return;
    }

    try {
      console.log('🛑 Stopping recording...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setSystemStatus(prev => ({ ...prev, sttStatus: 'processing' }));
      console.log('✅ Recording stopped successfully');
    } catch (error) {
      console.error('❌ Error stopping recording:', error);
      setIsRecording(false);
    }
  };



  // Process audio with optimizations for speed
  const processAudio = async (audioBlob: Blob) => {
    console.log(`🔄 Starting audio processing - Size: ${audioBlob.size} bytes, Type: ${audioBlob.type}`);
    setIsProcessing(true);
    setSystemStatus(prev => ({ ...prev, sttStatus: 'processing' }));

    try {
      const formData = new FormData();
      // Determine file extension based on blob type
      let extension = 'webm';
      if (audioBlob.type.includes('mp4')) extension = 'mp4';
      else if (audioBlob.type.includes('wav')) extension = 'wav';
      
      formData.append('audio', audioBlob, `recording.${extension}`);

      const startTime = Date.now();
      console.log('📤 Sending audio to backend...');
      
      const response = await fetch(`${backendUrl}/api/process-audio`, {
        method: 'POST',
        body: formData,
        // Add timeout for audio processing - increased to match backend timeout
        signal: AbortSignal.timeout(30000), // 30 second timeout to match backend
      });

      console.log(`📥 Backend response received - Status: ${response.status}, Time: ${Date.now() - startTime}ms`);

      if (response.ok) {
        const data = await response.json();
        const processingTime = Date.now() - startTime;
        
        console.log('📝 Response data:', {
          hasTranscription: !!data.transcription,
          transcription: data.transcription,
          hasResponse: !!data.response,
          hasAudio: !!data.audio_url,
          processingTime
        });
        
        if (data.transcription) {
          console.log(`🗣️ Transcription: "${data.transcription}"`);
          const userMessage: Message = {
            id: Date.now().toString(),
            text: data.transcription,
            sender: 'user',
            timestamp: new Date(),
            type: 'voice'
          };
          setMessages(prev => [...prev, userMessage]);

          if (data.response) {
            console.log(`🤖 AI Response: "${data.response}"`);
            const aiMessage: Message = {
              id: (Date.now() + 1).toString(),
              text: data.response,
              sender: 'ai',
              timestamp: new Date(),
              type: 'text',
              audioUrl: data.audio_url ? `${backendUrl}${data.audio_url}` : undefined
            };
            setMessages(prev => [...prev, aiMessage]);

            // Play TTS audio in parallel (don't wait)
            if (data.audio_url) {
              const fullAudioUrl = `${backendUrl}${data.audio_url}`;
              console.log(`🔊 Playing TTS audio: ${fullAudioUrl}`);
              playTTSAudio(fullAudioUrl).catch(err => {
                console.error('❌ TTS playback failed:', err);
              });
            }
          }
        } else {
          console.warn('⚠️ No transcription received from backend');
        }
        setSystemStatus(prev => ({ ...prev, sttStatus: 'idle' }));
        
        // Log performance for monitoring
        console.log(`✅ Audio processing completed in ${processingTime}ms`);
      } else {
        const errorText = await response.text();
        console.error(`❌ Backend error ${response.status}:`, errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Audio processing error:', error);
      
      let errorMessage = 'Audio processing failed';
      if (error instanceof Error) {
        if (error.name === 'AbortError' || error.message.includes('timeout')) {
          errorMessage = 'Audio processing timed out. Please try again with a shorter message.';
        } else if (error.message.includes('HTTP 400')) {
          errorMessage = 'Invalid audio format. Please check your microphone settings.';
        } else if (error.message.includes('HTTP 500')) {
          errorMessage = 'Server error during audio processing. Please try again.';
        } else if (error.message.includes('Failed to fetch')) {
          errorMessage = 'Connection error. Please check your internet connection.';
        } else {
          errorMessage = error.message;
        }
      }
      
      setSystemStatus(prev => ({ 
        ...prev, 
        sttStatus: 'error', 
        lastError: errorMessage
      }));
    } finally {
      setIsProcessing(false);
      console.log('🏁 Audio processing finished');
    }
  };



  // Play TTS audio
  const playTTSAudio = async (audioUrl: string) => {
    try {
      setSystemStatus(prev => ({ ...prev, ttsStatus: 'playing' }));
      
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }

      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;
      
      audio.onended = () => {
        setSystemStatus(prev => ({ ...prev, ttsStatus: 'idle' }));
      };
      
      audio.onerror = (e) => {
        console.error('❌ TTS audio playback error:', e);
        setSystemStatus(prev => ({ 
          ...prev, 
          ttsStatus: 'error', 
          lastError: 'Audio playback failed. Please check your speakers or try again.' 
        }));
      };

      await audio.play();
    } catch (error) {
      console.error('❌ TTS playback error:', error);
      let errorMessage = 'Audio playback failed';
      if (error instanceof Error) {
        if (error.message.includes('NotAllowedError')) {
          errorMessage = 'Audio playback blocked. Please allow audio in your browser settings.';
        } else if (error.message.includes('NotSupportedError')) {
          errorMessage = 'Audio format not supported by your browser.';
        } else {
          errorMessage = 'Audio playback failed. Please try again.';
        }
      }
      
      setSystemStatus(prev => ({ 
        ...prev, 
        ttsStatus: 'error', 
        lastError: errorMessage
      }));
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Initial health check
  useEffect(() => {
    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Render system status page
  // Render system status page
  const renderStatusPage = () => {
    const statusCards = [
      {
        label: 'API Server',
        icon: Server,
        ok: systemStatus.apiConnected,
        value: systemStatus.apiConnected ? 'Connected' : 'Disconnected',
        meta: systemStatus.responseTime ? systemStatus.responseTime + 'ms round trip' : 'localhost:8000',
      },
      {
        label: 'AI Model',
        icon: Cpu,
        ok: true,
        value: systemStatus.model,
        meta: 'Ollama - runs locally',
      },
      {
        label: 'Audio System',
        icon: systemStatus.audioEnabled ? Mic : MicOff,
        ok: systemStatus.audioEnabled,
        value: systemStatus.audioEnabled ? 'Enabled' : 'Disabled',
        meta: systemStatus.audioEnabled ? 'Mic and speaker ready' : 'Speech-to-text ' + systemStatus.sttStatus,
      },
      {
        label: 'Database',
        icon: Database,
        ok: systemStatus.databaseConnected,
        value: systemStatus.databaseConnected ? 'Connected' : 'Disconnected',
        meta: 'SQLite - bookings.db',
      },
    ];

    const modes = [
      {
        id: 'chat' as const,
        icon: MessageSquare,
        title: 'Chat',
        copy: 'Type a message and get a reply from the local model.',
        meta: 'Text - instant',
        disabled: false,
      },
      {
        id: 'voice' as const,
        icon: Mic,
        title: 'Voice',
        copy: 'Speak naturally and hear the answer read back to you.',
        meta: 'Speech in - speech out',
        disabled: !systemStatus.audioEnabled,
      },
      {
        id: 'calendar' as const,
        icon: CalendarDays,
        title: 'Calendar',
        copy: 'Review bookings and the Google Calendar sync.',
        meta: 'Bookings - Google sync',
        disabled: false,
      },
    ];

    const footprint = [
      { icon: Zap, label: 'Response time', value: aiCapabilities.responseTime },
      { icon: Globe, label: 'Languages', value: aiCapabilities.languages.join(', ') },
      { icon: Building2, label: 'Provider', value: aiCapabilities.provider },
    ];

    return (
      <div className="relative min-h-screen overflow-hidden bg-[#07080d] px-6 py-12 text-white">
        {/* Ambient light, rather than the old three-stop purple wash */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(60% 45% at 50% 0%, rgba(99,102,241,0.18), transparent 70%), radial-gradient(40% 35% at 85% 85%, rgba(14,165,233,0.10), transparent 70%)',
          }}
        />

        <div className="relative mx-auto max-w-6xl">
          {/* Header */}
          <header className="mb-14 text-center">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.04]">
              <Waves size={24} strokeWidth={1.75} className="text-indigo-300" />
            </div>
            <h1 className="text-[2.75rem] font-semibold leading-none tracking-tight">Vertiqx AI Assistant</h1>
            <p className="mt-3 text-sm text-white/45">Voice and chat booking agent, running on a local model</p>
          </header>

          {/* System status */}
          <section className="mb-5 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
            {statusCards.map(card => (
              <div
                key={card.label}
                className="group rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 transition-colors hover:border-white/[0.12]"
              >
                <div className="flex items-start justify-between">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">{card.label}</p>
                  <card.icon size={15} strokeWidth={1.75} className="text-white/25 transition-colors group-hover:text-white/40" />
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${card.ok ? 'bg-emerald-400' : 'bg-white/25'}`} />
                  <p className="text-lg font-medium tracking-tight">{card.value}</p>
                </div>
                <p className="mt-2 text-xs text-white/35">{card.meta}</p>
              </div>
            ))}
          </section>

          {systemStatus.lastError && (
            <div className="mb-5 flex items-start gap-3 rounded-2xl border border-rose-500/20 bg-rose-500/[0.06] p-4">
              <AlertTriangle size={16} strokeWidth={1.75} className="mt-0.5 shrink-0 text-rose-300" />
              <div>
                <p className="text-sm font-medium text-rose-200">System error</p>
                <p className="mt-1 text-xs text-rose-200/70">{systemStatus.lastError}</p>
              </div>
            </div>
          )}

          {/* Capabilities */}
          <section className="mb-5 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-8">
            <div className="grid grid-cols-1 gap-10 lg:grid-cols-2">
              <div>
                <p className="mb-5 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">Core capabilities</p>
                <ul className="space-y-3">
                  {aiCapabilities.capabilities.map((capability, index) => (
                    <li key={index} className="flex items-center gap-3 text-sm text-white/75">
                      <Check size={14} strokeWidth={2.25} className="shrink-0 text-emerald-400/80" />
                      {capability}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <p className="mb-5 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">Trained for</p>
                <ul className="space-y-3">
                  {aiCapabilities.trainedFor.map((training, index) => (
                    <li key={index} className="flex items-center gap-3 text-sm text-white/75">
                      <span className="h-1 w-1 shrink-0 rounded-full bg-indigo-400/70" />
                      {training}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mt-10 grid grid-cols-1 gap-6 border-t border-white/[0.06] pt-7 md:grid-cols-3">
              {footprint.map(item => (
                <div key={item.label} className="flex items-center gap-3">
                  <item.icon size={15} strokeWidth={1.75} className="shrink-0 text-white/25" />
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">{item.label}</p>
                    <p className="mt-1 text-sm text-white/80">{item.value}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Mode selection */}
          <section className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-8">
            <p className="mb-6 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/35">Choose a mode</p>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              {modes.map(mode => (
                <button
                  key={mode.id}
                  onClick={() => setCurrentMode(mode.id)}
                  disabled={mode.disabled}
                  className="group rounded-xl border border-white/[0.07] bg-white/[0.02] p-6 text-left transition-colors hover:border-indigo-400/30 hover:bg-white/[0.04] disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:border-white/[0.07] disabled:hover:bg-white/[0.02]"
                >
                  <mode.icon size={18} strokeWidth={1.75} className="text-white/40 transition-colors group-hover:text-indigo-300" />
                  <h3 className="mt-4 text-base font-medium tracking-tight">{mode.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-white/45">{mode.copy}</p>
                  <p className="mt-4 text-[11px] uppercase tracking-[0.1em] text-white/25">
                    {mode.disabled ? 'Audio unavailable' : mode.meta}
                  </p>
                </button>
              ))}
            </div>

            <button
              onClick={checkSystemHealth}
              className="mt-6 inline-flex items-center gap-2 rounded-lg border border-white/[0.08] px-4 py-2 text-xs font-medium text-white/55 transition-colors hover:border-white/15 hover:text-white/80"
            >
              <RotateCw size={13} strokeWidth={2} />
              Refresh status
            </button>
          </section>
        </div>
      </div>
    );
  };


  // Render chat interface
  const renderChatInterface = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="glass-panel p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentMode('status')}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-all duration-200"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">💬 Chat Mode</h1>
                <p className="text-blue-200">Type your messages below</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${systemStatus.apiConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-white text-sm">{systemStatus.model}</span>
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="glass-panel h-[600px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-300 mt-20">
                <div className="text-6xl mb-4">💬</div>
                <h3 className="text-xl font-semibold mb-2">Start a conversation!</h3>
                <p>Type a message below to begin chatting with the AI assistant.</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'bg-blue-600 text-white'
                  }`}>
                    <p>{message.text}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                      {message.audioUrl && (
                        <button
                          onClick={() => playTTSAudio(message.audioUrl!)}
                          className="text-xs bg-white/20 px-2 py-1 rounded hover:bg-white/30 transition-all"
                        >
                          🔊 Play
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-blue-600 text-white px-4 py-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span>AI is thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Memory Status */}
          {memoryStatus && (
            <div className="border-t border-white/20 p-4 bg-white/5">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-300">
                  <span className="font-semibold">🧠 Memory:</span>
                  {memoryStatus.name && <span className="ml-2">👤 {memoryStatus.name}</span>}
                  {memoryStatus.phone && <span className="ml-2">📞 {memoryStatus.phone}</span>}
                  {memoryStatus.service && <span className="ml-2">⚙️ {memoryStatus.service}</span>}
                  {memoryStatus.date && <span className="ml-2">📅 {memoryStatus.date}</span>}
                  {memoryStatus.time && <span className="ml-2">⏰ {memoryStatus.time}</span>}
                </div>
                <button
                  onClick={resetMemory}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-all duration-200"
                >
                  Reset Memory
                </button>
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t border-white/20 p-4">
            <div className="flex space-x-3">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
                placeholder="Type your message here..."
                className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                disabled={isProcessing}
              />
              <button
                onClick={sendTextMessage}
                disabled={!inputText.trim() || isProcessing}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg transition-all duration-200"
              >
                Send
              </button>
              {systemStatus.responseTime && (
                <div className="flex items-center px-3 py-3 bg-green-600/20 text-green-300 rounded-lg text-sm">
                  ⚡ {systemStatus.responseTime}ms
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render voice interface
  const renderVoiceInterface = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="glass-panel p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentMode('status')}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-all duration-200"
              >
                ← Back
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">🎤 Voice Mode</h1>
                <p className="text-blue-200">Speak naturally with the AI</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  systemStatus.sttStatus === 'listening' ? 'bg-red-400 animate-pulse' :
                  systemStatus.sttStatus === 'processing' ? 'bg-yellow-400' :
                  systemStatus.sttStatus === 'idle' ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <span className="text-white text-sm">STT: {systemStatus.sttStatus}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  systemStatus.ttsStatus === 'playing' ? 'bg-blue-400 animate-pulse' :
                  systemStatus.ttsStatus === 'generating' ? 'bg-yellow-400' :
                  systemStatus.ttsStatus === 'idle' ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
                <span className="text-white text-sm">TTS: {systemStatus.ttsStatus}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Voice Control */}
        <div className="glass-panel p-8 mb-6 text-center">
          <div className="flex flex-col items-center space-y-6">
            {/* Main Recording Button */}
            <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer ${
              isRecording 
                ? 'bg-red-500 animate-pulse shadow-lg shadow-red-500/50' 
                : isProcessing
                ? 'bg-yellow-500 animate-spin'
                : 'bg-blue-600 hover:bg-blue-700 shadow-lg'
            }`}
            onClick={isRecording ? stopRecording : startRecording}
            >
              <div className="text-white text-4xl">
                {isProcessing ? '⏳' : isRecording ? '⏹️' : '🎤'}
              </div>
            </div>
            
            {/* Control Buttons */}
            <div className="flex space-x-4">
              <button
                onClick={startRecording}
                disabled={isRecording || isProcessing}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                START
              </button>
              <button
                onClick={stopRecording}
                disabled={!isRecording || isProcessing}
                className="bg-red-600 hover:bg-red-700 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                STOP
              </button>
            </div>
            
            {/* Status Text */}
            <p className="text-gray-300 text-lg text-center">
              {isProcessing 
                ? 'Processing your request...' 
                : isRecording 
                ? 'Recording... Speak now!' 
                : 'Click START to begin recording'
              }
            </p>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="glass-panel h-[400px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-300 mt-16">
                <div className="text-6xl mb-4">🎙️</div>
                <h3 className="text-xl font-semibold mb-2">Voice conversation ready!</h3>
                <p>Click the microphone button above to start speaking.</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                    message.sender === 'user'
                      ? message.type === 'voice' 
                        ? 'bg-green-600 text-white border-l-4 border-green-400'
                        : 'bg-purple-600 text-white'
                      : 'bg-blue-600 text-white'
                  }`}>
                    <div className="flex items-center space-x-2 mb-1">
                      {message.type === 'voice' && <span className="text-xs">🎤</span>}
                      <span className="font-medium">
                        {message.sender === 'user' ? 'You' : 'AI'}
                      </span>
                    </div>
                    <p>{message.text}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                      {message.audioUrl && (
                        <button
                          onClick={() => playTTSAudio(message.audioUrl!)}
                          className="text-xs bg-white/20 px-2 py-1 rounded hover:bg-white/30 transition-all"
                        >
                          🔊 Replay
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>
    </div>
  );

  // Main render
  if (currentMode === 'status') {
    return renderStatusPage();
  } else if (currentMode === 'chat') {
    return renderChatInterface();
  } else if (currentMode === 'calendar') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900 text-white">
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold">📅 Calendar & Bookings</h1>
            <button
              onClick={() => setCurrentMode('status')}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-all duration-200"
            >
              ← Back to Status
            </button>
          </div>
          <GoogleCalendar 
            backendUrl={backendUrl} 
            onBack={() => setCurrentMode('status')} 
          />
        </div>
      </div>
    );
  } else {
    return renderVoiceInterface();
  }
}