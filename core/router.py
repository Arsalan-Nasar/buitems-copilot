# core/router.py — THE BRAIN. Reads the message, picks which skill should answer.
# Works for BOTH English and Roman Urdu keywords.

import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.language import detect_language

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
        "possible", "achievable", "achieve", "can i reach", "can i get",
    ],
    "schedule": [
        "schedule", "timetable", "class today", "next class", "exam", "datesheet",
    ],
    "alerts": [
        "alert", "alerts", "summary", "overview", "at a glance",
        "what should i know", "anything important", "notifications",
    ],
}

# phrases that mean "do something to my data / someone else's data" —
# these must NEVER be treated as a normal data-display request
_OUT_OF_SCOPE_PATTERNS = [
    "change my grade", "change my mark", "change my cgpa", "change my result",
    "edit my grade", "edit my result", "fix my grade", "update my grade",
    "email my professor", "email professor", "contact my professor", "message my professor",
    "tell my parent", "tell my mom", "tell my dad", "tell my family",
    "another student", "someone else's", "other student's", "my friend's",
    "delete my", "remove my semester", "erase my", "hack",
    "admin password", "give me the password", "login as",
    "write me a poem", "write a poem", "tell me a joke", "write me a story",
]


def _looks_like_cgpa_goal(text):
    """
    High-priority check: a CGPA/GPA number together with clear goal-intent
    language means this is a goal question, regardless of which other
    keywords (predictor's 'what do i need', cgpa's 'cgpa') also appear.
    """
    has_number = re.search(r'\d\.\d{1,2}', text) is not None
    mentions_gpa_word = "cgpa" in text or "gpa" in text
    intent_words = (
        "possible", "achievable", "achieve", "reach", "target", "goal",
        "graduate", "plan", "need", "want", "get a", "can i"
    )
    has_intent = any(w in text for w in intent_words)
    return has_number and mentions_gpa_word and has_intent


def _is_out_of_scope_request(text):
    """Requests asking the agent to DO something it can't/shouldn't do."""
    return any(p in text for p in _OUT_OF_SCOPE_PATTERNS)


def route(message):
    """Return (intent, language). Intent is the skill to call; 'info' if none match."""
    text = message.lower()
    language = detect_language(message)

    # checks that must win over the generic keyword loop below
    if _is_out_of_scope_request(text):
        return "out_of_scope", language

    if _looks_like_cgpa_goal(text):
        return "goal", language

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
        "Is a 3.2 CGPA possible for me?",
        "What do I need for a 4.0 CGPA by semester 7?",
        "Can you change my grades for me?",
        "Can you email my professor and ask for extra marks?",
        "Will you tell my parents if my CGPA is low?",
        "Show me another student's CGPA",
        "Write me a poem about exams",
    ]
    for t in tests:
        intent, lang = route(t)
        print(f"{intent:>14} | {lang:>10}  <-  {t}")