import feedparser
import json
import os
import datetime
from dateutil import parser
from openai import OpenAI
import pandas as pd
from jinja2 import Template

# تنظیمات
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"
API_KEY = os.environ.get("OPENAI_API_KEY")

# پرامپت مهندسی شده برای تحلیلگر رسانه (Expert Journalist Persona)
SYSTEM_PROMPT = """
You are a senior media analyst and expert in psychological warfare and narrative framing. 
Your goal is to deconstruct media coverage to find the hidden intent and suggest counter-narratives.

Analyze the provided YouTube video metadata (Title, Description). 
Output a JSON object with the following fields:
1. "core_message": The superficial message being conveyed.
2. "narrative_framing": The psychological framing used (e.g., Fear of war, Economic despair, Heroization of Pahlavi, Demonization of regime).
3. "hidden_intent": The reverse-engineered strategic goal behind this coverage (What do they want the viewer to feel or do?).
4. "counter_narrative_tip": A specific, punchy tip for a social media influencer to counter this narrative effectively.
"""

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def analyze_content(title, description):
    if not API_KEY:
        return {"error": "No API Key provided for analysis"}
    
    client = OpenAI(api_key=API_KEY)
    
    user_content = f"Title: {title}\nDescription: {description}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # یا gpt-3.5-turbo
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def update_feed():
    feed = feedparser.parse(RSS_URL)
    existing_data = load_data()
    existing_ids = {item['video_id'] for item in existing_data}
    
    new_entries = []
    
    # فیلتر کردن ویدیوهای ۸ ساعت گذشته (یا جدیدهایی که نداریم)
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    print(f"Fetching feed... Found {len(feed.entries)} items.")

    for entry in feed.entries:
        video_id = entry.yt_videoid
        published_dt = parser.parse(entry.published)
        
        # اگر ویدیو جدید است (در دیتابیس نیست)
        if video_id not in existing_ids:
            print(f"Processing new video: {entry.title}")
            
            # استخراج محتوا
            title = entry.title
            desc = entry.media_group[0]['media_description']
            thumbnail = entry.media_group[0]['media_thumbnail'][0]['url']
            
            # انجام تحلیل هوشمند
            analysis = analyze_content(title, desc)
            
            video_data = {
                "video_id": video_id,
                "title": title,
                "link": entry.link,
                "published_at": published_dt.isoformat(),
                "description": desc,
                "thumbnail": thumbnail,
                "fetched_at": current_time.isoformat(),
                "analysis": analysis
            }
            new_entries.append(video_data)
    
    # اضافه کردن به ابتدای لیست (جدیدترین‌ها اول)
    updated_data = new_entries + existing_data
    save_data(updated_data)
    return updated_data

def generate_html(data):
    # تبدیل به دیتافریم برای مدیریت راحت‌تر زمان
    df = pd.DataFrame(data)
    if not df.empty:
        df['published_at'] = pd.to_datetime(df['published_at'])
        # فیلترهای زمانی
        now = pd.Timestamp.now(tz='UTC')
        last_24h = df[df['published_at'] > (now - pd.Timedelta(days=1))]
        last_7d = df[df['published_at'] > (now - pd.Timedelta(days=7))]
    else:
        last_24h, last_7d = df, df

    html_template = """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>پنل رصد و تحلیل روایت (Counter-Narrative Dashboard)</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #f4f6f9; font-family: 'Tahoma', sans-serif; }
            .card { margin-bottom: 20px; border: none; shadow-sm: 0 2px 4px rgba(0,0,0,0.1); }
            .analysis-box { background-color: #e9ecef; padding: 15px; border-radius: 8px; margin-top: 10px; }
            .badge-intent { background-color: #dc3545; color: white; }
            .badge-counter { background-color: #198754; color: white; }
            .raw-data { font-size: 0.8em; color: #666; max-height: 100px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1 class="mb-4 text-center">پنل هوشمند تحلیل روایت رسانه</h1>
            
            <div class="row text-center mb-4">
                <div class="col-md-4">
                    <div class="card p-3">
                        <h3>{{ day_count }}</h3>
                        <p>ویدیوهای ۲۴ ساعت گذشته</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-3">
                        <h3>{{ week_count }}</h3>
                        <p>ویدیوهای ۷ روز گذشته</p>
                    </div>
                </div>
            </div>

            <h2 class="mb-3">تحلیل و پیشنهادات مقابله (۲۴ ساعت اخیر)</h2>
            <div class="row">
                {% for item in recent_items %}
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <img src="{{ item.thumbnail }}" class="img-fluid rounded" alt="Thumbnail">
                                </div>
                                <div class="col-md-9">
                                    <h5 class="card-title"><a href="{{ item.link }}" target="_blank">{{ item.title }}</a></h5>
                                    <small class="text-muted">{{ item.published_at }}</small>
                                    
                                    {% if item.analysis and item.analysis.core_message %}
                                    <div class="analysis-box">
                                        <p><strong>🎯 پیام اصلی:</strong> {{ item.analysis.core_message }}</p>
                                        <p><strong>🖼 فریم‌بندی روانی:</strong> {{ item.analysis.narrative_framing }}</p>
                                        <p><strong>🕵️ نیت پنهان (Reverse Engineered):</strong> <span class="text-danger">{{ item.analysis.hidden_intent }}</span></p>
                                        <div class="alert alert-success mt-2">
                                            <strong>💡 راهبرد پیشنهادی برای اینفلوئنسرها:</strong><br>
                                            {{ item.analysis.counter_narrative_tip }}
                                        </div>
                                    </div>
                                    {% else %}
                                    <p class="text-warning">تحلیل هوشمند برای این مورد موجود نیست.</p>
                                    {% endif %}
                                    
                                    <details>
                                        <summary>مشاهده داده خام (JSON)</summary>
                                        <pre class="raw-data">{{ item | tojson }}</pre>
                                    </details>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <h3 class="mt-5">آرشیو تحلیل‌های اخیر</h3>
            <table class="table table-striped">
                <thead><tr><th>تاریخ</th><th>عنوان</th><th>نیت شناسایی شده</th></tr></thead>
                <tbody>
                {% for item in history_items %}
                    <tr>
                        <td>{{ item.published_at }}</td>
                        <td><a href="{{ item.link }}">{{ item.title }}</a></td>
                        <td>{{ item.analysis.hidden_intent if item.analysis else '-' }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    rendered_html = template.render(
        recent_items=last_24h.to_dict(orient='records'),
        history_items=last_7d.to_dict(orient='records'),
        day_count=len(last_24h),
        week_count=len(last_7d)
    )
    
    with open(HTML_OUTPUT, "w", encoding='utf-8') as f:
        f.write(rendered_html)

if __name__ == "__main__":
    data = update_feed()
    generate_html(data)
