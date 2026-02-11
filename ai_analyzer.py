import json
import os
import datetime
from openai import OpenAI

BASE_URL = "https://ai.liara.ir/api/698d02e7fa009fae9b12b7dd/v1"
MODEL_NAME = "google/gemini-3-pro-preview"
API_KEY = os.environ.get("LIARA_AI_API_KEY")
DATA_FILE = "data/videos.json"

PSYCHO_PROMPT = """
You are a Cognitive Psychologist.
Output ONLY JSON in Persian:
{
  "viewer_emotion": "...",
  "viewer_expectation": "...",
  "psychological_impact": "...",
  "urgency_score": 1-10
}
"""


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def analyze(video):
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=40.0)

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": PSYCHO_PROMPT},
            {
                "role": "user",
                "content": f"Title: {video['title']}\nDesc: {video['description']}"
            }
        ]
    )

    content = completion.choices[0].message.content
    return json.loads(content[content.find("{"):content.rfind("}") + 1])


def main():
    if not API_KEY:
        return

    data = load_data()

    for video in data:
        if video["analysis"] is not None:
            continue

        try:
            result = analyze(video)
            video["analysis"] = result
            video["analyzed_at"] = datetime.datetime.utcnow().isoformat()
        except Exception:
            continue

    save_data(data)


if __name__ == "__main__":
    main()
