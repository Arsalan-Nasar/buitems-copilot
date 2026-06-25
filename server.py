# server.py — Flask backend: serves the premium interface + connects chat to the engine.
import json
import os
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


def build_reply(message):
    """Same routing logic as before — returns text, or a markdown image link for the chart."""
    intent, language = route(message)
    text = message.lower()

    # GPA trend chart -> save image, return markdown that points to it
    if any(w in text for w in ["trend", "graph", "chart"]):
        path = trend_chart(DATA)
        if path:
            # copy chart into static so the browser can load it
            dest = os.path.join("static", "gpa_trend.png")
            import shutil
            shutil.copy(path, dest)
            return "**Your GPA Trend**\n\n![GPA Trend](/static/gpa_trend.png)"
        return "I need at least two completed semesters to draw your GPA trend."

    if intent == "report_card":
        reply = report_card(DATA, message)
    elif intent == "cgpa":
        reply = cgpa_dashboard(DATA, message)
    elif intent == "fees":
        reply = fees_summary(DATA, message)
    elif intent == "attendance":
        reply = attendance_summary(DATA, message)
    elif intent == "whatif":
        reply = whatif(DATA, message)
    elif intent == "predictor":
        reply = predictor(DATA, message)
    elif intent == "goal":
        reply = goal_planner(DATA, message)
    elif intent == "schedule":
        reply = schedule_summary(DATA, message)
    elif intent == "alerts":
        reply = alerts_summary(DATA)
    else:
        reply = answer_question(message)

    if language == "roman_urdu":
        reply = to_roman_urdu(reply)
    return reply


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = (data or {}).get("message", "")
    if not message.strip():
        return jsonify({"reply": "Please type a question."})
    try:
        reply = build_reply(message)
    except Exception as e:
        reply = "Sorry, something went wrong while processing that."
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, port=5000)