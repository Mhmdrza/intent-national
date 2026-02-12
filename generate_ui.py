import json
import os
from jinja2 import Template

DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"

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

    # Sort safely: if urgency_score is missing or not an int, default to 0
    def get_score(v):
        try:
            return int(v.get("analysis", {}).get("urgency_score", 0))
        except (ValueError, TypeError):
            return 0

    analyzed.sort(key=get_score, reverse=True)

    template_str = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>رادار جنگ شناختی</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
    <style>
        body { font-family: 'Vazirmatn', sans-serif; background: #0f172a; color: #f1f5f9; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { border-bottom: 2px solid #334155; padding-bottom: 15px; color: #38bdf8; }
        
        .card { 
            background: #1e293b; border: 1px solid #334155; border-radius: 8px; 
            padding: 20px; margin-bottom: 20px; transition: 0.2s;
        }
        .card:hover { border-color: #64748b; transform: translateY(-2px); }
        
        .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }
        .title { font-size: 1.2rem; font-weight: bold; color: #fff; text-decoration: none; flex: 1; }
        .title:hover { color: #38bdf8; }
        
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; white-space: nowrap; margin-right: 10px;}
        .high { background: #ef4444; color: white; }
        .med { background: #f59e0b; color: black; }
        .low { background: #10b981; color: white; }
        .unknown { background: #64748b; color: white; }
        
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; background: #0f172a; padding: 15px; border-radius: 6px; }
        .item { display: flex; flex-direction: column; }
        .label { font-size: 0.75rem; color: #94a3b8; margin-bottom: 3px; }
        .value { font-size: 0.95rem; }
        
        @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>رادار تحلیل جنگ شناختی</h1>
        {% for v in analyzed %}
            {# Safe access to urgency score using .get() #}
            {% set score = v.analysis.get('urgency_score', 0) | int %}
            
            <div class="card">
                <div class="header">
                    <a href="{{ v.link }}" target="_blank" class="title">{{ v.title }}</a>
                    <span class="badge {% if score >= 8 %}high{% elif score >= 5 %}med{% elif score > 0 %}low{% else %}unknown{% endif %}">
                        خطر: {{ score }}/10
                    </span>
                </div>
                <div class="grid">
                    <div class="item">
                        <span class="label">القای حسی</span>
                        <span class="value">{{ v.analysis.get('viewer_emotion', 'N/A') }}</span>
                    </div>
                    <div class="item">
                        <span class="label">انتظار مخاطب</span>
                        <span class="value">{{ v.analysis.get('viewer_expectation', 'N/A') }}</span>
                    </div>
                    <div class="item">
                        <span class="label">روایت معکوس</span>
                        <span class="value">{{ v.analysis.get('defensive_counter_narrative', 'N/A') }}</span>
                    </div>
                    <div class="item">
                        <span class="label">هدف رفتاری</span>
                        <span class="value">{{ v.analysis.get('call_to_action', 'N/A') }}</span>
                    </div>
                </div>
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""
    t = Template(template_str)
    try:
        html = t.render(analyzed=analyzed)
        with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"UI successfully generated at {HTML_OUTPUT}")
    except Exception as e:
        print(f"Error rendering template: {e}")

if __name__ == "__main__":
    main()
