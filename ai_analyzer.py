import json
import os
import datetime
from openai import OpenAI

BASE_URL = "https://ai.liara.ir/api/698d02e7fa009fae9b12b7dd/v1"
MODEL_NAME = "google/gemini-3-pro-preview"
API_KEY = os.environ.get("LIARA_AI_API_KEY")
DATA_FILE = "data/videos.json"

# We instruct the model to accept a JSON dictionary of ID:Data and return ID:Analysis
PSYCHO_PROMPT = """
You are an expert in Cognitive Warfare and Propaganda Analysis.
Your task is to analyze a batch of video metadata to identify psychological manipulation tactics.

Input Format: A JSON object where keys are Video IDs and values are objects containing "title" and "description".

Output Format: A JSON object where keys are the SAME Video IDs, and values are objects following this schema (in Persian/Farsi):
{
  "viewer_emotion": "The primary emotion being induced (e.g., Fear, Hope, Anger)",
  "viewer_expectation": "What the viewer is led to expect about the future",
  "psychological_impact": "The intended psychological effect on the target audience",
  "call_to_action": "What the content implicitly wants the user to do (mobilize, despair, fight, etc.)",
  "urgency_score": "Integer 1-10 indicating the intensity of the narrative attack"
}

Ensure the output is valid JSON. Do not include Markdown code blocks.
"""

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def batch_analyze(videos):
    """
    Sends a batch of videos to the AI model in a single request.
    """
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=120.0)

    # Prepare payload: { "vid1": {"title": "...", "desc": "..."}, "vid2": ... }
    payload = {
        v['video_id']: {"title": v['title'], "description": v['description']} 
        for v in videos
    }

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": PSYCHO_PROMPT},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
            ],
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content
        
        # Robust parsing to handle potential markdown wrappers
        start = content.find("{")
        end = content.rfind("}") + 1
        clean_json = content[start:end]
        
        return json.loads(clean_json)
    except Exception as e:
        print(f"Error during API call or parsing: {e}")
        return {}

def main():
    if not API_KEY:
        print("Error: LIARA_AI_API_KEY is not set.")
        return

    data = load_data()
    
    # Filter for videos that have NOT been analyzed yet
    unanalyzed = [v for v in data if v.get("analysis") is None]

    if not unanalyzed:
        print("All videos are already analyzed.")
        return

    print(f"Found {len(unanalyzed)} videos to analyze.")

    # Process in batches of 15 to respect context windows and rate limits
    BATCH_SIZE = 15
    
    for i in range(0, len(unanalyzed), BATCH_SIZE):
        batch = unanalyzed[i:i + BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} items)...")
        
        results = batch_analyze(batch)
        
        for video in batch:
            vid_id = video["video_id"]
            if vid_id in results:
                video["analysis"] = results[vid_id]
                video["analyzed_at"] = datetime.datetime.utcnow().isoformat()
                print(f"  [OK] Analyzed: {video['title'][:30]}...")
            else:
                print(f"  [FAIL] No result for: {video['title'][:30]}")

    save_data(data)
    print("Batch analysis complete.")

if __name__ == "__main__":
    main()
