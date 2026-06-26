# server.py — Flask backend: serves the premium interface + formats replies as clean cards.
import json
import os
import re
import shutil
from flask import Flask, render_template, request, jsonify

from config import DATA_FILE
from core.router import route
from core.roman_urdu import to_roman_urdu
from skills.report_card import report_card
from skills.cgpa_dashboard import cgpa_dashboard
from skills.fees import fees_summary
from skills.attendance import attendance_summary
from skills.whatif import whatif
from skills.predictor import predictor
from skills.goal_planner import goal_planner
from skills.schedule import schedule_summary
from skills.alerts import alerts_summary
from skills.trend_chart import trend_chart
from knowledge.rag import answer_question

DATA = json.load(open(DATA_FILE, encoding="utf-8"))
app = Flask(__name__)


# ---------- markdown -> clean HTML cards ----------
def md_to_card(md, downloadable=False):
    """Turn a skill's markdown (title + table/lines) into a clean horizontal-table card."""
    lines = [l for l in md.split("\n")]
    html = ['<div class="result-card">']
    table_rows = []
    in_table = False
    title_done = False

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return ""
        header = table_rows[0]
        body = table_rows[1:]
        # build a compact horizontal table
        out = ['<table class="rtable">']
        # header row
        out.append("<tr>")
        for i, h in enumerate(header):
            cls = "" if i == 0 else ' class="c"'
            out.append(f"<th{cls}>{h}</th>")
        out.append("</tr>")
        # body rows
        for row in body:
            out.append("<tr>")
            for i, v in enumerate(row):
                h = header[i].lower() if i < len(header) else ""
                if i == 0:
                    out.append(f'<td class="subj">{v}</td>')
                elif "grade" in h:
                    cell = f'<span class="gd">{v}</span>' if v not in ("", "—") else "—"
                    out.append(f'<td class="c">{cell}</td>')
                elif "total" in h:
                    out.append(f'<td class="tot">{v}</td>')
                else:
                    out.append(f'<td class="c">{v}</td>')
            out.append("</tr>")
        out.append("</table>")
        table_rows = []
        return "".join(out)

    for line in lines:
        s = line.strip()
        if not s:
            continue
        img = re.search(r"!\[.*?\]\((.*?)\)", s)
        if img:
            html.append(f'<img src="{img.group(1)}" alt="GPA Trend">')
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|")[1:-1]]
            if all(re.match(r"^-+$", c) for c in cells):
                continue
            in_table = True
            table_rows.append(cells)
            continue
        else:
            if in_table:
                html.append(flush_table())
                in_table = False
        clean = s.replace("**", "").replace("_", "")
        if not title_done and ("**" in line or clean.startswith("Your")):
            html.append(f'<div class="rc-title">{clean}</div>')
            title_done = True
            continue
        if re.search(r"(GPA|CGPA).*[:—-]\s*[\d.]", clean) or "GPA this semester" in clean:
            m = re.search(r"([\d.]+)\s*$", clean)
            val = m.group(1) if m else ""
            lbl = clean.split(":")[0] if ":" in clean else clean
            html.append(f'<div class="rc-foot"><span class="lbl">{lbl}</span><span class="val">{val}</span></div>')
            continue
        bold = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        html.append(f'<div style="font-size:13.5px;line-height:1.55;margin:3px 0;">{bold}</div>')

    if in_table:
        html.append(flush_table())
    if downloadable:
        html.append('<div class="dl"><button class="dl-png">⬇ Save as PNG</button></div>')
    html.append("</div>")
    return "".join(html)


def build_reply(message):
    intent, language = route(message)
    text = message.lower()

    # GPA trend chart -> image card
    if any(w in text for w in ["trend", "graph", "chart"]):
        path = trend_chart(DATA)
        if path:
            shutil.copy(path, os.path.join("static", "gpa_trend.png"))
            md = "Your GPA Trend\n\n![GPA Trend](/static/gpa_trend.png)"
            return md_to_card(md, downloadable=True), "english"
        return "I need at least two completed semesters to draw your GPA trend.", "english"

    if intent == "report_card": reply = report_card(DATA, message); dl=True
    elif intent == "cgpa": reply = cgpa_dashboard(DATA, message); dl=True
    elif intent == "fees": reply = fees_summary(DATA, message); dl=True
    elif intent == "attendance": reply = attendance_summary(DATA, message); dl=True
    elif intent == "whatif": reply = whatif(DATA, message); dl=False
    elif intent == "predictor": reply = predictor(DATA, message); dl=False
    elif intent == "goal": reply = goal_planner(DATA, message); dl=False
    elif intent == "schedule": reply = schedule_summary(DATA, message); dl=True
    elif intent == "alerts": reply = alerts_summary(DATA); dl=False
    else: reply = answer_question(message); dl=False

    if language == "roman_urdu":
        reply = to_roman_urdu(reply)

    return md_to_card(reply, downloadable=dl), language


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = (data or {}).get("message", "")
    if not message.strip():
        return jsonify({"html": "Please type a question."})
    try:
        html, _ = build_reply(message)
    except Exception as e:
        html = "Sorry, something went wrong while processing that."
    return jsonify({"html": html})


if __name__ == "__main__":
    app.run(debug=True, port=5000)