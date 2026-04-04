import os
import json
import feedparser
import requests
from groq import Groq
from datetime import datetime, timezone
import time

# إعدادات الـ APIs
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
GROQ_MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_links.json"

FEEDS = [
    {"name": "Family TV", "url": "https://familytvr.blogspot.com/feeds/posts/default?alt=rss", "type": "blog"},
    {"name": "Quickcomicx Dailymotion", "url": "https://www.dailymotion.com/rss/user/Quickcomicx/1", "type": "video"}
]

def load_posted_links():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def save_posted_link(link):
    links = load_posted_links()
    links.append(link)
    with open(DB_FILE, "w") as f:
        json.dump(links[-200:], f)

def get_content_to_post():
    posted_links = load_posted_links()
    
    for feed in FEEDS:
        print(f"Checking {feed['name']}...")
        parsed = feedparser.parse(feed['url'])
        
        if not parsed.entries:
            continue

        for entry in parsed.entries:
            # استخراج وقت النشر من الريس (RSS)
            # معظم الروابط تستخدم published_parsed أو updated_parsed
            published_time = entry.get('published_parsed') or entry.get('updated_parsed')
            
            if published_time:
                # تحويل وقت المنشور إلى توقيت جهازك للمقارنة
                post_date = datetime.fromtimestamp(time.mktime(published_time), tz=timezone.utc)
                now = datetime.now(timezone.utc)
                diff = now - post_date
                
                # إذا كان الرابط لم ينشر من قبل
                if entry.link not in posted_links:
                    print(f"Found new content: {entry.title}")
                    return {"title": entry.title, "link": entry.link, "type": feed['type'], "source": feed['name']}
                
    return None

def ai_rephrase(data):
    prompt = f"Write a viral Facebook post for Trend Tech. Content: {data['title']}. Link: {data['link']}. Source: {data['source']}. Use emojis."
    completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=GROQ_MODEL)
    return completion.choices[0].message.content

def post_to_fb(text):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    return requests.post(url, data={'message': text, 'access_token': FB_PAGE_ACCESS_TOKEN}).json()

if __name__ == "__main__":
    content = get_content_to_post()
    
    if content:
        # إذا وجدنا شيء لم ينشر، ننشره فوراً في منشور منفصل
        print(f"Post detected from {content['source']}")
        post_text = ai_rephrase(content)
        res = post_to_fb(post_text)
        
        if "id" in res:
            save_posted_link(content['link'])
            print("Successfully posted to Facebook.")
    else:
        print("No new content found in the last check.")
