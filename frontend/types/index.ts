export interface Message {
  id: string;
  type: 'user' | 'ai';
  text: string;
  timestamp: Date;
  audioUrl?: string;
}

export interface AudioProcessingResponse {
  transcription: string;
  response: string;
  audio_url?: string;
  confidence?: number;
  processing_time?: number;
}

export interface BackendHealthResponse {
  status: string;
  backend: string;
  message?: string;
  timestamp: string;
}

export interface VoiceAssistantConfig {
  backendUrl: string;
  autoStart: boolean;
  recordingDuration: number;
  silenceThreshold: number;
  silenceDuration: number;
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';
export type RecordingState = 'idle' | 'recording' | 'processing' | 'playing';