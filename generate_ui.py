import json
import os
from jinja2 import Template

DATA_FILE = "data/videos.json"
HTML_OUTPUT = "index.html"


def main():
    if not os.path.exists(DATA_FILE):
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    analyzed = [v for v in data if v["analysis"]]

    template = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>تحلیل روان‌شناختی روایت‌ها</title>

<style>
body {
    font-family: Vazirmatn, sans-serif;
    background: #111;
    color: #eaeaea;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 900px;
    margin: 60px auto;
    padding: 0 20px;
}

h1 {
    font-size: 28px;
    font-weight: 600;
    border-bottom: 1px solid #333;
    padding-bottom: 15px;
    margin-bottom: 40px;
}

.card {
    background: #1a1a1a;
    padding: 25px;
    margin-bottom: 30px;
    border-radius: 6px;
    border: 1px solid #222;
}

.card h2 {
    font-size: 18px;
    margin-bottom: 10px;
}

.meta {
    font-size: 13px;
    color: #888;
    margin-bottom: 15px;
}

.section {
    margin-bottom: 12px;
}

.label {
    font-weight: 600;
    color: #bbb;
}

.urgency {
    font-weight: 600;
    color: #ff4c4c;
}
</style>
</head>

<body>
<div class="container">
    <h1>تحلیل روان‌شناختی مخاطب رسانه</h1>

    {% for v in analyzed %}
    <div class="card">
        <h2><a href="{{ v.link }}" target="_blank" style="color:#fff; text-decoration:none;">
            {{ v.title }}
        </a></h2>

        <div class="meta">
            انتشار: {{ v.published_at }}
        </div>

        <div class="section">
            <span class="label">حس مخاطب:</span>
            {{ v.analysis.viewer_emotion }}
        </div>

        <div class="section">
            <span class="label">انتظار مخاطب:</span>
            {{ v.analysis.viewer_expectation }}
        </div>

        <div class="section">
            <span class="label">اثر روانی:</span>
            {{ v.analysis.psychological_impact }}
        </div>

        <div class="section urgency">
            شدت اثر: {{ v.analysis.urgency_score }}/10
        </div>
    </div>
    {% endfor %}
</div>
</body>
</html>
"""

    t = Template(template)
    html = t.render(analyzed=analyzed)

    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
