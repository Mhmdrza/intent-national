import feedparser
import json
import os
import datetime
from dateutil import parser
from openai import OpenAI
import pandas as pd
from jinja2 import Template
import sys

# --- تنظیمات اختصاصی ---
BASE_URL = "https://ai.liara.ir/api/698d02e7fa009fae9b12b7dd/v1"
MODEL_NAME = "google/gemini-3-pro-preview"
API_KEY = os.environ.get("LIARA_AI_API_KEY") 

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"

# محدودیت برای بار اول (برای جلوگیری از طولانی شدن بیش از حد)
MAX_NEW_VIDEOS_PER_RUN = 5 

def get_ai_analysis(title, description):
    if not API_KEY: return {"error": "No API Key"}
    
    # تنظیم Timeout برای جلوگیری از گیر کردن ابدی
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=30.0)
    
    prompt = f"Analyze media narrative.\nTitle: {title}\nDesc: {description}"
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a media analyst. Return ONLY JSON with keys: core_message, framing, hidden_intent, expected_effect, counter_narrative_strategy."},
                {"role": "user", "content": prompt}
            ]
        )
        content = completion.choices[0].message.content
        json_str = content[content.find('{'):content.rfind('}')+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"   ⚠️ AI Error: {e}")
        return {"error": "Analysis timed out or failed"}

def main():
    print(f"🚀 Starting Engine at {datetime.datetime.now()}")
    
    if not API_KEY:
        print("❌ ERROR: LIARA_AI_API_KEY is not set!")
        sys.exit(1)

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = []

    existing_ids = {item['video_id'] for item in db}
    
    print(f"📡 Fetching RSS Feed from YouTube...")
    feed = feedparser.parse(RSS_URL)
    print(f"✅ Found {len(feed.entries)} total videos in feed.")

    new_entries = []
    processed_count = 0

    for entry in feed.entries:
        v_id = getattr(entry, 'yt_videoid', None)
        if not v_id or v_id in existing_ids:
            continue

        if processed_count >= MAX_NEW_VIDEOS_PER_RUN:
            print(f"⏳ Limit reached ({MAX_NEW_VIDEOS_PER_RUN}). Skipping remaining new videos for next run.")
            break

        print(f"🔍 Analyzing ({processed_count + 1}/{MAX_NEW_VIDEOS_PER_RUN}): {entry.title[:50]}...")
        
        desc = ""
        if hasattr(entry, 'media_group'):
            desc = entry.media_group[0].get('media_description', '')
        
        # فراخوانی AI
        analysis = get_ai_analysis(entry.title, desc)
        
        item = {
            "video_id": v_id,
            "title": entry.title,
            "link": entry.link,
            "published_at": parser.parse(entry.published).isoformat(),
            "thumbnail": entry.media_group[0]['media_thumbnail'][0]['url'] if hasattr(entry, 'media_group') else "",
            "description": desc,
            "analysis": analysis,
            "fetched_at": datetime.datetime.now().isoformat()
        }
        new_entries.append(item)
        processed_count += 1

    if new_entries:
        print(f"💾 Saving {len(new_entries)} new analyses to database...")
        updated_db = new_entries + db
        os.makedirs("data", exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_db, f, ensure_ascii=False, indent=2)
    else:
        print("RSS فید ویدیوی جدیدی نداشت.")
        updated_db = db

    print("🎨 Generating HTML Dashboard...")
    generate_html(updated_db)
    print("✨ All tasks completed successfully!")

def generate_html(data):
    if not data:
        with open(HTML_OUTPUT, "w") as f: f.write("<h1>No Data Yet</h1>")
        return

    df = pd.DataFrame(data)
    df['published_at'] = pd.to_datetime(df['published_at'])
    now = pd.Timestamp.now(tz='UTC')
    
    # نمایش ۱۰ مورد آخر در بخش اصلی
    recent = df.sort_values('published_at', ascending=False).head(10).to_dict(orient='records')
    
    template_str = """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>دیده‎‌بان روایت</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; font-family: sans-serif; }
            .analysis-box { border-right: 4px solid #007bff; background: #fff; margin-bottom: 20px; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .intent { color: #d9534f; font-weight: bold; }
            .counter { color: #5cb85c; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <h1 class="text-center mb-5">🕵️ تحلیل هوشمند روایت‌های رسانه‌ای</h1>
            {% for item in recent %}
            <div class="analysis-box">
                <h4><a href="{{ item.link }}" target="_blank" style="text-decoration:none;">{{ item.title }}</a></h4>
                <hr>
                <div class="row">
                    <div class="col-md-6">
                        <p class="intent">🎯 نیت پنهان:</p>
                        <p>{{ item.analysis.hidden_intent or 'تحلیل ناموفق' }}</p>
                    </div>
                    <div class="col-md-6">
                        <p class="counter">💡 پاتک رسانه‌ای:</p>
                        <p>{{ item.analysis.counter_narrative_strategy or 'تحلیل ناموفق' }}</p>
                    </div>
                </div>
                <details>
                    <summary class="text-muted small">مشاهده جزئیات فریم‌بندی</summary>
                    <p class="mt-2"><strong>فریم روانی:</strong> {{ item.analysis.framing }}</p>
                    <p><strong>اثر مورد انتظار:</strong> {{ item.analysis.expected_effect }}</p>
                </details>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    t = Template(template_str)
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(t.render(recent=recent))

if __name__ == "__main__":
    main()
