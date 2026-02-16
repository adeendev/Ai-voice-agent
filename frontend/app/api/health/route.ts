import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Check if backend is running
    const backendResponse = await fetch('http://localhost:8000/health', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (backendResponse.ok) {
      return NextResponse.json({ 
        status: 'ok', 
        backend: 'connected',
        timestamp: new Date().toISOString()
      });
    } else {
      return NextResponse.json({ 
        status: 'error', 
        backend: 'disconnected',
        message: 'Backend server not responding'
      }, { status: 503 });
    }
  } catch (error) {
    return NextResponse.json({ 
      status: 'error', 
      backend: 'disconnected',
      message: 'Cannot connect to backend server'
    }, { status: 503 });
  }
}