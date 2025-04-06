import { NextResponse } from 'next/server';

const BASE_URL = "http://127.0.0.1:8000";
const TIMEOUT_DURATION = 60000; // 60 seconds timeout

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_DURATION);
    
    console.log(`Fetching from: ${BASE_URL}/api/news`);
    
    // Use Render backend URL with extended timeout
    const response = await fetch(`${BASE_URL}/api/news`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
      // Increase timeout using AbortController
    }).finally(() => {
      clearTimeout(timeoutId);
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error proxying to FastAPI:', error);
    
    // Handle AbortError specifically for timeouts
    if (error.name === 'AbortError') {
      return NextResponse.json(
        { 
          error: 'Request timed out. The backend server might be starting up after inactivity. Please try again.',
          articles: [],
          message: "Server is warming up. Please try again in a moment.",
          total_found: 0,
          total_pages: 0,
          current_page: 1,
          available_sources: []
        },
        { status: 504 }
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Failed to fetch news',
        articles: [],
        message: "Error connecting to server. Please try again later.",
        total_found: 0,
        total_pages: 0,
        current_page: 1,
        available_sources: []
      },
      { status: 500 }
    );
  }
}