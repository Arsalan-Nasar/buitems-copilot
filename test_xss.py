# test_xss.py — DEPARTMENT 5 (web layer): Cross-Site Scripting defense.
#
# PLAIN ENGLISH:
# The agent builds HTML from data. If data contains something like
# '<script>...' and it goes into the HTML raw, the browser would EXECUTE it —
# an attacker's code running in a student's logged-in session. The defense is
# HTML-escaping: '<script>' must become harmless display text '&lt;script&gt;'.
#
# This suite injects malicious HTML into every data field and confirms the final
# HTML contains NO actual executable tag — only escaped, safe text.
#
# Usage:  python test_xss.py

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if "groq" not in sys.modules:
    sys.modules["groq"] = types.SimpleNamespace(Groq=lambda **k: None)

import server
from core.normalize import normalize_student
from skills.report_card import report_card
from skills.cgpa_dashboard import cgpa_dashboard
from skills.attendance import attendance_summary
from skills.fees import fees_summary
from skills.schedule import schedule_summary


import re

# Tags the app legitimately generates itself (safe).
_OUR_TAGS = {"div", "table", "tr", "td", "th", "span", "strong", "img", "button"}


def _has_executable_payload(html_out):
    """Return a real executable dangerous tag if one exists, else None.

    The ONLY real XSS danger is an UNESCAPED tag — a literal '<' followed by a
    tag name. Escaped text like '&lt;script&gt;' is safe display text and must
    NOT count. So we extract every actual '<tag ...>' and flag any that is not
    one we generate ourselves, or that carries an inline event handler / script.
    """
    for tag in re.findall(r"<[a-zA-Z/][^>]*>", html_out):
        name_match = re.match(r"</?([a-zA-Z]+)", tag)
        if not name_match:
            continue
        name = name_match.group(1).lower()
        low = tag.lower()
        if name == "script":
            return tag
        if "onerror" in low or "onload" in low or "onclick" in low or "javascript:" in low:
            return tag
        if name not in _OUR_TAGS:
            return tag
    return None


def _evil_student():
    xss = "<script>alert(document.cookie)</script>"
    xss2 = "<img src=x onerror=alert(1)>"
    return {
        "student_id": "X1",
        "name": xss,
        "program": xss2,
        "current_semester": 1,
        "semesters": {"1": {"term": xss, "courses": [
            {"code": xss2, "title": xss, "credit_hours": 3,
             "mid": 20, "final": 40, "sessional": 20}]}},
        "fees": [{"term": xss, "total": 50000, "paid": 0}],
        "attendance": [{"code": xss2, "title": xss, "present": 10, "total": 30}],
        "schedule": [{"code": xss2, "title": xss, "day": xss, "time": xss, "room": xss2}],
    }


def run():
    data = normalize_student(_evil_student())
    results = []

    skills = [
        ("report_card", report_card(data, "result")),
        ("cgpa", cgpa_dashboard(data, "cgpa")),
        ("attendance", attendance_summary(data, "attendance")),
        ("fees", fees_summary(data, "fees")),
        ("schedule", schedule_summary(data, "schedule")),
    ]

    for name, md in skills:
        html_out = server.md_to_card(md)
        hit = _has_executable_payload(html_out)
        results.append((f"{name}: no executable payload in HTML", hit is None))
        if hit:
            print(f"    [{name}] LEAKED executable marker: {hit!r}")

    # sanity: normal formatting (our own <strong>, <table>) must still work
    import json
    real = normalize_student(json.load(open("data/student.json", encoding="utf-8")))
    normal = server.md_to_card(cgpa_dashboard(real, "cgpa"))
    results.append(("normal CGPA value still displays", "3.28" in normal))
    results.append(("our own <strong> formatting still works", "<strong>" in normal))
    results.append(("our own <table> still works", "<table" in normal))

    passed = sum(1 for _, ok in results if ok)
    for nm, ok in results:
        if not ok:
            print(f"[FAIL] {nm}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else f"— {len(results) - passed} XSS HOLE(S)")
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
