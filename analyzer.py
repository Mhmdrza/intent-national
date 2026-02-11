import feedparser
import json
import os
import datetime
from dateutil import parser
from openai import OpenAI
import pandas as pd
from jinja2 import Template

# --- تنظیمات اختصاصی Liara AI ---
BASE_URL = "https://ai.liara.ir/api/698d02e7fa009fae9b12b7dd/v1"
MODEL_NAME = "google/gemini-3-pro-preview"
API_KEY = os.environ.get("LIARA_AI_API_KEY") 

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"

SYSTEM_PROMPT = """
You are a senior psychological operations (PSYOP) analyst. Analyze the following media metadata.
Identify the hidden narrative control attempt.
Provide a JSON response with:
- "core_message": The surface story.
- "framing": How they want the audience to feel.
- "hidden_intent": The real strategic goal (reverse-engineered).
- "counter_narrative": Strategic advice for a counter-media influencer to flip the narrative.
"""

def get_ai_analysis(title, description):
    if not API_KEY: return {"error": "Missing API Key"}
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Title: {title}\nDesc: {description}"}
            ]
        )
        # برخی مدل‌ها مستقیما JSON نمی‌دهند، تلاش برای پاکسازی:
        content = completion.choices[0].message.content
        return json.loads(content[content.find('{'):content.rfind('}')+1])
    except:
        return {"error": "Analysis failed"}

def main():
    # بارگذاری داده‌های قدیمی
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = []

    existing_ids = {item['video_id'] for item in db}
    feed = feedparser.parse(RSS_URL)
    
    new_items = []
    for entry in feed.entries:
        if entry.yt_videoid not in existing_ids:
            print(f"Analyzing: {entry.title}")
            desc = entry.media_group[0]['media_description']
            analysis = get_ai_analysis(entry.title, desc)
            
            item = {
                "video_id": entry.yt_videoid,
                "title": entry.title,
                "link": entry.link,
                "published_at": parser.parse(entry.published).isoformat(),
                "thumbnail": entry.media_group[0]['media_thumbnail'][0]['url'],
                "analysis": analysis
            }
            new_items.append(item)

    # ادغام و ذخیره
    updated_db = new_items + db
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_db, f, ensure_ascii=False, indent=2)

    # تولید HTML (ساده شده)
    df = pd.DataFrame(updated_db)
    df['published_at'] = pd.to_datetime(df['published_at'])
    recent = df.head(10).to_dict(orient='records')
    
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(f"""
        <html dir="rtl" lang="fa">
        <head><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
        <body class="bg-light">
            <div class="container py-5">
                <h1 class="text-center mb-5">دیده‎‌بان هوشمند روایت رسانه</h1>
                {" ".join([f'''
                    <div class="card mb-3 shadow-sm">
                        <div class="card-body">
                            <h5 class="text-primary">{i['title']}</h5>
                            <div class="bg-dark text-white p-3 rounded">
                                <b>نیت پنهان:</b> {i['analysis'].get('hidden_intent', 'N/A')}<br>
                                <b class="text-warning">پاتک پیشنهادی:</b> {i['analysis'].get('counter_narrative', 'N/A')}
                            </div>
                        </div>
                    </div>
                ''' for i in recent])}
            </div>
        </body>
        </html>
        """)

if __name__ == "__main__":
    main()
