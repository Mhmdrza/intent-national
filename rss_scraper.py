import feedparser
import json
import os
import datetime
import argparse
from dateutil import parser

DATA_DIR = "data"

# ----------------------------------------------------------------------
# Option 1: define channels directly in this list (leave empty if using CLI)
# Format: (channel_id, output_filename_inside_DATA_DIR)
# ----------------------------------------------------------------------
CHANNELS = [
    # ("UCat6bC0Wrqq9Bcq7EkH_yQw", "videos.json"),
    # ("UCldfgbzNILYZA4dmDt4Cd6A", "secular_talk.json"),
]

# ----------------------------------------------------------------------
# Database helpers – now accept a file path
# ----------------------------------------------------------------------
def load_db(filepath):
    """Load existing video database from a JSON file."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return {v["video_id"]: v for v in json.load(f)}
            except json.JSONDecodeError:
                return {}
    return {}

def save_db(db, filepath):
    """Save the video database, sorted by publication date."""
    data = sorted(db.values(), key=lambda x: x["published_at"], reverse=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------
# Processing a single channel
# ----------------------------------------------------------------------
def process_channel(channel_id, output_file):
    """Fetch RSS for a given YouTube channel and update its JSON store."""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    filepath = os.path.join(DATA_DIR, output_file)
    db = load_db(filepath)

    print(f"Fetching RSS for channel {channel_id} ...")
    feed = feedparser.parse(rss_url)

    new_items = 0
    for entry in feed.entries:
        vid = getattr(entry, "yt_videoid", None)
        if not vid or vid in db:
            continue

        # Description: try media_group first, fallback to summary
        desc = ""
        if hasattr(entry, "media_group") and entry.media_group:
            desc = entry.media_group[0].get("media_description", "")
        if not desc:
            desc = getattr(entry, "summary", "")

        # Parse publication date
        try:
            pub = parser.parse(entry.published).isoformat()
        except Exception:
            pub = datetime.datetime.utcnow().isoformat()

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
        save_db(db, filepath)
        print(f"  Added {new_items} new videos → {filepath}")
    else:
        print("  No new videos.")

# ----------------------------------------------------------------------
# Main entry point – supports both CLI arguments and the CHANNELS list
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Scrape YouTube channel RSS feeds and store video metadata."
    )
    parser.add_argument(
        "--channel", "-c",
        action="append",
        dest="channel_ids",
        help="YouTube channel ID (can be repeated)"
    )
    parser.add_argument(
        "--output", "-o",
        action="append",
        dest="output_files",
        help="Output JSON filename (relative to data/), paired with --channel"
    )
    args = parser.parse_args()

    # Combine CLI arguments (if any) into pairs
    cli_pairs = []
    if args.channel_ids or args.output_files:
        if not (args.channel_ids and args.output_files) or \
           len(args.channel_ids) != len(args.output_files):
            parser.error("When using --channel and --output you must provide them in equal numbers.")
        cli_pairs = list(zip(args.channel_ids, args.output_files))

    # Use CHANNELS list if no CLI arguments given
    channels_to_process = cli_pairs if cli_pairs else CHANNELS

    if not channels_to_process:
        print("No channels specified. Either edit the CHANNELS list in the script or use:")
        print("  python script.py --channel UC... --output file1.json --channel UC... --output file2.json")
        return

    for channel_id, output_file in channels_to_process:
        process_channel(channel_id, output_file)

if __name__ == "__main__":
    main()
