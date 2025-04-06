from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import feedparser
import re
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import time
from datetime import datetime, timedelta
import json
import socket
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
import os


import google.generativeai as genai
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDOrCItR_V5KP0oD0jP1OMmTNrnS4Oe2_k")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# NewsAPI fallback
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "dd52e9d920b247e1b51fa8c08ca5b662")  # Get your free key from newsapi.org

# Set default socket timeout for all connections
socket.setdefaulttimeout(5.0)  # Reduce timeout from 15s to 5s

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
    page: int = 1
    page_size: int = 10
    preferred_sources: List[str] = []
    category: Optional[str] = None

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
    relevance: Optional[float] = None
    image_url: Optional[str] = None

class NewsResponse(BaseModel):
    articles: List[NewsArticle]
    message: str
    total_found: int
    total_pages: int
    current_page: int
    available_sources: List[str] = []
    available_categories: List[str] = []

# RSS feeds configuration reorganized by category
RSS_FEEDS = {
    "News": {
        "en": [
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
            "https://www.freepressjournal.in/stories.rss",
            "https://www.deccanchronicle.com/rss_feed/",
            "https://www.oneindia.com/rss/news-fb.xml",
            "http://feeds.feedburner.com/ScrollinArticles.rss",
            "https://theprint.in/feed/"
        ],
        "hi": [
            "https://www.bhaskar.com/rss-feed/1061/",
            "https://www.amarujala.com/rss/breaking-news.xml",
            "https://navbharattimes.indiatimes.com/rssfeedsdefault.cms",
            "http://api.patrika.com/rss/india-news",
            "https://www.jansatta.com/feed/",
            "https://feed.livehindustan.com/rss/3127"
        ],
        "gu": [
            "https://www.gujaratsamachar.com/rss/top-stories",
            "https://www.divyabhaskar.co.in/rss-feed/1037/"
        ],
        "mr": [
            "https://maharashtratimes.com/rssfeedsdefault.cms",
            "https://www.loksatta.com/desh-videsh/feed/",
            "https://lokmat.news18.com/rss/program.xml"
        ],
        "ta": [
            "https://tamil.oneindia.com/rss/tamil-news.xml",
            "https://tamil.samayam.com/rssfeedstopstories.cms",
            "https://www.dinamani.com/rss/latest-news.xml"
        ],
        "te": [
            "https://telugu.oneindia.com/rss/telugu-news.xml",
            "https://telugu.samayam.com/rssfeedstopstories.cms",
            "https://www.sakshi.com/rss.xml"
        ]
    },
    "Business & Economy": {
        "en": [
            "https://www.business-standard.com/rss/home_page_top_stories.rss",
            "https://www.outlookindia.com/rss/main/magazine",
            "http://www.moneycontrol.com/rss/latestnews.xml",
            "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
            "https://www.financialexpress.com/feed/",
            "https://www.thehindubusinessline.com/feeder/default.rss",
            "http://feeds.feedburner.com/techgenyz",
            "https://prod-qt-images.s3.amazonaws.com/production/swarajya/feed.xml"
        ]
    },
    "Android": {
        "en": [
            "https://blog.google/products/android/rss",
            "https://www.reddit.com/r/android/.rss",
            "https://www.androidauthority.com/feed",
            "https://www.youtube.com/feeds/videos.xml?user=AndroidAuthority",
            "https://androidauthority.libsyn.com/rss",
            "http://feeds.androidcentral.com/androidcentral",
            "http://feeds.feedburner.com/AndroidCentralPodcast",
            "https://androidcommunity.com/feed/",
            "http://feeds.feedburner.com/AndroidPolice",
            "https://www.androidguys.com/feed",
            "https://www.cultofandroid.com/feed",
            "https://www.cyanogenmods.org/feed",
            "https://www.droid-life.com/feed",
            "http://feeds2.feedburner.com/AndroidPhoneFans",
            "http://feeds.feedburner.com/AndroidNewsGoogleAndroidForums"
        ]
    },
    "Apple": {
        "en": [
            "https://9to5mac.com/feed",
            "https://www.youtube.com/feeds/videos.xml?user=Apple",
            "https://www.apple.com/newsroom/rss-feed.rss",
            "https://appleinsider.com/rss/news/",
            "https://www.cultofmac.com/feed",
            "https://daringfireball.net/feeds/main",
            "https://www.youtube.com/feeds/videos.xml?user=macrumors",
            "http://feeds.macrumors.com/MacRumors-Mac",
            "https://www.macstories.net/feed",
            "https://www.macworld.com/index.rss",
            "https://marco.org/rss",
            "http://feeds.feedburner.com/osxdaily",
            "https://www.loopinsight.com/feed",
            "https://www.reddit.com/r/apple/.rss",
            "http://feeds.feedburner.com/TheiPhoneBlog",
            "https://www.reddit.com/r/iphone/.rss"

        ]
    },
    "Photography": {
        "en": [
            "https://iso.500px.com/feed/",
            "https://500px.com/editors.rss",
            "https://www.bostonglobe.com/rss/bigpicture",
            "https://www.canonrumors.com/feed/",
            "https://feeds.feedburner.com/DigitalPhotographySchool",
            "https://www.lightstalking.com/feed/",
            "https://lightroomkillertips.com/feed/",
            "http://feeds.feedburner.com/OneBigPhoto",
            "https://petapixel.com/feed/",
            "http://feeds.feedburner.com/blogspot/WOBq",
            "https://stuckincustoms.com/feed/",
            "https://iso.500px.com/feed/",
            "https://500px.com/editors.rss",
            "https://www.bostonglobe.com/rss/bigpicture",
            "https://www.canonrumors.com/feed/",
            "https://feeds.feedburner.com/DigitalPhotographySchool",
            "https://www.lightstalking.com/feed/",
            "https://lightroomkillertips.com/feed/",
            "http://feeds.feedburner.com/OneBigPhoto",
            "https://petapixel.com/feed/",
            "http://feeds.feedburner.com/blogspot/WOBq",
            "https://stuckincustoms.com/feed/",
            "https://feeds.feedburner.com/TheSartorialist"

        ]
    },
    "Beauty": {
        "en": [
            "https://www.elle.com/rss/beauty.xml/",
            "https://fashionista.com/.rss/excerpt/beauty",
            "https://www.fashionlady.in/category/beauty-tips/feed",
            "https://thebeautybrains.com/blog/feed/",
            "https://www.wearedore.com/feed",
            "http://feeds.feedburner.com/frmheadtotoe",
            "https://feeds.feedburner.com/intothegloss/oqoU",
            "https://www.popsugar.com/beauty/feed",
            "https://www.refinery29.com/beauty/rss.xml",
            "https://www.yesstyle.com/blog/category/the-beauty-blog/feed/",
            "https://thebeautylookbook.com/feed"
        ]
    },
    "Fashion": {
        "en": [
            "https://www.elle.com/rss/fashion.xml/",
            "https://www.theguardian.com/fashion/rss",
            "https://www.fashionlady.in/category/fashion/feed",
            "https://www.fashionbeans.com/rss-feed/?category=fashion",
            "https://fashionista.com/.rss/excerpt/",
            "https://rss.nytimes.com/services/xml/rss/nyt/FashionandStyle.xml",
            "https://www.popsugar.com/fashion/feed",
            "https://www.refinery29.com/fashion/rss.xml",
            "https://www.yesstyle.com/blog/category/trend-and-style/feed/",
            "https://www.whowhatwear.com/rss"

        ]
    },
    "Tech": {
        "en": [
            "https://atp.fm/rss",
            "https://www.relay.fm/analogue/feed",
            "http://feeds.arstechnica.com/arstechnica/index",
            "https://www.youtube.com/feeds/videos.xml?user=CNETTV",
            "https://www.cnet.com/rss/news/",
            "https://www.relay.fm/clockwise/feed",
            "https://gizmodo.com/rss",
            "https://news.ycombinator.com/rss",
            "https://lifehacker.com/rss",
            "https://www.youtube.com/feeds/videos.xml?user=LinusTechTips",
            "https://www.youtube.com/feeds/videos.xml?user=marquesbrownlee",
            "http://feeds.mashable.com/Mashable",
            "https://readwrite.com/feed/",
            "https://feeds.megaphone.fm/replyall",
            "https://www.relay.fm/rocket/feed",
            "http://rss.slashdot.org/Slashdot/slashdotMain",
            "http://stratechery.com/feed/",
            "http://feeds.feedburner.com/TechCrunch",
            "https://www.blog.google/rss/",
            "https://thenextweb.com/feed/",
            "https://www.youtube.com/feeds/videos.xml?user=TheVerge",
            "https://www.theverge.com/rss/index.xml",
            "https://feeds.megaphone.fm/vergecast",
            "https://feeds.twit.tv/twit.xml",
            "https://www.youtube.com/feeds/videos.xml?user=unboxtherapy",
            "https://www.engadget.com/rss.xml"

            
        ]
    },
    "Programming": {
        "en": [
            "https://dev.to/feed",
            "https://stackoverflow.blog/feed/",
            "https://css-tricks.com/feed/",
            "https://www.freecodecamp.org/news/rss/",
            "https://blog.github.com/feed/",
            "https://medium.com/feed/better-programming",
            "https://codeascraft.com/feed/atom/",
            "http://feeds.codenewbie.org/cnpodcast.xml",
            "https://feeds.feedburner.com/codinghorror",
            "https://completedeveloperpodcast.com/feed/podcast/",
            "https://overreacted.io/rss.xml",
            "https://feeds.simplecast.com/dLRotFGk",
            "https://blog.twitter.com/engineering/en_us/blog.rss",
            "https://feeds.twit.tv/floss.xml",
            "https://engineering.fb.com/feed/",
            "https://about.gitlab.com/atom.xml",
            "http://feeds.feedburner.com/GDBcode",
            "https://www.youtube.com/feeds/videos.xml?user=GoogleTechTalks",
            "https://medium.com/feed/hackernoon",
            "https://feeds.simplecast.com/gvtxUiIf",
            "https://feed.infoq.com",
            "https://instagram-engineering.com/feed/",
            "https://blog.jooq.org/feed",
            "https://blog.jetbrains.com/feed",
            "https://www.joelonsoftware.com/feed/",
            "https://engineering.linkedin.com/blog.rss.html",
            "https://martinfowler.com/feed.atom",
            "https://netflixtechblog.com/feed",
            "https://buffer.com/resources/overflow/rss/",
            "https://softwareengineeringdaily.com/category/podcast/feed",
            "https://www.thirtythreeforty.net/posts/index.xml",
            "https://engineering.prezi.com/feed",
            "http://feeds.feedburner.com/ProgrammingThrowdown",
            "https://www.thecrazyprogrammer.com/category/programming/feed",
            "https://robertheaton.com/feed.xml",
            "http://feeds.hanselman.com/ScottHanselman",
            "http://scripting.com/rss.xml",
            "https://m.signalvnoise.com/feed/",
            "https://slack.engineering/feed",
            "https://feeds.fireside.fm/sdt/rss",
            "http://feeds.feedburner.com/se-radio",
            "https://developers.soundcloud.com/blog/blog.rss",
            "https://labs.spotify.com/feed/",
            "https://stackabuse.com/rss/",
            "https://stackoverflow.blog/feed/",
            "http://6figuredev.com/feed/rss/",
            "https://medium.com/feed/airbnb-engineering",
            "https://cynicaldeveloper.com/feed/podcast",
            "https://github.blog/feed/",
            "https://feeds.transistor.fm/productivity-in-tech-podcast",
            "http://therabbithole.libsyn.com/rss",
            "https://feeds.simplecast.com/XA_851k3",
            "https://feeds.fireside.fm/standup/rss",
            "https://thewomenintechshow.com/category/podcast/feed/",
            "https://www.reddit.com/r/programming/.rss"

        ]
    },
    "Web Development": {
        "en": [
            "https://css-tricks.com/feed/",
            "https://www.smashingmagazine.com/feed/",
            "https://alistapart.com/main/feed/",
            "https://www.sitepoint.com/feed/",
            "https://developer.mozilla.org/en-US/blog/feed.xml"
        ]
    },
    "Sports": {
        "en": [
            "https://www.espn.com/espn/rss/news",
            "https://sports.ndtv.com/rss/all",
            "https://www.sportskeeda.com/feed",
            "http://feeds.bbci.co.uk/sport/rss.xml",
            "https://www.reddit.com/r/sports.rss",
            "http://feeds.skynews.com/feeds/rss/sports.xml",
            "https://sports.yahoo.com/rss/",
            "https://rss.app/feeds/Bm1Bif5VM1GNfYgf.xml",

        ]
    },
    "Cricket": {
        "en": [
            "http://feeds.bbci.co.uk/sport/cricket/rss.xml",
            "http://feeds.feedburner.com/cantbowlcantthrow",
            "https://rss.app/feeds/Bm1Bif5VM1GNfYgf.xml",
            "https://www.youtube.com/feeds/videos.xml?channel_id=UCSRQXk5yErn4e14vN76upOw",
            "https://www.reddit.com/r/Cricket/.rss",
            "https://rss.acast.com/cricket-unfiltered",
            "http://www.espncricinfo.com/rss/content/story/feeds/0.xml",
            "https://www.theguardian.com/sport/cricket/rss",
            "https://www.theroar.com.au/cricket/feed/",
            "https://www.youtube.com/feeds/videos.xml?user=ecbcricket",
            "http://feeds.feedburner.com/ndtvsports-cricket",
            "https://www.youtube.com/feeds/videos.xml?channel_id=UCiWrjBhlICf_L_RK5y6Vrxw",
            "https://www.spreaker.com/show/3387348/episodes/feed",
            "https://www.youtube.com/feeds/videos.xml?user=TheOfficialSLC",
            "https://podcasts.files.bbci.co.uk/p02gsrmh.rss",
            "https://feeds.megaphone.fm/ESP9247246951",
            "https://podcasts.files.bbci.co.uk/p02pcb4w.rss",
            "https://podcasts.files.bbci.co.uk/p02nrsl2.rss",
            "http://rss.acast.com/theanalystinsidecricket",
            "https://rss.whooshkaa.com/rss/podcast/id/1308",
            "https://www.wisden.com/feed",
            "http://feeds.soundcloud.com/users/soundcloud:users:341034518/sounds.rss",
            "https://www.youtube.com/feeds/videos.xml?user=cricketaustraliatv",

        ]
    },
    "Football": {
        "en": [
            "https://www.goal.com/feeds/en/news",
            "https://www.football365.com/feed",
            "https://www.reddit.com/r/Championship/.rss?format=xml",
            "https://www.reddit.com/r/football/.rss?format=xml",
            "https://www.goal.com/feeds/en/news",
            "https://www.football365.com/feed",
            "https://www.soccernews.com/feed"
            "https://rss.app/feeds/Bm1Bif5VM1GNfYgf.xml"

        ]
    },
    "Movies": {
        "en": [
                "https://feeds2.feedburner.com/slashfilm",
                "https://www.aintitcool.com/node/feed/",
                "https://www.comingsoon.net/feed",
                "https://deadline.com/feed/",
                "https://filmschoolrejects.com/feed/",
                "https://www.firstshowing.net/feed/",
                "https://www.indiewire.com/feed",
                "https://reddit.com/r/movies/.rss",
                "https://www.bleedingcool.com/movies/feed/",
                "https://film.avclub.com/rss",
                "https://variety.com/feed/"

        ]
    },
    "Gaming": {
        "en": [
            "https://www.polygon.com/rss/index.xml",
            "https://kotaku.com/rss",
            "https://www.ign.com/rss/articles/feed"
            "https://www.escapistmagazine.com/v2/feed/",
            "https://www.eurogamer.net/?format=rss",
            "http://feeds.feedburner.com/GamasutraNews",
            "https://www.gamespot.com/feeds/mashup/",
            "http://feeds.ign.com/ign/all",
            "https://indiegamesplus.com/feed",
            "https://kotaku.com/rss",
            "https://www.makeupandbeautyblog.com/feed/",
            "http://feeds.feedburner.com/psblog",
            "https://www.polygon.com/rss/index.xml",
            "http://feeds.feedburner.com/RockPaperShotgun",
            "https://store.steampowered.com/feeds/news.xml",
            "http://feeds.feedburner.com/TheAncientGamingNoob",
            "https://toucharcade.com/community/forums/-/index.rss",
            "https://majornelson.com/feed/",
            "https://www.reddit.com/r/gaming.rss"

        ]
    },
    "Science": {
        "en": [
            "http://rss.sciam.com/sciam/60secsciencepodcast",
            "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
            "https://podcasts.files.bbci.co.uk/p002w557.rss",
            "https://flowingdata.com/feed",
            "https://www.omnycontent.com/d/playlist/aaea4e69-af51-495e-afc9-a9760146922b/2a195077-f014-41d2-8313-ab190186b4c2/277bcd5c-0a05-4c14-8ba6-ab190186b4d5/podcast.rss",
            "https://gizmodo.com/tag/science/rss",
            "https://feeds.npr.org/510308/podcast.xml",
            "https://feeds.npr.org/510307/podcast.xml",
            "https://www.sciencedaily.com/rss/all.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
            "https://www.nature.com/nature.rss",
            "https://phys.org/rss-feed/",
            "https://probablyscience.libsyn.com/rss",
            "http://feeds.wnyc.org/radiolab",
            "https://reddit.com/r/science/.rss",
            "https://feeds.simplecast.com/y1LF_sn2",
            "https://www.wired.com/feed/category/science/latest/rss",
            "http://feeds.gimletmedia.com/ScienceVs",
            "https://sciencebasedmedicine.org/feed/",
            "http://rss.sciam.com/ScientificAmerican-Global",
            "https://shirtloadsofscience.libsyn.com/rss",
            "https://pa.tedcdn.com/feeds/talks.rss",
            "https://podcasts.files.bbci.co.uk/b00snr0w.rss",
            "http://www.twis.org/feed/",
            "https://www.reddit.com/r/space/.rss?format=xml",
            "https://www.nasa.gov/rss/dyn/breaking_news.rss",
            "https://www.newscientist.com/subject/space/feed/",
            "https://www.skyandtelescope.com/feed/",
            "https://www.theguardian.com/science/space/rss",
            "https://www.space.com/feeds/all",
            "https://www.youtube.com/feeds/videos.xml?user=spacexchannel"

        ]
    },
    "Space": {
        "en": [
            "https://www.space.com/feeds/all",
            "https://www.nasa.gov/rss/dyn/breaking_news.rss",
            "https://www.reddit.com/r/space/.rss?format=xml",
            "https://www.nasa.gov/rss/dyn/breaking_news.rss",
            "https://www.newscientist.com/subject/space/feed/",
            "https://www.skyandtelescope.com/feed/",
            "https://www.theguardian.com/science/space/rss",
            "https://www.youtube.com/feeds/videos.xml?user=spacexchannel",

        ]
    },
    "Food": {
        "en": [
            "https://www.101cookbooks.com/feed",
            "https://www.youtube.com/feeds/videos.xml?user=bgfilms",
            "https://www.youtube.com/feeds/videos.xml?user=BonAppetitDotCom",
            "https://cnz.to/feed/",
            "https://www.davidlebovitz.com/feed/",
            "http://feeds.feedburner.com/food52-TheAandMBlog",
            "https://greenkitchenstories.com/feed/",
            "https://www.howsweeteats.com/feed/",
            "http://joythebaker.com/feed/",
            "https://www.thekitchn.com/main.rss",
            "https://www.youtube.com/feeds/videos.xml?user=LauraVitalesKitchen",
            "https://www.loveandoliveoil.com/feed",
            "https://rss.nytimes.com/services/xml/rss/nyt/DiningandWine.xml",
            "https://ohsheglows.com/feed/",
            "https://www.youtube.com/feeds/videos.xml?user=SeriousEats",
            "http://feeds.feedburner.com/seriouseats/recipes",
            "http://www.shutterbean.com/feed/",
            "https://www.skinnytaste.com/feed/",
            "https://www.sproutedkitchen.com/home?format=rss",
            "https://blog.williams-sonoma.com/feed/",
            "http://feeds.feedburner.com/smittenkitchen"


        ]
    },
    "Travel": {
        "en": [
            "https://www.atlasobscura.com/feeds/latest",
            "https://www.livelifetravel.world/feed/",
            "https://www.lonelyplanet.com/news/feed/atom/",
            "https://rss.nytimes.com/services/xml/rss/nyt/Travel.xml",
            "https://www.nomadicmatt.com/travel-blog/feed/",
            "https://www.theguardian.com/uk/travel/rss"

        ]
    },
    "Personal Finance": {
        "en": [
            "https://www.fool.com/feed/",
            "https://www.mrmoneymustache.com/feed/",
            "https://www.moneycontrol.com/rss/mfcolumnists.xml"
        ]
    },
    "UI/UX": {
        "en": [
            "https://uxdesign.cc/feed",
            "https://www.nngroup.com/feed/rss/",
            "https://www.smashingmagazine.com/category/ux-design/feed/"
        ]
    },
    "Interior Design": {
        "en": [
            "https://www.designsponge.com/feed",
            "https://www.apartmenttherapy.com/main.rss",
            "https://www.dezeen.com/interiors/feed/"
        ]
    },
    "DIY": {
        "en": [
            "https://www.instructables.com/feed.rss",
            "https://makezine.com/feed/",
            "https://www.doityourself.com/feed"
        ]
    },
    "History": {
        "en": [
            "https://feeds.megaphone.fm/ESP5765452710",
            "https://americanhistory.si.edu/blog/feed",
            "https://feeds.feedburner.com/dancarlin/history?format=xml",
            "https://www.historyisnowmagazine.com/blog?format=RSS",
            "http://www.historynet.com/feed",
            "https://feeds.megaphone.fm/lore",
            "https://feeds.megaphone.fm/revisionisthistory",
            "https://www.thehistoryreader.com/feed/",
            "https://feeds.npr.org/510333/podcast.xml",
            "https://feeds.megaphone.fm/YMRT7068253588",
            "http://feeds.thememorypalace.us/thememorypalace"

        ]
    },
    "Books": {
        "en": [
            "https://www.nybooks.com/feed/",
            "https://lithub.com/feed/",
            "https://www.goodreads.com/blog/list_rss.xml",
            "https://ayearofreadingtheworld.com/feed/",
            "https://aestasbookblog.com/feed/",
            "https://bookriot.com/feed/",
            "https://www.kirkusreviews.com/feeds/rss/",
            "https://www.newinbooks.com/feed/",
            "https://reddit.com/r/books/.rss",
            "https://wokeread.home.blog/feed/"

        ]
    },
    "Cars": {
        "en": [
            "https://www.caranddriver.com/rss/all.xml/",
            "https://www.autocar.co.uk/rss",
            "https://www.motor1.com/rss/news/all/",
            "https://www.autoblog.com/rss.xml",
            "https://www.autocarindia.com/RSS/rss.ashx?type=all_bikes",
            "https://www.autocarindia.com/RSS/rss.ashx?type=all_cars",
            "https://www.autocarindia.com/RSS/rss.ashx?type=News",
            "https://www.autocar.co.uk/rss",
            "https://feeds.feedburner.com/BmwBlog",
            "https://www.bikeexif.com/feed",
            "https://www.carbodydesign.com/feed/",
            "https://www.carscoops.com/feed/",
            "https://www.reddit.com/r/formula1/.rss",
            "https://jalopnik.com/rss",
            "https://www.autocarindia.com/rss/all",
            "https://www.caranddriver.com/rss/all.xml/",
            "https://petrolicious.com/feed",
            "http://feeds.feedburner.com/autonews/AutomakerNews",
            "http://feeds.feedburner.com/autonews/EditorsPicks",
            "http://feeds.feedburner.com/speedhunters",
            "https://www.thetruthaboutcars.com/feed/",
            "https://bringatrailer.com/feed/"

        ]
    },
    "Funny": {
        "en": [
            "https://www.theonion.com/rss",
            "https://www.collegehumor.com/feed",
            "https://rss.gocomics.com/foxtrot"
        ]
    },
    "Startups": {
        "en": [
            "https://techcrunch.com/startups/feed/",
            "https://news.ycombinator.com/rss",
            "https://feeds.feedburner.com/PaulGrahamUnofficialRssFeed"
        ]
    },
    "Music": {
        "en": [
            "https://www.billboard.com/articles/rss.xml",
            "http://consequenceofsound.net/feed",
            "https://edm.com/.rss/full/",
            "http://feeds.feedburner.com/metalinjection",
            "https://www.musicbusinessworldwide.com/feed/",
            "http://pitchfork.com/rss/news",
            "http://songexploder.net/feed",
            "https://www.youredm.com/feed",

        ]
    },
    "Architecture": {
        "en": [
            "https://www.archdaily.com/feed",
            "https://www.dezeen.com/architecture/feed/",
            "https://www.architecturaldigest.com/feed/rss"
        ]
    },
    "Television": {
        "en": [
            "https://www.tvguide.com/rss/news/",
            "https://variety.com/v/tv/feed/",
            "https://deadline.com/category/tv/feed/"
            "https://www.bleedingcool.com/tv/feed/",
            "https://www.tvfanatic.com/rss.xml",
            "https://tvline.com/feed/",
            "https://reddit.com/r/television/.rss",
            "https://tv.avclub.com/rss",
            "http://feeds.feedburner.com/thetvaddict/AXob",

        ]
    },
    "Tennis": {
        "en": [
            "https://www.atptour.com/en/media/rss-feed/xml-feed",
            "https://www.tennis.com/feed"
        ]
    },
    "iOS Development": {
        "en": [
            "https://developer.apple.com/news/rss/news.rss",
            "https://www.raywenderlich.com/feed",
            "https://iosdevweekly.com/issues.rss"
        ]
    }
}

# User-friendly names for news sources
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
    "sakshi.com": "Sakshi",
    "newsapi.org": "News API",
    # Adding more source names for the new categories
    "androidauthority.com": "Android Authority",
    "androidcentral.com": "Android Central",
    "androidpolice.com": "Android Police",
    "macrumors.com": "MacRumors",
    "cultofmac.com": "Cult of Mac",
    "9to5mac.com": "9to5Mac",
    "petapixel.com": "PetaPixel",
    "500px.com": "500px",
    "techcrunch.com": "TechCrunch",
    "wired.com": "Wired",
    "theverge.com": "The Verge",
    "engadget.com": "Engadget",
    "dev.to": "DEV Community",
    "espncricinfo.com": "ESPNCricinfo",
    "cricbuzz.com": "Cricbuzz"
}

# Common thumbnail images for sources that don't provide images
DEFAULT_SOURCE_IMAGES = {
    "BBC News": "https://ichef.bbci.co.uk/news/1024/branded_news/83B3/production/_115651733_breaking-large-promo-nc.png",
    "The Guardian": "https://i.guim.co.uk/img/media/b73cc57cb1d40376957ef6ad5d3c284d5b00f0d2/0_0_2000_1200/master/2000.jpg?width=620&quality=85&auto=format&fit=max&s=b2cf56f189b3903ba09d875fbc46eea7",
    "Times of India": "https://static.toiimg.com/photo/imgsize-,msid-63612505/63612505.jpg",
    "The Hindu": "https://www.thehindu.com/theme/images/th-online/logo.png",
    "NDTV News": "https://cdn.ndtv.com/common/images/ogndtv.png",
    "India Today": "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202001/IT-770x433.jpeg?VersionId=nO6H7UrzMfJL8s9bzgolmVuEyw8tKZA6",
    "Android Authority": "https://www.androidauthority.com/wp-content/uploads/2022/07/Android-Authority-logo-3.jpg",
    "TechCrunch": "https://techcrunch.com/wp-content/uploads/2015/02/cropped-cropped-favicon-gradient.png",
    "default": "https://www.shutterstock.com/image-vector/live-breaking-news-template-business-600w-1897043905.jpg"
}

# News cache store
NEWS_CACHE = {}
CACHE_EXPIRY = 1800  # 30 minutes in seconds

@app.get("/api/py/helloFastApi")
def hello_fast_api():
    return {"message": "Hello from FastAPI powered by Gemini 1.5 Flash"}

# Get available news sources for a language
@app.get("/api/news/sources/{language}")
def get_news_sources(language: str):
    """Get list of available news sources for a specific language"""
    sources = []
    
    # Go through all categories and collect sources for the specified language
    for category, languages in RSS_FEEDS.items():
        if language in languages:
            for feed_url in languages[language]:
                domain = feed_url.split('/')[2]
                source_name = NEWS_SOURCE_NAMES.get(domain, domain)
                sources.append({
                    "name": source_name,
                    "url": feed_url,
                    "id": domain,
                    "category": category,
                    "image": DEFAULT_SOURCE_IMAGES.get(source_name, DEFAULT_SOURCE_IMAGES["default"])
                })
    
    if not sources:
        raise HTTPException(status_code=404, detail=f"Language {language} not supported")
    
    return {"sources": sources}

# Get available categories
@app.get("/api/news/categories")
def get_categories():
    """Get list of all available news categories"""
    return {"categories": list(RSS_FEEDS.keys())}

def extract_image_from_entry(entry):
    """Extract image URL from a feed entry if available"""
    # Try different places where images might be in RSS feeds
    try:
        # Check for media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('medium', '') == 'image':
                    return media.get('url')
        
        # Check for media:thumbnail
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0]['url']
        
        # Check for enclosures
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'image' in enclosure.type:
                    return enclosure.href
        
        # Try to find image in content
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value
            img_match = re.search(r'<img[^>]+src="([^">]+)"', content)
            if img_match:
                return img_match.group(1)
                
        # Try to find image in summary
        if hasattr(entry, 'summary'):
            img_match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
            if img_match:
                return img_match.group(1)
    except:
        pass
    
    return None

def fetch_rss_feed(feed_url, category=None, max_retries=2):
    """Fetch articles from a single RSS feed with retry logic"""
    for retry in range(max_retries):
        try:
            # Parse the feed with a short timeout
            feed = feedparser.parse(feed_url, timeout=3)
            
            # Check if feed has entries
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                print(f"Warning: No entries found in {feed_url}")
                return []
            
            # Get source name from feed or fallback to URL
            domain = feed_url.split('/')[2]
            source_name = NEWS_SOURCE_NAMES.get(domain, feed.feed.title if hasattr(feed.feed, 'title') else domain)
            source_image = DEFAULT_SOURCE_IMAGES.get(source_name, DEFAULT_SOURCE_IMAGES["default"])
            
            # Process each entry - increased from 10 to 20 entries per feed
            articles = []
            for entry in feed.entries[:20]:  # Process up to 20 articles per feed
                try:
                    # Extract and clean data - only basics for speed
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
                    
                    # Simple image extraction (skip complex extraction for performance)
                    image_url = None
                    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0]['url']
                    image_url = image_url or source_image
                    
                    # Create article object
                    article = {
                        "id": str(hash(title + source_name)),
                        "title": title,
                        "summary": summary,
                        "source": {"name": source_name, "url": feed_url},
                        "published_date": pub_date,
                        "link": entry.link if hasattr(entry, 'link') else "",
                        "image_url": image_url,
                        "category": category
                    }
                    articles.append(article)
                except Exception as e:
                    print(f"Error processing entry from {feed_url}: {e}")
                    continue
            
            return articles
        
        except Exception as e:
            if retry == max_retries - 1:
                print(f"Error fetching {feed_url} after {max_retries} retries: {e}")
                return []
            else:
                print(f"Retrying {feed_url} ({retry+2}/{max_retries})...")
                time.sleep(0.5)  # Reduced wait time between retries

async def fetch_news_api(query, language, category=None, fallback=True):
    """Fetch news from NewsAPI as a fallback"""
    if not NEWS_API_KEY or not fallback:
        return []
    
    try:
        # Map our language codes to NewsAPI codes
        lang_map = {
            "en": "en",
            "hi": "hi",
            "ta": "ta", 
            "te": "te",
            "gu": "gu",
            "mr": "mr"
        }
        lang = lang_map.get(language, "en")
        
        # Country code for India
        country = "in"
        
        # Add category to query if provided
        query_with_category = query
        if category:
            query_with_category = f"{query} {category}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # If there's a query, use the everything endpoint, otherwise top headlines
            if query:
                url = f"https://newsapi.org/v2/everything?q={query_with_category}&language={lang}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
            else:
                url = f"https://newsapi.org/v2/top-headlines?country={country}&language={lang}&apiKey={NEWS_API_KEY}"
                if category:
                    # Map our category to NewsAPI categories if possible
                    category_map = {
                        "Business & Economy": "business",
                        "Sports": "sports",
                        "Cricket": "sports",
                        "Football": "sports",
                        "Tech": "technology",
                        "Science": "science",
                        "Entertainment": "entertainment",
                        "Movies": "entertainment",
                        "Television": "entertainment",
                        "Health": "health"
                    }
                    api_category = category_map.get(category)
                    if api_category:
                        url += f"&category={api_category}"
            
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                
                if data["status"] != "ok" or not data.get("articles"):
                    return []
                
                articles = []
                for item in data["articles"]:
                    # Create article in our standard format
                    article = {
                        "id": str(hash(item["title"] + (item["source"]["name"] if item["source"] else "NewsAPI"))),
                        "title": item["title"] or "",
                        "summary": item["description"] or "",
                        "source": {
                            "name": item["source"]["name"] if item["source"] else "NewsAPI",
                            "url": "https://newsapi.org"
                        },
                        "published_date": item["publishedAt"] or datetime.now().isoformat(),
                        "link": item["url"] or "",
                        "image_url": item["urlToImage"] or DEFAULT_SOURCE_IMAGES["default"],
                        "category": category
                    }
                    articles.append(article)
                
                print(f"Fetched {len(articles)} articles from NewsAPI for {category if category else 'general'}")
                return articles
            else:
                print(f"NewsAPI error: {response.status_code} - {response.text}")
                return []
    except Exception as e:
        print(f"Error fetching from NewsAPI: {e}")
        return []

def fetch_all_feeds(feed_urls, category=None, max_workers=16):
    """Fetch articles from multiple RSS feeds concurrently with improved coverage and performance"""
    all_articles = []
    successful_feeds = 0
    start_time = time.time()
    
    # Increase the number of feeds to process for better coverage
    # Process up to 15 feeds (increased from 10) for comprehensive results
    limited_feeds = feed_urls[:min(15, len(feed_urls))]
    
    # Use ThreadPoolExecutor for parallel fetching with increased workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all feed fetching tasks
        future_to_url = {executor.submit(fetch_rss_feed, url, category): url for url in limited_feeds}
        
        # Process results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
                    successful_feeds += 1
                    # Only break if we have an extremely large number of articles to prevent overload
                    if len(all_articles) > 200:  # Increased from 100
                        print(f"Reached article threshold with {successful_feeds} feeds")
                        break
            except Exception as e:
                print(f"Error processing results from {url}: {e}")
    
    fetch_time = time.time() - start_time
    print(f"Successfully fetched from {successful_feeds}/{len(limited_feeds)} feeds in {fetch_time:.2f}s")
    print(f"Total raw articles collected: {len(all_articles)}")
    
    # Improved deduplication with faster title-based matching and source diversity
    unique_articles = {}
    source_counts = {}
    
    # First pass - identify duplicate titles and track source counts
    for article in all_articles:
        # Use normalized title as a deduplication key
        norm_title = re.sub(r'\W+', ' ', article["title"].lower()).strip()[:60]
        source_name = article["source"]["name"]
        
        # Track source counts for diversity
        if source_name not in source_counts:
            source_counts[source_name] = 0
        source_counts[source_name] += 1
        
        # Prefer articles with longer summaries when duplicates are found
        if norm_title in unique_articles:
            existing_len = len(unique_articles[norm_title]["summary"])
            current_len = len(article["summary"])
            
            # Replace if current article has a substantially longer summary
            if current_len > existing_len * 1.5:
                unique_articles[norm_title] = article
        else:
            unique_articles[norm_title] = article
    
    # Second pass - ensure source diversity 
    # If any source has more than 20% of articles, reduce its presence
    result_articles = []
    source_limit = max(5, int(len(unique_articles) * 0.2))  # 20% or at least 5
    source_added = {}
    
    # First add one article from each source to ensure representation
    for article in unique_articles.values():
        source_name = article["source"]["name"]
        if source_name not in source_added:
            result_articles.append(article)
            source_added[source_name] = 1
            
    # Then add remaining articles with source limits
    for article in unique_articles.values():
        source_name = article["source"]["name"]
        if article not in result_articles and source_added.get(source_name, 0) < source_limit:
            result_articles.append(article)
            source_added[source_name] = source_added.get(source_name, 0) + 1
    
    print(f"Unique articles after deduplication: {len(result_articles)} from {len(source_added)} sources")
    dedup_time = time.time() - start_time - fetch_time
    print(f"Deduplication took {dedup_time:.2f}s")
    
    return result_articles

async def determine_category_for_query(query):
    """Use Gemini to determine the best category for a query"""
    if not query:
        return None
    
    try:
        prompt = f"""Determine the most relevant category for this search query from the list below:
Query: "{query}"

Available categories:
{', '.join(RSS_FEEDS.keys())}

Return ONLY the single most relevant category name from the list.
"""
        response = model.generate_content(prompt)
        category = response.text.strip()
        
        # Validate the category
        if category in RSS_FEEDS:
            print(f"Gemini suggested category '{category}' for query '{query}'")
            return category
        else:
            print(f"Gemini suggested invalid category '{category}', defaulting to general search")
            return None
    except Exception as e:
        print(f"Error determining category with Gemini: {e}")
        return None

# Gemini 1.5 Flash inspired search enhancement
def advanced_semantic_search(articles, query, threshold=0.03):  # Lower threshold for more matches
    """
    Supercharged search function that intelligently balances speed with comprehensive results
    """
    if not query:
        return articles, 0
    
    start_time = time.time()
    
    # Normalize the query
    query_lower = query.lower()
    query_terms = set(query_lower.split())  # Using a set for faster lookups
    
    # Fast pre-filtering based on title match
    fast_matches = []
    remaining_articles = []
    
    for article in articles:
        title_lower = article["title"].lower()
        
        # Quick check if any query term is in the title - fast path
        if any(term in title_lower for term in query_terms):
            # Calculate how many query terms match and their position (earlier = better)
            matched_terms = sum(1 for term in query_terms if term in title_lower)
            earliest_pos = min((title_lower.find(term) for term in query_terms if term in title_lower), default=999)
            
            # Improved relevance scoring based on match quality
            relevance = 0.7 + (0.2 * (matched_terms / len(query_terms))) - (0.1 * (earliest_pos / 100))
            article["relevance"] = min(max(relevance, 0.1), 0.99)  # Keep between 0.1 and 0.99
            fast_matches.append(article)
        else:
            remaining_articles.append(article)
    
    # Check if we have enough fast matches (more than before)
    if len(fast_matches) >= 25:  # Increased from 20
        print(f"Fast path search found {len(fast_matches)} matches in {time.time() - start_time:.3f}s")
        fast_matches.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return fast_matches, len(fast_matches)
    
    # Otherwise proceed with more detailed matching
    scored_articles = []
    
    # Smart category detection for contextual search
    query_categories = {
        "sports": ["cricket", "football", "sport", "match", "ipl", "tournament", "player", "team", "game", 
                  "score", "coach", "athlete", "league", "championship", "win", "lose"],
        "tech": ["tech", "ai", "digital", "app", "mobile", "computer", "software", "hardware", "device", 
                "gadget", "smartphone", "internet", "web", "technology", "code", "programming"],
        "politics": ["election", "minister", "government", "party", "political", "parliament", "president", 
                    "vote", "campaign", "policy", "leader", "prime minister", "law"],
        "finance": ["market", "finance", "stock", "economy", "business", "money", "bank", "investor", 
                   "economic", "trade", "financial", "investment", "fund", "currency"],
        "entertainment": ["movie", "film", "actor", "actress", "director", "show", "music", "song", 
                         "celebrity", "tv", "cinema", "netflix", "entertainment", "album"],
        "science": ["research", "study", "scientist", "discovery", "science", "experiment", "space", 
                   "nasa", "planet", "species", "data", "findings"],
        "health": ["health", "covid", "vaccine", "doctor", "hospital", "disease", "medical", "treatment", 
                  "patient", "medicine", "cure", "symptom"]
    }
    
    # Find which categories the query might belong to
    detected_categories = []
    for category, terms in query_categories.items():
        if any(term in query_lower for term in terms):
            detected_categories.append(category)
    
    # Process each article with the enhanced algorithm
    for article in remaining_articles:
        title_lower = article["title"].lower()
        summary_lower = article["summary"].lower() if article.get("summary") else ""
        article_text = title_lower + " " + summary_lower
        
        # Quick scoring system
        score = 0.0
        
        # Title matches are important
        title_matches = sum(1 for term in query_terms if term in title_lower)
        if title_matches > 0:
            score += 0.4 * (title_matches / len(query_terms))
        
        # Content match
        summary_matches = sum(1 for term in query_terms if term in summary_lower)
        if summary_matches > 0:
            score += 0.3 * (summary_matches / len(query_terms))
            
        # Exact phrase match in either title or summary (strong signal)
        if query_lower in article_text:
            score += 0.5
            
        # Check for all words appearing in any order
        if all(term in article_text for term in query_terms):
            score += 0.3
            
        # Partial phrase matches (more comprehensive)
        words_in_query = query_lower.split()
        if len(words_in_query) > 1:
            # Check for adjacent word pairs
            for i in range(len(words_in_query) - 1):
                partial_phrase = " ".join(words_in_query[i:i+2])
                if partial_phrase in article_text:
                    score += 0.15
            
            # Check for triplets in longer queries
            if len(words_in_query) > 2:
                for i in range(len(words_in_query) - 2):
                    partial_phrase = " ".join(words_in_query[i:i+3])
                    if partial_phrase in article_text:
                        score += 0.2
        
        # Category match bonus - more sophisticated matching
        article_category = article.get("category", "").lower()
        
        # Map detected query categories to article categories
        category_mapping = {
            "sports": ["sports", "cricket", "football"],
            "tech": ["tech", "programming", "android", "apple", "ios development"],
            "politics": ["news", "world"],
            "finance": ["business & economy", "personal finance"],
            "entertainment": ["movies", "television", "music"],
            "science": ["science", "space"],
            "health": ["health"]
        }
        
        for detected in detected_categories:
            mapped_categories = category_mapping.get(detected, [])
            if article_category and any(mapped_cat.lower() in article_category for mapped_cat in mapped_categories):
                score += 0.25  # Increased from 0.2
        
        # Recency bonus (newer articles score slightly higher)
        try:
            pub_date = article.get("published_date", "")
            if pub_date:
                # Parse the date, assuming ISO format
                pub_datetime = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                age_in_days = (datetime.now() - pub_datetime).days
                # Small bonus for recent articles (up to 0.1)
                if age_in_days <= 7:  # Articles less than a week old
                    score += max(0.1 - (age_in_days * 0.01), 0)
        except Exception:
            pass  # Skip if date parsing fails
            
        # Improved threshold calculation - adaptive based on query length
        adaptive_threshold = threshold * (0.8 if len(query_terms) > 3 else 1.0)
            
        # Keep article if it meets threshold
        if score > adaptive_threshold:
            article["relevance"] = score
            scored_articles.append(article)
    
    # Combine results and sort
    combined_results = fast_matches + scored_articles
    combined_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    
    print(f"Full semantic search found {len(combined_results)} matches in {time.time() - start_time:.3f}s")
    
    return combined_results, len(combined_results)

def gemini_enhanced_search(articles, query):
    """
    Harness the power of Gemini 1.5 Flash for intelligent semantic understanding
    This function uses Gemini's embeddings for enhanced semantic search with real NLP capabilities
    """
    start_time = time.time()
    
    if not query:
        return articles, 0
        
    try:
        # Generate embedding for query using Gemini's text embedding capability
        query_embedding = model.embed_content(query).embedding
        
        # Process each article with semantic similarity
        scored_articles = []
        
        print(f"Computing semantic similarity for {len(articles)} articles...")
        
        # First try processing in small batches for efficiency (avoids rate limits)
        batch_size = 20  # Process in batches to balance speed and API usage
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            
            # Process each article in the batch
            for article in batch:
                try:
                    # Combine title and summary for better semantic matching
                    content = article["title"] + ". " + article["summary"]
                    
                    # Generate embedding for the article content
                    article_embedding = model.embed_content(content).embedding
                    
                    # Calculate cosine similarity between query and article
                    similarity = calculate_cosine_similarity(query_embedding, article_embedding)
                    
                    # Add semantic relevance score
                    article["relevance"] = float(similarity)  # Convert to float to ensure JSON serialization
                    scored_articles.append(article)
                    
                except Exception as e:
                    print(f"Error embedding article: {e}")
                    # Fall back to adding the article with a default score
                    article["relevance"] = 0.5
                    scored_articles.append(article)
        
        # Sort articles by relevance score (highest first)
        scored_articles.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        print(f"Gemini semantic search completed for {len(scored_articles)} articles in {time.time() - start_time:.3f}s")
        
        return scored_articles, len(scored_articles)
        
    except Exception as e:
        print(f"Error using Gemini for semantic search: {e}")
        # Fall back to advanced text-based search
        print("Falling back to traditional search algorithm...")
        return advanced_semantic_search(articles, query)
        
def calculate_cosine_similarity(vec1, vec2):
    """
    Calculate the cosine similarity between two vectors
    
    This measures the cosine of the angle between two vectors, providing a similarity score
    that's 1.0 for identical vectors and 0.0 for orthogonal vectors
    """
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Calculate magnitudes
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
        
    # Calculate cosine similarity
    return dot_product / (magnitude1 * magnitude2)

@app.post("/api/news", response_model=NewsResponse)
async def get_news(request: NewsRequest):
    try:
        start_time = time.time()
        language = request.language
        query = request.query
        page = request.page
        page_size = request.page_size
        preferred_sources = request.preferred_sources
        category = request.category
        
        print(f"Processing news request: lang={language}, query='{query}', category={category}, page={page}")
        
        # Skip category detection for empty queries to save time
        if not category and query and len(query) > 2:
            # Only use category detection for substantial queries
            category = await determine_category_for_query(query)
        
        # Check cache first - with a sophisticated cache key that includes more parameters
        cache_key = f"{language}-{category or 'all'}-{query[:30]}-{'-'.join(sorted(preferred_sources))}"
        current_time = time.time()
        
        # Fast path: Return cached results if available and not expired
        if cache_key in NEWS_CACHE and (current_time - NEWS_CACHE[cache_key]["timestamp"] < CACHE_EXPIRY):
            cached_data = NEWS_CACHE[cache_key]
            
            # Calculate pagination directly from cache
            total_matches = len(cached_data["articles"])
            total_pages = max(1, (total_matches + page_size - 1) // page_size)
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_matches)
            
            # Get requested page of articles
            paged_articles = cached_data["articles"][start_idx:end_idx]
            
            category_msg = f" in {category}" if category else ""
            message = f"Found {total_matches} articles matching '{query}'{category_msg}." if query else f"Showing {min(page_size, total_matches)} recent news articles{category_msg}."
            
            print(f"Returned cached results for '{query}' in {time.time() - start_time:.3f}s")
            
            return NewsResponse(
                articles=paged_articles,
                message=message,
                total_found=total_matches,
                total_pages=total_pages,
                current_page=page,
                available_sources=cached_data.get("available_sources", []),
                available_categories=list(RSS_FEEDS.keys())
            )
        
        # Not in cache, need to fetch new data
        articles = []
        fetch_start = time.time()
        
        # Parallel fetch strategy - fetch from multiple sources concurrently
        fetch_tasks = []
        
        # 1. Fetch category-specific articles if a category is specified
        if category and category in RSS_FEEDS:
            # Check if the language is supported for this category
            if language not in RSS_FEEDS[category]:
                # Try to fall back to English
                if "en" in RSS_FEEDS[category]:
                    language = "en"
                else:
                    return NewsResponse(
                        articles=[],
                        message=f"Language {request.language} not available for category '{category}'.",
                        total_found=0,
                        total_pages=0,
                        current_page=page,
                        available_sources=[],
                        available_categories=list(RSS_FEEDS.keys())
                    )
            
            # Get feeds for the specified category and language
            feeds = RSS_FEEDS[category][language]
            articles = fetch_all_feeds(feeds, category=category)
            
            # Check if we should also fetch from related categories for better coverage
            # Map of related categories to check
            related_categories = {
                "Sports": ["Cricket", "Football"],
                "News": ["Business & Economy"],
                "Programming": ["Web Development", "Tech"],
                "Movies": ["Television"],
                "Tech": ["Android", "Apple"]
            }
            
            # Fetch from related categories for broader coverage when relevant
            if category in related_categories and len(articles) < 50:
                for related_cat in related_categories[category]:
                    if related_cat in RSS_FEEDS and language in RSS_FEEDS[related_cat]:
                        related_feeds = RSS_FEEDS[related_cat][language]
                        print(f"Fetching additional articles from related category: {related_cat}")
                        related_articles = fetch_all_feeds(related_feeds, category=related_cat)
                        articles.extend(related_articles)
            
        else:
            # Get general news feeds for this language or fall back to English
            if language in RSS_FEEDS["News"]:
                feeds = RSS_FEEDS["News"][language]
            else:
                feeds = RSS_FEEDS["News"]["en"]
            
            articles = fetch_all_feeds(feeds, category="News")
        
        # Always try NewsAPI for search queries to get more comprehensive results
        # Extended to also fetch when we have too few articles
        news_api_articles = []
        if query or len(articles) < 30:
            news_api_articles = await fetch_news_api(query, language, category=category)
            if news_api_articles:
                print(f"Added {len(news_api_articles)} articles from NewsAPI")
                articles.extend(news_api_articles)
        
        print(f"Fetched {len(articles)} total articles in {time.time() - fetch_start:.3f}s")
        
        # Extract available sources for filtering
        available_sources = []
        source_set = set()
        for article in articles:
            source_name = article["source"]["name"]
            if source_name not in source_set:
                source_set.add(source_name)
                available_sources.append(source_name)
        
        # Apply source filtering if specified
        if preferred_sources and len(preferred_sources) > 0:
            filtered_by_source = [a for a in articles if any(
                ps.lower() in a["source"]["name"].lower() for ps in preferred_sources
            )]
            if filtered_by_source:
                print(f"Filtered by source: {len(filtered_by_source)} articles matched preferred sources")
                articles = filtered_by_source
        
        # Apply search filtering only if there's a query
        search_start = time.time()
        if query:
            try:
                # Try Gemini enhanced search first (with error handling)
                filtered_articles, total_matches = gemini_enhanced_search(articles, query)
                print(f"Gemini search found {total_matches} matches")
            except Exception as e:
                print(f"Gemini search failed: {e}, falling back to advanced search")
                # Fall back to our optimized search algorithm
                filtered_articles, total_matches = advanced_semantic_search(articles, query)
                print(f"Advanced search found {total_matches} matches")
            
            if not filtered_articles:
                filtered_articles = sorted(articles, key=lambda x: x.get("published_date", ""), reverse=True)
                total_matches = len(filtered_articles)
                category_msg = f" in {category}" if category else ""
                message = f"No exact matches for '{query}'{category_msg}. Showing recent articles instead."
            else:
                category_msg = f" in {category}" if category else ""
                message = f"Found {total_matches} articles matching '{query}'{category_msg}."
                
                # Enhanced relevance - boost certain items based on recency and quality
                for article in filtered_articles:
                    try:
                        # Boost high-quality sources slightly
                        quality_sources = ["BBC News", "The Guardian", "The Hindu", "Times of India", "NDTV News"]
                        if article["source"]["name"] in quality_sources:
                            article["relevance"] = min(article.get("relevance", 0.5) * 1.1, 0.99)
                        
                        # Boost recent articles
                        pub_date = article.get("published_date", "")
                        if pub_date:
                            # Parse the date
                            pub_datetime = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                            hours_old = (datetime.now() - pub_datetime).total_seconds() / 3600
                            if hours_old < 24:  # Less than a day old
                                article["relevance"] = min(article.get("relevance", 0.5) * 1.1, 0.99)
                    except Exception:
                        pass  # Ignore errors in relevance enhancement
        else:
            # No query, just sort by date
            filtered_articles = sorted(articles, key=lambda x: x.get("published_date", ""), reverse=True)
            total_matches = len(filtered_articles)
            category_msg = f" in {category}" if category else ""
            message = f"Showing {min(page_size, total_matches)} recent news articles{category_msg}."
        
        print(f"Search completed in {time.time() - search_start:.3f}s")
        
        # Store in cache for future requests - include available_sources
        NEWS_CACHE[cache_key] = {
            "timestamp": current_time,
            "articles": filtered_articles,
            "available_sources": available_sources
        }
        
        # Clean cache if it's getting too large (over 50 entries)
        if len(NEWS_CACHE) > 50:
            oldest_keys = sorted(NEWS_CACHE.keys(), key=lambda k: NEWS_CACHE[k]["timestamp"])[:10]
            for old_key in oldest_keys:
                del NEWS_CACHE[old_key]
            print(f"Cleaned {len(oldest_keys)} old entries from cache")
        
        # Final pagination
        total_pages = max(1, (total_matches + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_matches)
        
        # Get requested page of articles
        paged_articles = filtered_articles[start_idx:end_idx]
        
        # Ensure all articles have a relevance score for UI
        for article in paged_articles:
            if "relevance" not in article:
                article["relevance"] = 0.5
                
        total_time = time.time() - start_time
        print(f"Request completed in {total_time:.3f}s, returning {len(paged_articles)} articles")
        
        return NewsResponse(
            articles=paged_articles,
            message=message,
            total_found=total_matches,
            total_pages=total_pages,
            current_page=page,
            available_sources=available_sources,
            available_categories=list(RSS_FEEDS.keys())
        )
    
    except Exception as e:
        print(f"Error in get_news: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing news: {str(e)}")