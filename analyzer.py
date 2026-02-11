import feedparser
import json
import os
import datetime
import sys
from dateutil import parser
from openai import OpenAI
import pandas as pd
from jinja2 import Template

# --- CONFIG ---
BASE_URL = "https://ai.liara.ir/api/698d02e7fa009fae9b12b7dd/v1"
MODEL_NAME = "google/gemini-3-pro-preview"
API_KEY = os.environ.get("LIARA_AI_API_KEY")
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"
MAX_NEW_VIDEOS_PER_RUN = 8  # Safety limit for cost control

# --- THE PSYCHO-ANALYTIC PROMPT ---
PSYCHO_PROMPT = """
You are a Cognitive Psychologist. Profile the Target Audience's Mental State based on this news.
Output ONLY JSON in Persian:
{
  "viewer_emotion": "حس مخاطب",
  "viewer_expectation": "انتظار مخاطب",
  "psychological_impact": "اثر عمیق روانی",
  "urgency_score": 1-10
}
"""


def get_ai_analysis(title, description):
    if not API_KEY:
        return None

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=40.0)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": PSYCHO_PROMPT},
                {"role": "user", "content": f"Title: {title}\nDesc: {description}"}
            ]
        )
        content = completion.choices[0].message.content
        return json.loads(content[content.find('{'):content.rfind('}') + 1])
    except Exception as e:
        print(f"   ⚠️ AI skipped due to error: {e}")
        return None


def main():
    # 1. LOAD CACHE (MEMOIZATION)
    if not os.path.exists("data"):
        os.makedirs("data")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            database = {item['video_id']: item for item in json.load(f)}
    else:
        database = {}

    print(f"📦 Memoizer loaded: {len(database)} analyzed videos in memory.")

    # 2. FETCH FEED
    feed = feedparser.parse(RSS_URL)
    new_analyses_count = 0

    for entry in feed.entries:
        v_id = getattr(entry, 'yt_videoid', None)

        if v_id in database:
            continue

        if new_analyses_count >= MAX_NEW_VIDEOS_PER_RUN:
            print("🛑 Hit safety limit for this run. Saving budget.")
            break

        if len(entry.title) < 10:
            continue

        print(f"🧠 New Content Detected [ID: {v_id}]. Processing...")

        desc = ""
        if hasattr(entry, 'media_group'):
            desc = entry.media_group[0].get('media_description', '')

        analysis = get_ai_analysis(entry.title, desc)

        if analysis:
            database[v_id] = {
                "video_id": v_id,
                "title": entry.title,
                "link": entry.link,
                "published_at": parser.parse(entry.published).isoformat(),
                "analysis": analysis,
                "fetched_at": datetime.datetime.now().isoformat()
            }
            new_analyses_count += 1

    # 3. SAVE BACK TO DISK
    final_list = sorted(
        database.values(),
        key=lambda x: x['published_at'],
        reverse=True
    )

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)

    # 4. GENERATE DASHBOARD
    generate_html(final_list)

    print(f"✨ Success. {new_analyses_count} new items added to bench.")


def generate_html(data):
    if not data:
        with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
            f.write("<h1>No Data Yet</h1>")
        return

    df = pd.DataFrame(data)
    df['published_at'] = pd.to_datetime(df['published_at'])

    recent = (
        df.sort_values('published_at', ascending=False)
        .head(10)
        .to_dict(orient='records')
    )

    template_str = """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>دیده‎‌بان روایت</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #f8f9fa; font-family: sans-serif; }
            .analysis-box {
                border-right: 4px solid #007bff;
                background: #fff;
                margin-bottom: 20px;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .intent { color: #d9534f; font-weight: bold; }
            .counter { color: #5cb85c; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <h1 class="text-center mb-5">🕵️ تحلیل هوشمند روایت‌های رسانه‌ای</h1>
            {% for item in recent %}
            <div class="analysis-box">
                <h4>
                    <a href="{{ item.link }}" target="_blank" style="text-decoration:none;">
                        {{ item.title }}
                    </a>
                </h4>
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
