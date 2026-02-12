import feedparser
import json
import os
import datetime
from dateutil import parser

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "videos.json")

def load_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return {v["video_id"]: v for v in json.load(f)}
            except: return {}
    return {}

def save_db(db):
    data = sorted(db.values(), key=lambda x: x["published_at"], reverse=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    db = load_db()
    print(f"Fetching RSS...")
    feed = feedparser.parse(RSS_URL)
    
    new_items = 0
    for entry in feed.entries:
        vid = getattr(entry, "yt_videoid", None)
        if not vid or vid in db: continue

        # Extract description
        desc = ""
        if hasattr(entry, "media_group") and entry.media_group:
             desc = entry.media_group[0].get("media_description", "")
        if not desc: desc = getattr(entry, "summary", "")

        try: pub = parser.parse(entry.published).isoformat()
        except: pub = datetime.datetime.utcnow().isoformat()

        db[vid] = {
            "video_id": vid,
            "title": entry.title,
            "link": entry.link,
            "published_at": pub,
            "description": desc,
            "analysis": None,
            "fetched_at": datetime.datetime.utcnow().isoformat()
        }
        new_items += 1

    if new_items:
        save_db(db)
        print(f"Added {new_items} new videos.")
    else:
        print("No new videos.")

if __name__ == "__main__":
    main()
