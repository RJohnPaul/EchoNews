import { NextResponse } from 'next/server';

// Increased timeout for better reliability
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://newsai-swc7.onrender.com";
const TIMEOUT_DURATION = 90000; // Extended to 90 seconds for better reliability

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_DURATION);
    
    console.log(`Fetching from: ${BASE_URL}/api/news with parameters:`, JSON.stringify(body));
    
    // Add page_size parameter if not provided, ensuring more results
    if (!body.page_size || body.page_size < 20) {
      body.page_size = 20; // Increase default page size
    }
    
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

// API route for trending news
export async function GET(request: Request) {
  try {
    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_DURATION);
    
    // Get URL parameters
    const url = new URL(request.url);
    const language = url.searchParams.get('language') || 'en';
    const limit = url.searchParams.get('limit') || '10';
    
    console.log(`Fetching trending news from: ${BASE_URL}/api/trending`);
    
    // Use Render backend URL with extended timeout
    const response = await fetch(`${BASE_URL}/api/trending?language=${language}&limit=${limit}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      signal: controller.signal,
    }).finally(() => {
      clearTimeout(timeoutId);
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error fetching trending news:', error);
    
    // Handle AbortError specifically for timeouts
    if (error.name === 'AbortError') {
      return NextResponse.json(
        { 
          error: 'Request timed out. The backend server might be starting up after inactivity. Please try again.',
          articles: [],
          message: "Server is warming up. Please try again in a moment.",
          categories: {}
        },
        { status: 504 }
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Failed to fetch trending news',
        articles: [],
        message: "Error connecting to server. Please try again later.",
        categories: {}
      },
      { status: 500 }
    );
  }
}