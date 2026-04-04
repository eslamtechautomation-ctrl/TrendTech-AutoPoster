import os
import json
import feedparser
from groq import Groq
from atproto import Client # مكتبة باسكاي

# إعدادات الـ APIs
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_links.json"

# المصادر (المدونة وديلي موشن)
FEEDS = [
    {"name": "Family TV", "url": "https://familytvr.blogspot.com/feeds/posts/default?alt=rss", "type": "blog"},
    {"name": "Quickcomicx Dailymotion", "url": "https://www.dailymotion.com/rss/user/Quickcomicx/1", "type": "video"}
]

# حسابات باسكاي (تأكد من إضافة اليوزر والباسوورد في الـ Secrets)
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
        print(f"✅ Success on Bluesky: {user}")
    except Exception as e:
        print(f"❌ Error on {user}: {e}")

if __name__ == "__main__":
    posted_links = load_posted()
    
    for feed in FEEDS:
        print(f"🔍 Checking: {feed['name']}")
        parsed = feedparser.parse(feed['url'])
        
        for entry in parsed.entries:
            if entry.link not in posted_links:
                print(f"✨ New post found: {entry.title}")
                
                # صياغة المنشور بالذكاء الاصطناعي
                prompt = f"Create a viral social media post in Arabic for: {entry.title}. Link: {entry.link}. Use tech emojis."
                ai_res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=GROQ_MODEL)
                post_text = ai_res.choices[0].message.content

                # النشر على حسابات باسكاي التلاتة
                for acc in BS_ACCOUNTS:
                    post_to_bs(post_text, acc['user'], acc['pass'])

                # حفظ الرابط
                posted_links.append(entry.link)
                with open(DB_FILE, "w") as f:
                    json.dump(posted_links[-200:], f)
                
                break # نشر بوست واحد جديد من كل مصدر
