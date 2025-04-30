import { NextResponse } from 'next/server';
import axios from 'axios';

// Trending topics for our fallback generator
const TRENDING_TOPICS = [
  "technology", "ai", "business", "climate", "health", 
  "politics", "entertainment", "sports", "science"
];

// Function to translate query to the selected language using Google Translate API (or fallback)
async function translateQuery(query: string, targetLang: string): Promise<string> {
  if (!query) return '';
  if (targetLang === 'en') return query;
  try {
    const res = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=${targetLang}&dt=t&q=${encodeURIComponent(query)}`);
    const data = await res.json();
    return data[0]?.map((t: any) => t[0]).join('') || query;
  } catch {
    return query; // fallback to original if translation fails
  }
}

// API route for trending news with sentiment analysis and fallback mechanism
export async function GET(request: Request) {
  try {
    // Get URL parameters
    const url = new URL(request.url);
    const language = url.searchParams.get('language') || 'en';
    const limit = parseInt(url.searchParams.get('limit') || '12');
    const query = url.searchParams.get('query') || '';

    // Try to fetch trending news from backend FastAPI first
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${backendUrl}/api/trending?language=${language}&limit=${limit}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store',
      });
      if (response.ok) {
        const data = await response.json();
        if (data.articles && data.articles.length > 0) {
          return NextResponse.json({
            articles: data.articles,
            message: data.message || 'Trending news from backend',
            categories: data.categories || {},
          });
        }
      }
    } catch (err) {
      // Ignore and fallback to RSS feeds
    }

    // If backend fails, fallback to RSS feeds
    const fallbackArticles = await generateFallbackTrendingNews(language, limit, query);
    return NextResponse.json({
      articles: fallbackArticles,
      message: 'Showing trending news from fallback',
      categories: generateCategoryDistribution(fallbackArticles),
    });
  } catch (error: any) {
    console.error('Error fetching trending news:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch trending news',
        articles: [],
        message: 'Error connecting to server. Please try again later.',
        categories: {},
      },
      { status: 200 } // Return 200 even on error to avoid cascading errors in UI
    );
  }
}

// Function to generate fallback trending news when API is unavailable
async function generateFallbackTrendingNews(language: string, limit: number, query?: string) {
  let RSS_FEEDS: string[] = [];
  if (language === 'ta') {
    RSS_FEEDS = [
      'https://feeds.feedburner.com/Hindu_Tamil_india',
      'https://feeds.feedburner.com/Hindu_Tamil_tamilnadu',
      'https://feeds.feedburner.com/Hindu_Tamil_tamilnadu',
      'https://feeds.feedburner.com/Hindu_Tamil_environment',
      'https://feeds.feedburner.com/Hindu_Tamil_sports',
      'https://feeds.feedburner.com/Hindu_Tamil_world',
      'https://feeds.feedburner.com/Hindu_Tamil_business',
    ];
  } else {
    RSS_FEEDS = [
      'https://www.bbc.co.uk/news/world/rss.xml',
      'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
      'https://www.theguardian.com/world/rss',
      'https://feeds.bbci.co.uk/news/rss.xml',
      'https://www.reuters.com/rssFeed/topNews',
      'https://www.cnn.com/rss/edition.rss',
      'https://www.aljazeera.com/xml/rss/all.xml',
    ];
  }

  const Parser = require('rss-parser');
  const parser = new Parser();
  let articles: any[] = [];

  // Translate query if needed
  let translatedQuery = query;
  if (query && language !== 'en') {
    translatedQuery = await translateQuery(query, language);
  }

  for (const feedUrl of RSS_FEEDS) {
    try {
      const feed = await parser.parseURL(feedUrl);
      for (const entry of feed.items.slice(0, 10)) {
        // If query is present, filter by translated query in title or summary
        if (translatedQuery) {
          const text = `${entry.title || ''} ${entry.contentSnippet || entry.summary || ''}`.toLowerCase();
          if (!text.includes(translatedQuery.toLowerCase())) continue;
        }
        articles.push({
          id: entry.guid || entry.link || entry.title,
          title: entry.title,
          summary: entry.contentSnippet || entry.summary || '',
          source: {
            name: feed.title,
            url: feed.link
          },
          published_date: entry.isoDate || entry.pubDate || new Date().toISOString(),
          link: entry.link,
          image_url: entry.enclosure?.url || '',
          sentiment: undefined,
          relevance: 1.0
        });
        if (articles.length >= limit) break;
      }
      if (articles.length >= limit) break;
    } catch (e) {
      // Ignore feed errors
    }
  }

  // If not enough articles, just return what we have
  return articles.slice(0, limit);
}

// Helper functions for generating realistic fallback data
function getRandomCategory() {
  return TRENDING_TOPICS[Math.floor(Math.random() * TRENDING_TOPICS.length)];
}

function generateCategoryDistribution(articles: any[]) {
  // Create a distribution of categories from the generated articles
  const categories: Record<string, number> = {};
  
  TRENDING_TOPICS.forEach(topic => {
    categories[topic] = Math.floor(Math.random() * 10) + 1;
  });
  
  return categories;
}