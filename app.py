# app.py — BUITEMS Copilot — main chat app
import json
import gradio as gr

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


def get_reply(message, history):
    if not message or not message.strip():
        return "Please type a question."

    intent, language = route(message)
    text = message.lower()

    # GPA trend chart (image) — returned as-is, no translation
    if any(w in text for w in ["trend", "graph", "chart"]):
        path = trend_chart(DATA)
        if path:
            return gr.Image(path)
        return "I need at least two completed semesters to draw your GPA trend."

    # get the English answer from the right skill
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

    # if the student wrote in Roman Urdu, reply in Roman Urdu
    if language == "roman_urdu":
        reply = to_roman_urdu(reply)

    return reply


with gr.Blocks(title="BUITEMS Copilot") as demo:
    gr.Markdown("## 🎓 BUITEMS Copilot\nYour AI academic assistant — ask in English or Roman Urdu.")
    gr.ChatInterface(
        fn=get_reply,
        examples=[
            "show my semester 3 result",
            "what should I know",
            "show my gpa trend",
            "mera result dikhao",
        ],
    )

if __name__ == "__main__":
    demo.launch()