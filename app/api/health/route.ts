import { NextResponse } from 'next/server';

// Basic health check endpoint
export async function GET() {
  return NextResponse.json({ 
    status: 'ok', 
    message: 'Health check endpoint is active',
    timestamp: new Date().toISOString()
  });
}