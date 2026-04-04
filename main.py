import os
import json
import feedparser
import requests
import time
from groq import Groq
from datetime import datetime, timezone
from atproto import Client

# 1. إعدادات الـ APIs (تُسحب من GitHub Secrets)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_links.json"

# 2. المصادر (المدونة وقناة ديلي موشن)
FEEDS = [
    {"name": "Family TV", "url": "https://familytvr.blogspot.com/feeds/posts/default?alt=rss", "type": "blog"},
    {"name": "Quickcomicx Dailymotion", "url": "https://www.dailymotion.com/rss/user/Quickcomicx/1", "type": "video"}
]

# 3. إعدادات حسابات Bluesky الثلاثة
BS_ACCOUNTS = [
    {"user": os.environ.get("BS_USER_1"), "pass": os.environ.get("BS_PASS_1")},
    {"user": os.environ.get("BS_USER_2"), "pass": os.environ.get("BS_PASS_2")},
    {"user": os.environ.get("BS_USER_3"), "pass": os.environ.get("BS_PASS_3")}
]

def load_posted():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def post_to_bs(text, user, password):
    if not user or not password:
        return
    try:
        bs_client = Client()
        bs_client.login(user, password)
        bs_client.send_post(text)
        print(f"✅ تم النشر بنجاح على حساب باسكاي: {user}")
    except Exception as e:
        print(f"❌ خطأ في النشر لحساب {user}: {e}")

def ai_rephrase(data):
    # برومبت مخصص لإنشاء منشور احترافي بالعربي
    prompt = f"اكتب منشوراً ترويجياً جذاباً لموقع Trend Tech حول هذا المحتوى: {data['title']}. الرابط: {data['link']}. النوع: {data['type']}. استخدم إيموجي تقنية وهاشتاجات مناسبة."
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ خطأ في الذكاء الاصطناعي: {e}")
        return f"جديدنا من Trend Tech: {data['title']} \n {data['link']}"

if __name__ == "__main__":
    posted_links = load_posted()
    new_content_posted = False

    for feed in FEEDS:
        print(f"🔍 فحص التحديثات في: {feed['name']}...")
        parsed = feedparser.parse(feed['url'])
        
        # ترتيب المدخلات من الأقدم للأحدث لنشر الأحدث دائماً
        entries = parsed.entries[::-1] 

        for entry in entries:
            if entry.link not in posted_links:
                print(f"✨ تم العثور على محتوى جديد من {feed['name']}: {entry.title}")
                
                # صياغة المنشور
                post_text = ai_rephrase({
                    "title": entry.title,
                    "link": entry.link,
                    "type": feed['type']
                })

                # النشر على الحسابات الثلاثة
                for acc in BS_ACCOUNTS:
                    post_to_bs(post_text, acc['user'], acc['pass'])

                # إضافة الرابط لقاعدة البيانات لمنع التكرار
                posted_links.append(entry.link)
                new_content_posted = True
                
                # التوقف بعد نشر منشور واحد من هذا المصدر لضمان الفصل بين المنشورات
                break 

    # تحديث ملف الروابط المنشورة
    if new_content_posted:
        with open(DB_FILE, "w") as f:
            json.dump(posted_links[-200:], f) # الاحتفاظ بآخر 200 رابط فقط
    else:
        print("☕ لا يوجد محتوى جديد للنشر في هذه الدورة.")
