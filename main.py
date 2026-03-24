import os
import json
import feedparser
import requests
from groq import Groq

# إعدادات الـ APIs
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_links.json"

# وظيفة لقراءة الروابط القديمة
def load_posted_links():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

# وظيفة لحفظ الرابط الجديد
def save_posted_link(link):
    links = load_posted_links()
    links.append(link)
    # نحتفظ بآخر 50 رابط بس عشان الملف ميكبرش أوي
    with open(DB_FILE, "w") as f:
        json.dump(links[-50:], f)

def get_new_tech_news():
    feed_url = "https://techcrunch.com/feed/"
    feed = feedparser.parse(feed_url)
    posted_links = load_posted_links()
    
    for entry in feed.entries:
        if entry.link not in posted_links:
            return {"title": entry.title, "link": entry.link}
    return None

def ai_rephrase(news_data):
    prompt = f"Create a viral tech post for Facebook about: {news_data['title']}. Link: {news_data['link']}. Use emojis and hashtags #TrendTech #AI."
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    return completion.choices[0].message.content

def post_to_fb(content):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    payload = {'message': content, 'access_token': FB_PAGE_ACCESS_TOKEN}
    return requests.post(url, data=payload).json()

# التشغيل الأساسي
print("Looking for fresh news...")
news = get_new_tech_news()

if news:
    print(f"New news found: {news['title']}")
    refined_post = ai_rephrase(news)
    result = post_to_fb(refined_post)
    
    if "id" in result:
        print("Success! Saving link...")
        save_posted_link(news['link'])
    else:
        print(f"Error posting: {result}")
else:
    print("No new news to post right now.")
