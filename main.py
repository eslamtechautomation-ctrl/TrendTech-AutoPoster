import os
import json
import feedparser
import requests
from groq import Groq

# إعدادات الـ APIs من الـ Secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

# تعريف الموديل الصحيح لـ Groq

GROQ_MODEL = "llama-3.3-70b-versatile"
client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_links.json"

def load_posted_links():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_posted_link(link):
    links = load_posted_links()
    links.append(link)
    with open(DB_FILE, "w") as f:
        json.dump(links[-50:], f) # بنحفظ آخر 50 خبر بس

def get_new_tech_news():
    feed_url = "https://techcrunch.com/feed/"
    feed = feedparser.parse(feed_url)
    posted_links = load_posted_links()
    
    for entry in feed.entries:
        if entry.link not in posted_links:
            return {"title": entry.title, "link": entry.link}
    return None

def ai_rephrase(news_data):
    prompt = f"""
    You are the admin of 'Trend Tech' Facebook page. 
    Rephrase this tech news into a viral, engaging Facebook post in English.
    News Title: {news_data['title']}
    News Link: {news_data['link']}
    
    Requirements:
    - Use catchy hooks.
    - Use tech emojis.
    - Include hashtags like #TrendTech #AI #TechNews.
    - Keep it concise.
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

# التشغيل الأساسي
if __name__ == "__main__":
    print("Checking for fresh news...")
    news = get_new_tech_news()

    if news:
        print(f"New news found: {news['title']}")
        refined_post = ai_rephrase(news)
        result = post_to_fb(refined_post)
        
        if "id" in result:
            print("Success! Saving link...")
            save_posted_link(news['link'])
        else:
            print(f"Error posting to FB: {result}")
    else:
        print("No new news found to post.")
