# core/router.py — THE BRAIN. Reads the message, picks which skill should answer.
# Works for BOTH English and Roman Urdu keywords.

import os
import sys

# allow running this file directly for testing (adds the main folder to the path)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.language import detect_language

# Each intent maps to keywords in BOTH languages.
INTENTS = {
    "report_card": [
        "result", "report card", "marks", "grades", "natija",
        "semester result", "report", "transcript",
    ],
    "cgpa": [
        "cgpa", "gpa", "overall", "average", "progress", "trend",
    ],
    "fees": [
        "fee", "fees", "dues", "payment", "owe", "baqi", "jama", "challan",
    ],
    "attendance": [
        "attendance", "haziri", "present", "absent",
    ],
    "whatif": [
        "what if", "what-if", "agar", "suppose", "simulate", "predict my",
    ],
    "predictor": [
        "what do i need", "how much do i need", "pass", "to get", "required marks",
    ],
    "goal": [
        "goal", "target", "graduate with", "i want", "plan", "reach",
    ],
    "schedule": [
        "schedule", "timetable", "class today", "next class", "exam", "datesheet",
    ],
    "alerts": [
        "alert", "alerts", "summary", "overview", "at a glance",
        "what should i know", "anything important", "notifications",
    ],
}


def route(message):
    """Return (intent, language). Intent is the skill to call; 'info' if none match."""
    text = message.lower()
    language = detect_language(message)

    order = ["alerts", "whatif", "predictor", "goal", "schedule", "attendance",
             "fees", "cgpa", "report_card"]

    for intent in order:
        for kw in INTENTS[intent]:
            if kw in text:
                return intent, language

    return "info", language


# Quick test
if __name__ == "__main__":
    tests = [
        "show my semester 3 result",
        "mera result dikhao",
        "what is my cgpa",
        "meri fees kitni baqi hai",
        "what's my attendance",
        "what if I get 40 in my final",
        "what do I need to pass data structures",
        "I want to graduate with a 3.5",
        "what's my schedule today",
        "what scholarships can I apply for",
    ]
    for t in tests:
        intent, lang = route(t)
        print(f"{intent:>12} | {lang:>10}  <-  {t}")