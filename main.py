import os
import feedparser
import requests
from groq import Groq

# إعدادات الـ APIs من الـ Secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_latest_tech_news():
    # رابط RSS لموقع TechCrunch (تقدر تضيف غيره)
    feed_url = "https://techcrunch.com/feed/"
    feed = feedparser.parse(feed_url)
    
    if feed.entries:
        latest_entry = feed.entries[0]
        return {
            "title": latest_entry.title,
            "link": latest_entry.link,
            "summary": latest_entry.summary
        }
    return None

def ai_rephrase_news(news_data):
    prompt = f"""
    You are the admin of 'Trend Tech' Facebook page. 
    Rephrase this tech news into a viral, engaging Facebook post in English.
    News Title: {news_data['title']}
    News Link: {news_data['link']}
    
    Requirements:
    - Use catchy hooks.
    - Use tech emojis.
    - Include hashtags like #TrendTech #AI #TechNews.
    - Keep it concise and professional yet exciting.
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )
    return completion.choices[0].message.content

def post_to_fb(content):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    payload = {'message': content, 'access_token': FB_PAGE_ACCESS_TOKEN}
    r = requests.post(url, data=payload)
    return r.json()

# تشغيل الدورة كاملة
print("Checking for news...")
news = get_latest_tech_news()
if news:
    print(f"Found news: {news['title']}")
    refined_post = ai_rephrase_news(news)
    print("Posting to Facebook...")
    result = post_to_fb(refined_post)
    print(f"Facebook Result: {result}")
