import os
from groq import Groq
import requests

# 1. إعداد Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_post(topic):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Write a viral Facebook post about {topic} in English. Keep it short, include emojis and tech hashtags.",
            }
        ],
        model="llama3-8b-8192", # موديل سريع وممتاز للبوستات
    )
    return chat_completion.choices[0].message.content

# 2. وظيفة النشر على فيسبوك
def post_to_facebook(message):
    page_id = os.environ.get("FB_PAGE_ID")
    access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v20.0/{page_id}/feed"
    payload = {'message': message, 'access_token': access_token}
    response = requests.post(url, data=payload)
    return response.json()

# تجربة التشغيل
test_topic = "Artificial Intelligence in 2026"
print("Generating post via Groq...")
ai_message = generate_post(test_topic)
print(f"Post Content: {ai_message}")

print("Posting to Facebook...")
result = post_to_facebook(ai_message)
print(f"Result: {result}")
