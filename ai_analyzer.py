import json
import os
import time
import datetime
from dateutil import parser
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
  "defensive_counter_narrative": "How to mitigate / neutrilze this coverage",
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
    """Saves data to disk immediately."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sanitize_result(result):
    """Ensures the AI result strictly follows the schema to prevent UI crashes."""
    defaults = {
        "viewer_emotion": "Unknown",
        "viewer_expectation": "Unknown",
        "defensive_counter_narrative": "Analysis unavailable",
        "call_to_action": "None",
        "urgency_score": 0
    }
    
    # Merge defaults with result
    sanitized = {**defaults, **result}
    
    # Force urgency_score to be an integer
    try:
        sanitized["urgency_score"] = int(sanitized["urgency_score"])
    except (ValueError, TypeError):
        sanitized["urgency_score"] = 0
        
    return sanitized

def batch_analyze(videos):
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=120.0)

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
        
        # Strip potential markdown wrapping
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"  [Error] Batch failed: {e}")
        return {}

def main():
    if not API_KEY:
        print("Error: LIARA_AI_API_KEY is not set.")
        return

    data = load_data()
    
    # Create a lookup map for faster access
    video_map = {v["video_id"]: v for v in data}
    
    # Identify videos needing analysis
    unanalyzed_ids = [v["video_id"] for v in data if v.get("analysis") is None]

    if not unanalyzed_ids:
        print("All videos are already analyzed.")
        return

    print(f"Found {len(unanalyzed_ids)} videos to analyze.")

    BATCH_SIZE = 5 # Reduced batch size slightly for better stability
    
    for i in range(0, len(unanalyzed_ids), BATCH_SIZE):
        batch_ids = unanalyzed_ids[i:i + BATCH_SIZE]
        batch_videos = [video_map[vid] for vid in batch_ids]
        
        print(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch_ids)} items)...")
        
        results = batch_analyze(batch_videos)
        
        for vid in batch_ids:
            if vid in results:
                # Sanitize ensures 'urgency_score' exists even if AI forgot it
                clean_analysis = sanitize_result(results[vid])
                video_map[vid]["analysis"] = clean_analysis
                video_map[vid]["analyzed_at"] = datetime.datetime.utcnow().isoformat()
                print(f"  [OK] {video_map[vid]['title'][:20]}... -> Score: {clean_analysis['urgency_score']}")
            else:
                print(f"  [WARN] No result for {vid}")

        # === CRITICAL: Save after EVERY batch ===
        print("  -> Saving progress...")
        save_data(list(video_map.values()))
        
        # Small sleep to be kind to the API rate limit
        time.sleep(1)

    print("Analysis complete.")

if __name__ == "__main__":
    main()
