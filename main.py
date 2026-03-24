import os
import json
import feedparser
import requests
from groq import Groq

# إعدادات الـ APIs
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

# الموديل المستقر
GROQ_MODEL = "llama-3.3-70b-versatile" 

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_links.json"

# قائمة المصادر الخاصة بك
FEEDS = [
    {"name": "Family TV", "url": "https://familytvr.blogspot.com/feeds/posts/default?alt=rss"}
   
   
]

def load_posted_links():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                content = f.read()
                return json.loads(content) if content else []
        except: return []
    return []

def save_posted_link(link):
    links = load_posted_links()
    links.append(link)
    with open(DB_FILE, "w") as f:
        json.dump(links[-100:], f)

def get_new_news():
    posted_links = load_posted_links()
    for feed in FEEDS:
        print(f"Checking: {feed['name']}")
        parsed_feed = feedparser.parse(feed['url'])
        for entry in parsed_feed.entries:
            if entry.link not in posted_links:
                return {"title": entry.title, "link": entry.link, "source": feed['name']}
    return None

def ai_rephrase(news_data):
    # برومبت ذكي يغير طريقة الكتابة حسب المصدر
    prompt = f"""
    You are the admin of 'Trend Tech' Facebook page. 
    Write a viral and engaging Facebook post in English for this news.
    Source: {news_data['source']}
    Title: {news_data['title']}
    Link: {news_data['link']}
    
    Guidelines:
    - If source is 'Family TV', talk about streaming and apps.
    - If source is 'Luxury Estate', talk about modern lifestyle and tech in homes.
    - If source is 'Tech News', talk about global tech trends.
    - Use emojis, catchy hooks, and hashtags like #TrendTech #Innovation.
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=GROQ_MODEL,
    )
    return completion.choices[0].message.content

def post_to_fb(content):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    payload = {'message': content, 'access_token': FB_PAGE_ACCESS_TOKEN}
    return requests.post(url, data=payload).json()

if __name__ == "__main__":
    news = get_new_news()
    if news:
        print(f"Found new content from {news['source']}: {news['title']}")
        refined_post = ai_rephrase(news)
        result = post_to_fb(refined_post)
        if "id" in result:
            print("Post success!")
            save_posted_link(news['link'])
        else:
            print(f"FB Error: {result}")
    else:
        print("Everything is up to date.")
