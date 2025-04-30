import { NextResponse } from 'next/server';

// Increased timeout for reliability
const BASE_URL = "https://newsai-swc7.onrender.com";
const TIMEOUT_DURATION = 60000; // 60 seconds timeout

export async function GET(request: Request, { params }: { params: { language: string } }) {
  try {
    // Get language from route parameters
    const language = params.language;
    
    console.log(`Fetching news sources for language: ${language}`);
    
    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_DURATION);
    
    // Fetch from backend API
    const response = await fetch(`${BASE_URL}/api/news/sources/${language}`, {
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
    console.error(`Error fetching news sources for language: ${params.language}`, error);
    
    // Handle AbortError specifically for timeouts
    if (error.name === 'AbortError') {
      return NextResponse.json(
        { 
          error: 'Request timed out. The backend server might be starting up after inactivity. Please try again.',
          sources: []
        },
        { status: 504 }
      );
    }
    
    // Provide fallback sources for common languages
    const fallbackSources = getFallbackSources(params.language);
    
    if (fallbackSources.length > 0) {
      return NextResponse.json(
        { 
          message: "Using fallback sources due to API error",
          sources: fallbackSources
        },
        { status: 200 }
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Failed to fetch news sources',
        sources: []
      },
      { status: 500 }
    );
  }
}

// Fallback sources when the backend is unavailable
function getFallbackSources(language: string) {
  const fallbackSourcesMap: Record<string, Array<{ name: string, url: string, id: string, category: string, image: string }>> = {
    "en": [
      { name: "BBC News", url: "https://www.bbc.co.uk/news/world/rss.xml", id: "bbci.co.uk", category: "News", image: "https://ichef.bbci.co.uk/news/1024/branded_news/83B3/production/_115651733_breaking-large-promo-nc.png" },
      { name: "The Guardian", url: "https://www.theguardian.com/world/rss", id: "theguardian.com", category: "News", image: "https://i.guim.co.uk/img/media/b73cc57cb1d40376957ef6ad5d3c284d5b00f0d2/0_0_2000_1200/master/2000.jpg?width=620&quality=85&auto=format&fit=max&s=b2cf56f189b3903ba09d875fbc46eea7" },
      { name: "CNN", url: "http://rss.cnn.com/rss/edition.rss", id: "cnn.com", category: "News", image: "https://cdn.cnn.com/cnn/.e/img/3.0/global/misc/cnn-logo.png" },
      { name: "Reuters", url: "https://www.reutersagency.com/feed/", id: "reuters.com", category: "News", image: "https://www.reuters.com/pf/resources/images/reuters/logo-vertical-default.png?d=135" },
      { name: "Al Jazeera", url: "https://www.aljazeera.com/xml/rss/all.xml", id: "aljazeera.com", category: "News", image: "https://www.aljazeera.com/wp-content/uploads/2023/01/logo-aj.png" }
    ],
    "hi": [
      { name: "Dainik Bhaskar", url: "https://www.bhaskar.com/rss-feed/1061/", id: "bhaskar.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" },
      { name: "Amar Ujala", url: "https://www.amarujala.com/rss/breaking-news.xml", id: "amarujala.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" },
      { name: "Navbharat Times", url: "https://navbharattimes.indiatimes.com/rssfeedsdefault.cms", id: "navbharattimes.indiatimes.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" }
    ],
    "ta": [
      { name: "Dinamani", url: "https://www.dinamani.com/rss/latest-news.xml", id: "dinamani.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" },
      { name: "OneIndia Tamil", url: "https://tamil.oneindia.com/rss/tamil-news.xml", id: "tamil.oneindia.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" }
    ],
    "te": [
      { name: "Eenadu", url: "https://telugu.samayam.com/rssfeedstopstories.cms", id: "telugu.samayam.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" },
      { name: "OneIndia Telugu", url: "https://telugu.oneindia.com/rss/telugu-news.xml", id: "telugu.oneindia.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" }
    ],
    "mr": [
      { name: "Maharashtra Times", url: "https://maharashtratimes.com/rssfeedsdefault.cms", id: "maharashtratimes.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" },
      { name: "Loksatta", url: "https://www.loksatta.com/desh-videsh/feed/", id: "loksatta.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" }
    ],
    "gu": [
      { name: "Gujarat Samachar", url: "https://www.gujaratsamachar.com/rss/top-stories", id: "gujaratsamachar.com", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" },
      { name: "Divya Bhaskar", url: "https://www.divyabhaskar.co.in/rss-feed/1037/", id: "divyabhaskar.co.in", category: "News", image: "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg" }
    ]
  };
  
  return fallbackSourcesMap[language] || [];
}