import json
import os
from dateutil import parser
import jdatetime
from datetime import datetime

DATA_FILE = "data/videos.json"
OUTPUT_FILE = "public/data/processed.json"

def main():
    if not os.path.exists(DATA_FILE):
        print("Data file missing.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Error: JSON file is corrupted.")
            return

    # Filter analyzed videos
    analyzed = [v for v in data if v.get("analysis")]

    FALLBACK_DATE = parser.isoparse("1970-01-01T00:00:00+00:00")

    def get_published_date(v):
        try:
            return parser.isoparse(v.get("published_at"))
        except (ValueError, TypeError):
            return FALLBACK_DATE
    
    analyzed.sort(key=get_published_date, reverse=True)

    # Generate Persian Jalali timestamp
    now = datetime.now()
    jalali_now = jdatetime.datetime.fromgregorian(datetime=now)
    last_updated = jalali_now.strftime('%Y/%m/%d - %H:%M')

    # Create output structure
    output = {
        "last_updated": last_updated,
        "videos": analyzed
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Write processed data
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Data successfully processed and saved to {OUTPUT_FILE}")
    print(f"Total videos processed: {len(analyzed)}")
    print(f"Last updated: {last_updated}")

if __name__ == "__main__":
    main()
