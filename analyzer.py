import feedparser
import json
import os
import datetime
from dateutil import parser
from openai import OpenAI
import pandas as pd
from jinja2 import Template

# --- تنظیمات اختصاصی ---
BASE_URL = "https://ai.liara.ir/api/698d02e7fa009fae9b12b7dd/v1"
MODEL_NAME = "google/gemini-3-pro-preview"
API_KEY = os.environ.get("LIARA_AI_API_KEY") 

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"

# پرامپت مهندسی شده برای تحلیل نیت رسانه‌ای
SYSTEM_PROMPT = """
You are a senior media analyst and expert in psychological warfare. 
Analyze the Title and Description provided. 
Your goal is to help media influencers see through the 'narrative control' and form a counter-narrative.

Output ONLY a raw JSON object with these keys:
- "core_message": The superficial story.
- "framing": How the content is 'packaged' (e.g., creating fear, false hope, or victimhood).
- "hidden_intent": The reverse-engineered goal (What do they want the viewer to think/do?).
- "expected_effect": The psychological impact on the target audience's mind.
- "counter_narrative_strategy": Specific, punchy advice for an influencer to debunk or flip this narrative.
"""

def get_ai_analysis(title, description):
    if not API_KEY: 
        return {"error": "API Key is missing."}
    
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Title: {title}\nDescription: {description}"}
            ]
        )
        content = completion.choices[0].message.content
        # تمیز کردن پاسخ از فرمت احتمالی Markdown
        json_str = content[content.find('{'):content.rfind('}')+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"AI Error for {title[:20]}: {e}")
        return {"error": "Analysis failed"}

def main():
    # ۱. مدیریت داده‌های قبلی
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
    else:
        db = []

    existing_ids = {item['video_id'] for item in db}
    
    # ۲. فچ کردن ایمن فید
    print("Fetching RSS feed...")
    feed = feedparser.parse(RSS_URL)
    new_entries = []

    for entry in feed.entries:
        v_id = getattr(entry, 'yt_videoid', None)
        if not v_id or v_id in existing_ids:
            continue

        print(f"Analyzing new video: {entry.title}")
        
        # استخراج ایمن توضیحات و تامنیل
        desc = ""
        if hasattr(entry, 'media_group'):
            desc = entry.media_group[0].get('media_description', '')
        elif 'summary' in entry:
            desc = entry.summary

        thumb = ""
        if hasattr(entry, 'media_group') and 'media_thumbnail' in entry.media_group[0]:
            thumb = entry.media_group[0]['media_thumbnail'][0].get('url', '')

        analysis = get_ai_analysis(entry.title, desc)
        
        new_items = {
            "video_id": v_id,
            "title": entry.title,
            "link": entry.link,
            "published_at": parser.parse(entry.published).isoformat(),
            "thumbnail": thumb,
            "description": desc,
            "analysis": analysis,
            "fetched_at": datetime.datetime.now().isoformat()
        }
        new_entries.append(new_items)

    # ۳. به‌روزرسانی دیتابیس
    updated_db = new_entries + db
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_db, f, ensure_ascii=False, indent=2)

    # ۴. تولید داشبورد HTML
    generate_html(updated_db)

def generate_html(data):
    df = pd.DataFrame(data)
    df['published_at'] = pd.to_datetime(df['published_at'])
    now = pd.Timestamp.now(tz='UTC')

    # فیلترهای زمانی
    last_24h = df[df['published_at'] > (now - pd.Timedelta(hours=24))].to_dict(orient='records')
    last_7d = df[df['published_at'] > (now - pd.Timedelta(days=7))].to_dict(orient='records')

    template_str = """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>دیده‎‌بان روایت رسانه‌ای</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f0f2f5; font-family: Tahoma, sans-serif; }
            .analysis-card { border-left: 5px solid #0d6efd; transition: 0.3s; }
            .analysis-card:hover { transform: scale(1.01); }
            .intent-box { background: #fff3f3; border-radius: 8px; padding: 15px; border-right: 4px solid #dc3545; }
            .counter-box { background: #f3fff5; border-radius: 8px; padding: 15px; border-right: 4px solid #198754; }
            .raw-data { font-size: 0.75rem; background: #eee; padding: 10px; max-height: 150px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <h1 class="text-center mb-2">🕵️‍♂️ پنل مهندسی معکوس روایت</h1>
            <p class="text-center text-muted mb-5">تحلیل هوشمند نیت و استراتژی پاتک رسانه‌ای</p>

            <div class="row g-4">
                {% for item in recent %}
                <div class="col-12">
                    <div class="card shadow-sm analysis-card">
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <img src="{{ item.thumbnail }}" class="img-fluid rounded mb-3">
                                    <p class="small text-muted">انتشار: {{ item.published_at.strftime('%Y-%m-%d %H:%M') }}</p>
                                </div>
                                <div class="col-md-9">
                                    <h4 class="card-title text-primary"><a href="{{ item.link }}" target="_blank" class="text-decoration-none">{{ item.title }}</a></h4>
                                    
                                    <div class="row mt-3">
                                        <div class="col-md-6">
                                            <div class="intent-box h-100">
                                                <h6>🎯 تحلیل نیت و فریم‌بندی:</h6>
                                                <p><strong>فریم:</strong> {{ item.analysis.framing }}</p>
                                                <p><strong>نیت پنهان:</strong> {{ item.analysis.hidden_intent }}</p>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="counter-box h-100">
                                                <h6>💡 پاتک پیشنهادی برای اینفلوئنسرها:</h6>
                                                <p>{{ item.analysis.counter_narrative_strategy }}</p>
                                            </div>
                                        </div>
                                    </div>

                                    <details class="mt-3">
                                        <summary class="text-muted small">مشاهده داده خام و توضیحات</summary>
                                        <div class="raw-data mt-2">{{ item.description }}</div>
                                        <pre class="raw-data mt-2">{{ item.analysis | tojson(indent=2) }}</pre>
                                    </details>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>

            <hr class="my-5">
            <h3>📊 آرشیو و پروفایل ۷ روز اخیر</h3>
            <div class="table-responsive bg-white p-3 rounded shadow-sm">
                <table class="table align-middle">
                    <thead><tr><th>تاریخ</th><th>عنوان</th><th>نیت شناسایی شده</th></tr></thead>
                    <tbody>
                        {% for item in archive %}
                        <tr>
                            <td>{{ item.published_at.strftime('%m/%d') }}</td>
                            <td><small>{{ item.title }}</small></td>
                            <td><span class="badge bg-danger">{{ item.analysis.hidden_intent[:50] }}...</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(template_str)
    html_content = template.render(recent=last_24h, archive=last_7d)
    
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    main()
