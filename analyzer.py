import feedparser
import json
import os
import datetime
from dateutil import parser
from openai import OpenAI
import pandas as pd
from jinja2 import Template

# --- تنظیمات سرویس اختصاصی تو ---
BASE_URL = "https://ai.liara.ir/api/698d02e7fa009fae9b12b7dd/v1"
MODEL_NAME = "google/gemini-3-pro-preview"
# توصیه اکید: کلید را از Environment Variable بخوان
API_KEY = os.environ.get("LIARA_AI_API_KEY") 

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"

# پرامپت مهندسی معکوس روایت (Expert Persona)
SYSTEM_PROMPT = """
You are an expert media strategist and counter-propaganda analyst. 
Analyze the Title and Description of the provided YouTube video metadata.
Your goal is to deconstruct the narrative control attempt.

Output a valid JSON object with these exact keys:
1. "core_message": The overt message.
2. "narrative_framing": The psychological/emotional frame (e.g. desperation, impending doom, manufactured hope).
3. "hidden_intent": Why was this content produced now? What is the desired behavior/shift in public opinion?
4. "counter_narrative": A sharp, strategic advice for an influencer to neutralize this specific narrative.
"""

def get_ai_analysis(title, description):
    if not API_KEY:
        return {"error": "API Key is missing in environment variables."}
    
    # مقداردهی کلاینت با تنظیمات لیارا
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    
    prompt = f"Title: {title}\nDescription: {description}"
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} # جیمینای معمولاً از این فرمت پشتیبانی می‌کند
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return {"error": "Failed to analyze"}

def process_workflow():
    # ۱. خواندن داده‌های قبلی
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    else:
        all_data = []

    existing_ids = {item['video_id'] for item in all_data}
    
    # ۲. فچ کردن فید جدید
    feed = feedparser.parse(RSS_URL)
    new_entries_count = 0

    for entry in feed.entries:
        if entry.yt_videoid not in existing_ids:
            print(f"Analyzing new video: {entry.title}")
            
            title = entry.title
            desc = entry.media_group[0]['media_description']
            
            # تحلیل هوشمند
            analysis = get_ai_analysis(title, desc)
            
            video_record = {
                "video_id": entry.yt_videoid,
                "title": title,
                "link": entry.link,
                "published_at": parser.parse(entry.published).isoformat(),
                "thumbnail": entry.media_group[0]['media_thumbnail'][0]['url'],
                "analysis": analysis,
                "fetched_at": datetime.datetime.now().isoformat()
            }
            all_data.insert(0, video_record) # جدیدترین‌ها در ابتدا
            new_entries_count += 1

    # ۳. ذخیره‌سازی داده‌ها
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    return all_data

# --- در اینجا متد generate_html (که در پاسخ قبلی دادم) قرار می‌گیرد ---
# (برای جلوگیری از طولانی شدن، فرض می‌کنیم همان منطق Jinja2 را اجرا می‌کند)

if __name__ == "__main__":
    final_data = process_workflow()
    # در اینجا تابع تولید HTML را فراخوانی کنید
