# core/router.py — THE BRAIN. Reads the message, picks which skill should answer.
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
        "goal", "target", "graduate with", "i want", "plan", "reach cgpa",
        "possible", "achievable", "achieve",
    ],
    "schedule": [
        "schedule", "timetable", "class today", "next class", "datesheet",
    ],
    "alerts": [
        "alert", "alerts", "summary", "overview", "at a glance",
        "what should i know", "anything important", "notifications",
    ],
}

# ---------- ACTION-SHAPE detection (the permanent fix) ----------
# Any of these verbs, combined with "my"/"me"/"for me"/"on my behalf" nearby,
# means the student is asking the agent to DO something — not view something.
_ACTION_VERBS = [
    "pay", "email", "contact", "message", "call", "tell", "inform",
    "mark", "change", "edit", "fix", "update", "delete", "remove", "erase",
    "hack", "override", "reveal", "give me the password", "login as",
    "take my exam", "take this exam", "sit my exam", "do my homework",
    "do my assignment", "write my", "submit my", "talk to", "speak to",
]


def _is_action_request(text):
    """True if the message asks the agent to DO something (not just show data)."""
    for verb in _ACTION_VERBS:
        if verb in text:
            # multi-word verbs like "take my exam" are self-contained matches
            if " " in verb:
                return True
            # single verbs need "my"/"me"/"for me"/"on my behalf" nearby to count
            idx = text.find(verb)
            window = text[max(0, idx - 15): idx + len(verb) + 20]
            if re.search(r'\bmy\b|\bme\b|\bon my behalf\b', window):
                return True
    return False


def _looks_like_cgpa_goal(text):
    """A CGPA/GPA number together with clear goal-intent language."""
    has_number = re.search(r'\d\.\d{1,2}', text) is not None
    mentions_gpa_word = "cgpa" in text or "gpa" in text
    intent_words = ("possible", "achievable", "achieve", "reach", "target",
                     "goal", "graduate", "plan", "need")
    has_intent = any(w in text for w in intent_words)
    return has_number and mentions_gpa_word and has_intent


def route(message):
    """Return (intent, language). Intent is the skill to call; 'info' if none match."""
    text = message.lower().strip()

    if not text:
        return "empty", "english"

    language = detect_language(message)

    # checks that must win over the generic keyword loop below
    if _is_action_request(text):
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
        "what if I get 40 in my final",
        "I want to graduate with a 3.5",
        "Is a 3.2 CGPA possible for me?",
        "Can I get 100% attendance if I attend just one class?",
        "Can you pay my fees for me?",
        "Can you mark me present for today?",
        "Can you take my exam for me?",
        "Can you do my homework for me?",
        "Delete my fee record please",
        "Can you email my professor and ask for extra marks?",
        "Can you talk to the Dean for me?",
        "  ",
        "/",
    ]
    for t in tests:
        intent, lang = route(t)
        print(f"{intent:>14} | {lang:>10}  <-  {repr(t)}")