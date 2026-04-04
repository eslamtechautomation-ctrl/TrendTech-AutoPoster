import os
import json
import feedparser
import requests
import time
from groq import Groq
from datetime import datetime, timezone
from atproto import Client

# الإعدادات
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

# بيانات باسكاي (3 حسابات)
BS_ACCOUNTS = [
    {"user": os.environ.get("BS_USER_1"), "pass": os.environ.get("BS_PASS_1")},
    {"user": os.environ.get("BS_USER_2"), "pass": os.environ.get("BS_PASS_2")},
    {"user": os.environ.get("BS_USER_3"), "pass": os.environ.get("BS_PASS_3")}
]

def load_posted():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def post_to_bs(text, user, password):
    if not user or not password: return
    try:
        bs_client = Client()
        bs_client.login(user, password)
        bs_client.send_post(text)
        print(f"✅ Success Bluesky: {user}")
    except Exception as e: print(f"❌ BS Error: {e}")

def post_to_fb(text):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    return requests.post(url, data={'message': text, 'access_token': FB_PAGE_ACCESS_TOKEN}).json()

if __name__ == "__main__":
    posted_links = load_posted()
    
    for feed in FEEDS:
        parsed = feedparser.parse(feed['url'])
        for entry in parsed.entries:
            if entry.link not in posted_links:
                # صياغة المنشور
                prompt = f"Write a viral post for Trend Tech. Title: {entry.title}. Link: {entry.link}. Type: {feed['type']}. Use emojis."
                ai_res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=GROQ_MODEL)
                post_text = ai_res.choices[0].message.content

                # النشر على فيسبوك
                post_to_fb(post_text)

                # النشر على 3 حسابات باسكاي
                for acc in BS_ACCOUNTS:
                    post_to_bs(post_text, acc['user'], acc['pass'])

                # حفظ الرابط
                posted_links.append(entry.link)
                with open(DB_FILE, "w") as f: json.dump(posted_links[-200:], f)
                
                # نشر منشور واحد من كل مصدر في المرة الواحدة
                break
