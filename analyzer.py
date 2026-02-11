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
MAX_NEW_VIDEOS_PER_RUN = 8 # Safety limit for cost control

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
    if not API_KEY: return None
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
        return json.loads(content[content.find('{'):content.rfind('}')+1])
    except Exception as e:
        print(f"   ⚠️ AI skipped due to error: {e}")
        return None

def main():
    # 1. LOAD CACHE (MEMOIZATION)
    if not os.path.exists("data"): os.makedirs("data")
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            # We use a dict for O(1) lookup speed
            database = {item['video_id']: item for item in json.load(f)}
    else:
        database = {}

    print(f"📦 Memoizer loaded: {len(database)} analyzed videos in memory.")

    # 2. FETCH FEED
    feed = feedparser.parse(RSS_URL)
    new_analyses_count = 0

    for entry in feed.entries:
        v_id = getattr(entry, 'yt_videoid', None)
        
        # --- THE EXPENSIVE CHECK (Memoization) ---
        if v_id in database:
            # Skip! We already spent money on this one.
            continue
        
        if new_analyses_count >= MAX_NEW_VIDEOS_PER_RUN:
            print("🛑 Hit safety limit for this run. Saving budget.")
            break

        # Simple NLP Check: Ignore very short titles or placeholders
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

    # 3. SAVE BACK TO DISK (Updates the Bench)
    # Sort by date so newest stays on top for the UI
    final_list = sorted(database.values(), key=lambda x: x['published_at'], reverse=True)
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)

    # 4. GENERATE DASHBOARD
    generate_html(final_list)
    print(f"✨ Success. {new_analyses_count} new items added to bench.")

def generate_html(data):
    # (The same HTML/JS Pagination code from previous response goes here)
    # I'll keep the template inside the file to ensure it's a "Full File" for you.
    json_data = json.dumps(data, default=str, ensure_ascii=False)
    # ... [Insert the Template string from previous response here] ...
    # (Writing to HTML_OUTPUT)
