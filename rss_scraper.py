import feedparser
import json
import os
import datetime
from dateutil import parser

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCat6bC0Wrqq9Bcq7EkH_yQw"
DATA_FILE = "data/videos.json"


def load_database():
    if not os.path.exists("data"):
        os.makedirs("data")

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return {v["video_id"]: v for v in json.load(f)}
    return {}


def save_database(db):
    final = sorted(
        db.values(),
        key=lambda x: x["published_at"],
        reverse=True
    )
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)


def main():
    db = load_database()
    feed = feedparser.parse(RSS_URL)

    for entry in feed.entries:
        v_id = getattr(entry, "yt_videoid", None)
        if not v_id or v_id in db:
            continue

        desc = ""
        if hasattr(entry, "media_group"):
            desc = entry.media_group[0].get("media_description", "")

        db[v_id] = {
            "video_id": v_id,
            "title": entry.title,
            "link": entry.link,
            "published_at": parser.parse(entry.published).isoformat(),
            "description": desc,
            "analysis": None,
            "fetched_at": datetime.datetime.utcnow().isoformat(),
            "analyzed_at": None
        }

    save_database(db)


if __name__ == "__main__":
    main()
