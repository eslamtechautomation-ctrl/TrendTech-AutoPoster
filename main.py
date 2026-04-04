import os
import json
import feedparser
import requests
import time
from groq import Groq
from datetime import datetime, timezone
from atproto import Client # مكتبة بلو سكاي

# إعدادات الـ APIs (تأكد من إضافتها في GitHub Secrets)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
GROQ_MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_links.json"

# المصادر
FEEDS = [
    {"name": "Family TV", "url": "https://familytvr.blogspot.com/feeds/posts/default?alt=rss", "type": "blog"},
    {"name": "Quickcomicx Dailymotion", "url": "https://www.dailymotion.com/rss/user/Quickcomicx/1", "type": "video"}
]

# بيانات حسابات Bluesky الثلاثة (تأكد من استخدام App Passwords)
BS_ACCOUNTS = [
    {"user": os.environ.get("BS_USER_1"), "pass": os.environ.get("BS_PASS_1")},
    {"user": os.environ.get("BS_USER_2"), "pass": os.environ.get("BS_PASS_2")},
    {"user": os.environ.get("BS_USER_3"), "pass": os.environ.get("BS_PASS_3")}
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

def post_to_bluesky(text, user, password):
    if not user or not password: return
    try:
        bs_client = Client()
        bs_client.login(user, password)
        bs_client.send_post(text)
        print(f"✅ Posted to Bluesky: {user}")
    except Exception as e:
        print(f"❌ Error on Bluesky ({user}): {e}")

def post_to_facebook(text):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    res = requests.post(url, data={'message': text, 'access_token': FB_PAGE_ACCESS_TOKEN})
    return res.json()

def ai_rephrase(data):
    prompt = f"Write a viral post for Trend Tech. Content: {data['title']}. Link: {data['link']}. Type: {data['type']}. Use emojis."
    completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=GROQ_MODEL)
    return completion.choices[0].message.content

if __name__ == "__main__":
    posted_links = load_posted_links()
    
    for feed in FEEDS:
        print(f"🔍 Checking {feed['name']}...")
        parsed = feedparser.parse(feed['url'])
        
        for entry in parsed.entries:
            if entry.link not in posted_links:
                # بمجرد إيجاد محتوى جديد من أي مصدر (مدونة أو ديلي موشن)
                print(f"✨ New content found: {entry.title}")
                
                # صياغة المنشور بالذكاء الاصطناعي
                post_text = ai_rephrase({"title": entry.title, "link": entry.link, "type": feed['type'], "source": feed['name']})
                
                # 1. النشر على فيسبوك
                fb_res = post_to_facebook(post_text)
                
                # 2. النشر على حسابات Bluesky الثلاثة
                for acc in BS_ACCOUNTS:
                    post_to_bluesky(post_text, acc['user'], acc['pass'])
                
                # حفظ الرابط لعدم تكراره
                save_posted_link(entry.link)
                
                # الخروج من اللوب للنشر في "منشور منفصل" لكل دورة (أو حذف break للنشر دفعة واحدة)
                break 

    print("🚀 Cycle finished.")
