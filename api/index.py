from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import feedparser
import re
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import time
from datetime import datetime
import json
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# Note: Gemini 1.5 Flash integration would require additional imports
# We'll simulate advanced semantic search capabilities in our implementation
# import google.generativeai as genai  # Would be required for actual Gemini integration

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class NewsRequest(BaseModel):
    query: str
    language: str
    max_articles: int = 5
    preferred_sources: List[str] = []  # Added preferred sources parameter

# Response models
class NewsSource(BaseModel):
    name: str
    url: Optional[str] = None

class NewsArticle(BaseModel):
    id: str
    title: str
    summary: str
    source: NewsSource
    published_date: str
    link: str

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    message: str
    total_found: int  # Added to track total found before limiting by max_articles
    available_sources: List[str] = []  # Added to return available sources for the UI

# Comprehensive RSS feeds by language
RSS_FEEDS = {
    "en": [
        # Major English News Sources in India
        "http://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
        "https://www.theguardian.com/world/india/rss",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://www.thehindu.com/feeder/default.rss",
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "https://www.indiatoday.in/rss/home",
        "http://indianexpress.com/print/front-page/feed/",
        "https://www.news18.com/rss/world.xml",
        "https://www.dnaindia.com/feeds/india.xml",
        "https://www.firstpost.com/rss/india.xml",
        
        # Business and Finance News
        "https://www.business-standard.com/rss/home_page_top_stories.rss",
        "https://www.outlookindia.com/rss/main/magazine",
        "https://www.freepressjournal.in/stories.rss",
        "https://www.deccanchronicle.com/rss_feed/",
        "http://www.moneycontrol.com/rss/latestnews.xml",
        "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
        "https://www.oneindia.com/rss/news-fb.xml",
        "http://feeds.feedburner.com/ScrollinArticles.rss",
        "https://www.financialexpress.com/feed/",
        "https://www.thehindubusinessline.com/feeder/default.rss",
        "http://feeds.feedburner.com/techgenyz",
        "https://theprint.in/feed/",
        "https://prod-qt-images.s3.amazonaws.com/production/swarajya/feed.xml"
    ],
    "hi": [
        # Hindi News Sources
        "https://www.bhaskar.com/rss-feed/1061/",
        "https://www.amarujala.com/rss/breaking-news.xml",
        "https://navbharattimes.indiatimes.com/rssfeedsdefault.cms",
        "http://api.patrika.com/rss/india-news",
        "https://www.jansatta.com/feed/",
        "https://feed.livehindustan.com/rss/3127",
        "https://feeds.feedburner.com/opindia"
    ],
    "gu": [
        # Gujarati News Sources
        "https://www.gujaratsamachar.com/rss/top-stories",
        "https://www.divyabhaskar.co.in/rss-feed/1037/"
    ],
    "mr": [
        # Marathi News Sources
        "https://maharashtratimes.com/rssfeedsdefault.cms",
        "https://www.loksatta.com/desh-videsh/feed/",
        "https://lokmat.news18.com/rss/program.xml"
    ],
    "ta": [
        # Tamil News Sources
        "https://tamil.oneindia.com/rss/tamil-news.xml",
        "https://tamil.samayam.com/rssfeedstopstories.cms",
        "https://www.dinamani.com/rss/latest-news.xml"
    ],
    "te": [
        # Telugu News Sources
        "https://telugu.oneindia.com/rss/telugu-news.xml",
        "https://telugu.samayam.com/rssfeedstopstories.cms",
        "https://www.sakshi.com/rss.xml"
    ]
}

# User-friendly names for news sources by domain
NEWS_SOURCE_NAMES = {
    "bbci.co.uk": "BBC News",
    "theguardian.com": "The Guardian",
    "timesofindia.indiatimes.com": "Times of India",
    "thehindu.com": "The Hindu",
    "ndtv.com": "NDTV News",
    "indiatoday.in": "India Today",
    "indianexpress.com": "Indian Express",
    "news18.com": "News18",
    "dnaindia.com": "DNA India",
    "firstpost.com": "Firstpost",
    "business-standard.com": "Business Standard",
    "outlookindia.com": "Outlook India",
    "freepressjournal.in": "Free Press Journal",
    "deccanchronicle.com": "Deccan Chronicle",
    "moneycontrol.com": "Moneycontrol",
    "economictimes.indiatimes.com": "Economic Times",
    "oneindia.com": "Oneindia",
    "scroll.in": "Scroll.in",
    "financialexpress.com": "Financial Express",
    "thehindubusinessline.com": "Hindu Business Line",
    "techgenyz.com": "TechGenyz",
    "theprint.in": "ThePrint",
    "swarajya": "Swarajya",
    "bhaskar.com": "Dainik Bhaskar",
    "amarujala.com": "Amar Ujala",
    "navbharattimes.indiatimes.com": "Navbharat Times",
    "patrika.com": "Patrika",
    "jansatta.com": "Jansatta",
    "livehindustan.com": "Live Hindustan",
    "opindia": "OpIndia",
    "gujaratsamachar.com": "Gujarat Samachar",
    "divyabhaskar.co.in": "Divya Bhaskar",
    "maharashtratimes.com": "Maharashtra Times",
    "loksatta.com": "Loksatta",
    "lokmat.news18.com": "Lokmat News18",
    "tamil.oneindia.com": "Tamil Oneindia",
    "tamil.samayam.com": "Tamil Samayam",
    "dinamani.com": "Dinamani",
    "telugu.oneindia.com": "Telugu Oneindia",
    "telugu.samayam.com": "Telugu Samayam", 
    "sakshi.com": "Sakshi"
}

# News cache store
NEWS_CACHE = {}
CACHE_EXPIRY = 1800  # 30 minutes in seconds

@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI"}

# Get available news sources for a language
@app.get("/api/news/sources/{language}")
def get_news_sources(language: str):
    """Get list of available news sources for a specific language"""
    if language not in RSS_FEEDS:
        raise HTTPException(status_code=404, detail=f"Language {language} not supported")
    
    feeds = RSS_FEEDS[language]
    sources = []
    
    for feed_url in feeds:
        domain = feed_url.split('/')[2]
        source_name = NEWS_SOURCE_NAMES.get(domain, domain)
        sources.append({
            "name": source_name,
            "url": feed_url,
            "id": domain
        })
    
    return {"sources": sources}

def fetch_rss_feed(feed_url, max_retries=3):
    """Fetch articles from a single RSS feed with retry logic"""
    for retry in range(max_retries):
        try:
            # Set socket timeout for this request
            socket.setdefaulttimeout(15)
            
            # Parse the feed
            feed = feedparser.parse(feed_url)
            
            # Check if feed has entries
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                print(f"Warning: No entries found in {feed_url}")
                return []
            
            # Get source name from feed or fallback to URL
            source_name = feed.feed.title if hasattr(feed.feed, 'title') else feed_url.split('/')[2]
            
            # Process each entry
            articles = []
            for entry in feed.entries:
                try:
                    # Extract and clean data
                    title = entry.title if hasattr(entry, 'title') else ""
                    title = re.sub(r'<.*?>', '', title)  # Remove HTML tags
                    
                    summary = entry.summary if hasattr(entry, 'summary') else ""
                    summary = re.sub(r'<.*?>', '', summary)  # Remove HTML tags
                    
                    # Extract publication date if available
                    pub_date = datetime.now().isoformat()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                        except:
                            pass
                    
                    # Create article object
                    article = {
                        "id": str(hash(title + source_name)),
                        "title": title,
                        "summary": summary,
                        "source": {"name": source_name, "url": feed_url},
                        "published_date": pub_date,
                        "link": entry.link if hasattr(entry, 'link') else ""
                    }
                    articles.append(article)
                except Exception as e:
                    print(f"Error processing entry from {feed_url}: {e}")
                    continue
            
            print(f"Fetched {len(articles)} articles from {feed_url}")
            return articles
        
        except Exception as e:
            if retry == max_retries - 1:
                print(f"Error fetching {feed_url} after {max_retries} retries: {e}")
                return []
            else:
                print(f"Retrying {feed_url} ({retry+2}/{max_retries})...")
                time.sleep(1)  # Wait before retrying

def fetch_all_feeds(feed_urls, max_workers=10):  # Increased workers to fetch more feeds
    """Fetch articles from multiple RSS feeds concurrently"""
    all_articles = []
    successful_feeds = 0
    
    # Use ThreadPoolExecutor for concurrent fetching
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all feed fetching tasks
        future_to_url = {executor.submit(fetch_rss_feed, url): url for url in feed_urls}
        
        # Process results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
                    successful_feeds += 1
            except Exception as e:
                print(f"Error processing results from {url}: {e}")
    
    print(f"Successfully fetched from {successful_feeds}/{len(feed_urls)} feeds")
    print(f"Total articles collected: {len(all_articles)}")
    
    return all_articles

# Gemini 1.5 Flash inspired search enhancement
def advanced_semantic_search(articles, query, threshold=0.2):
    """
    Enhanced search function inspired by Gemini 1.5 Flash capabilities.
    This simulates semantic search with more advanced term matching.
    """
    if not query:
        return articles, 0
    
    # Normalize the query
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    # Special case for cricket/sports queries like "CSK vs MI"
    is_sports_query = any(term in query_lower for term in ["vs", "cricket", "ipl", "match", "game", "score"])
    team_acronyms = ["csk", "mi", "rcb", "kkr", "srh", "dc", "pkbs", "rr", "gt", "lsg"]
    
    # Enhanced matching based on multiple factors
    scored_articles = []
    
    # First pass - identify potentially relevant articles
    for article in articles:
        title_lower = article["title"].lower()
        summary_lower = article["summary"].lower()
        combined_text = f"{title_lower} {summary_lower}"
        
        # Calculate various relevance signals
        exact_query_match = query_lower in combined_text
        
        # Term matching - count how many query terms appear in the text
        term_matches = sum(1 for term in query_terms if term in combined_text)
        term_match_ratio = term_matches / max(1, len(query_terms))
        
        # Check for team acronyms in sports queries
        team_match = 0
        if is_sports_query:
            team_match = sum(1 for team in team_acronyms if team in combined_text)
        
        # Title matching has higher weight
        title_term_matches = sum(1 for term in query_terms if term in title_lower)
        title_match_ratio = title_term_matches / max(1, len(query_terms))
        
        # Calculate final relevance score (emulating semantic matching)
        relevance_score = 0
        
        if exact_query_match:
            relevance_score += 0.5
        
        relevance_score += 0.3 * term_match_ratio
        relevance_score += 0.4 * title_match_ratio
        
        if is_sports_query:
            relevance_score += 0.2 * min(1.0, team_match)
        
        # Date recency bonus (up to 0.1)
        try:
            pub_date = datetime.fromisoformat(article["published_date"])
            current_date = datetime.now()
            days_old = (current_date - pub_date).days
            recency_bonus = max(0, 0.1 - (days_old * 0.01))  # Newer articles get a small boost
            relevance_score += recency_bonus
        except:
            pass
        
        # Normalize final score
        relevance_score = min(1.0, relevance_score)
        
        if relevance_score > threshold or term_matches > 0:
            article["relevance"] = relevance_score
            scored_articles.append(article)
    
    # Sort by relevance score
    scored_articles.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    
    return scored_articles, len(scored_articles)

@app.post("/api/news", response_model=NewsResponse)
async def get_news(request: NewsRequest):
    try:
        language = request.language
        query = request.query
        max_articles = request.max_articles
        preferred_sources = request.preferred_sources
        
        # Check cache first
        cache_key = f"{language}-all"
        current_time = time.time()
        
        # Use cached data if available and not expired
        if cache_key in NEWS_CACHE and (current_time - NEWS_CACHE[cache_key]["timestamp"] < CACHE_EXPIRY):
            print(f"Using cached news data for {language}")
            articles = NEWS_CACHE[cache_key]["articles"]
        else:
            # Get the appropriate feeds based on language
            feeds = RSS_FEEDS.get(language, RSS_FEEDS["en"])
            
            # Fetch all feeds concurrently
            articles = fetch_all_feeds(feeds)
            
            # Cache the results
            NEWS_CACHE[cache_key] = {
                "timestamp": current_time,
                "articles": articles
            }
        
        # Get unique list of available sources for this language
        available_sources = []
        source_set = set()
        for article in articles:
            source_name = article["source"]["name"]
            source_url = article["source"]["url"]
            if source_name not in source_set:
                source_set.add(source_name)
                available_sources.append({
                    "name": source_name,
                    "url": source_url
                })
        
        # Filter by preferred sources if specified
        if preferred_sources and len(preferred_sources) > 0:
            articles = [a for a in articles if any(ps.lower() in a["source"]["name"].lower() for ps in preferred_sources)]
            if not articles:
                return {
                    "articles": [],
                    "message": f"No articles found from your preferred sources. Try selecting different sources.",
                    "total_found": 0,
                    "available_sources": [s["name"] for s in available_sources]
                }
        
        print(f"Total articles after source filtering: {len(articles)}")
        
        # Apply Gemini 1.5 Flash inspired search
        if query:
            filtered_articles, total_matches = advanced_semantic_search(articles, query)
            
            if filtered_articles:
                message = f"Found {total_matches} articles matching '{query}'."
            else:
                # Fallback to date-sorted articles
                filtered_articles = sorted(articles, key=lambda x: x.get("published_date", ""), reverse=True)
                total_matches = len(filtered_articles)
                message = f"No exact matches for '{query}'. Showing {min(max_articles, total_matches)} recent articles."
        else:
            # Sort by published date (newest first) if no query
            filtered_articles = sorted(articles, key=lambda x: x.get("published_date", ""), reverse=True)
            total_matches = len(filtered_articles)
            message = f"Showing {min(max_articles, total_matches)} recent news articles."
        
        # If no articles after all filtering, provide a clear message
        if not filtered_articles:
            return {
                "articles": [],
                "message": "No news articles found. Please try a different search query or language selection.",
                "total_found": 0,
                "available_sources": [s["name"] for s in available_sources]
            }
        
        # Limit to requested max_articles (but keep track of total found)
        limited_articles = filtered_articles[:max_articles]
        
        return {
            "articles": limited_articles,
            "message": message,
            "total_found": total_matches,
            "available_sources": [s["name"] for s in available_sources]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing news: {str(e)}")