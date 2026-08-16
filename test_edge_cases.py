# test_edge_cases.py — DEPARTMENT 4: does the agent survive messy/extreme data?
#
# PLAIN ENGLISH:
# Real portal data is never as clean as one perfect demo record. Students can be
# brand new (no results), failing (all F), graduated, or have records with missing
# fields, None values, or garbage. This suite runs EVERY skill against EVERY one
# of those situations and asserts nothing crashes. Records are passed through the
# normalizer first (exactly as server.py does).
#
# Usage:  python test_edge_cases.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.normalize import normalize_student
from skills.cgpa_dashboard import cgpa_dashboard
from skills.fees import fees_summary
from skills.attendance import attendance_summary
from skills.report_card import report_card
from skills.goal_planner import goal_planner
from skills.alerts import alerts_summary
from skills.schedule import schedule_summary
from skills.predictor import predictor
from skills.whatif import whatif


def _sem(courses, term="Term"):
    return {"term": term, "courses": courses}


EDGE_STUDENTS = {
    "brand new (empty)": {
        "student_id": "N", "name": "New", "current_semester": 1,
        "semesters": {}, "fees": [], "attendance": [], "schedule": [],
    },
    "failing (all F)": {
        "student_id": "F", "name": "Fail", "current_semester": 2,
        "semesters": {"1": _sem([
            {"code": "C1", "title": "C", "credit_hours": 3, "mid": 5, "final": 10, "sessional": 5}])},
        "fees": [{"term": "F", "total": 50000, "paid": 0}],
        "attendance": [{"code": "C1", "title": "C", "present": 2, "total": 30}],
        "schedule": [],
    },
    "graduated (8 sems)": {
        "student_id": "G", "name": "Grad", "current_semester": 8,
        "semesters": {str(i): _sem([
            {"code": f"C{i}", "title": f"C{i}", "credit_hours": 3,
             "mid": 22, "final": 45, "sessional": 23}]) for i in range(1, 9)},
        "fees": [], "attendance": [], "schedule": [],
    },
    "missing fields": {
        "student_id": "B", "name": "B", "current_semester": 1,
        "semesters": {"1": _sem([{"code": "C1", "mid": 20, "final": 40, "sessional": 20}])},
        "fees": [{"term": "F", "total": 50000}],
        "attendance": [{"code": "C1"}], "schedule": [],
    },
    "None values": {
        "student_id": "Z",
        "semesters": {"1": _sem([
            {"code": "C1", "title": "C", "credit_hours": None,
             "mid": None, "final": None, "sessional": None}])},
        "fees": [{"term": "X", "total": None, "paid": None}],
        "attendance": [{"code": "C1", "title": "C", "present": None, "total": None}],
        "schedule": [],
    },
    "missing keys entirely": {
        "semesters": {"1": {}}, "fees": [{}], "attendance": [{}], "schedule": [{}],
    },
    "totally empty record": {},
    "garbage types": {
        "semesters": {"1": {"courses": [{"credit_hours": "abc", "mid": "xx"}]}},
        "fees": [{"total": "lots"}],
        "attendance": [{"present": "many", "total": "?"}],
    },
}

SKILLS = [
    ("cgpa", lambda d: cgpa_dashboard(d, "cgpa")),
    ("fees", lambda d: fees_summary(d, "fees")),
    ("attendance", lambda d: attendance_summary(d, "attendance")),
    ("report_card", lambda d: report_card(d, "result")),
    ("goal", lambda d: goal_planner(d, "can I get 3.5")),
    ("alerts", lambda d: alerts_summary(d)),
    ("schedule", lambda d: schedule_summary(d, "schedule")),
    ("predictor", lambda d: predictor(d, "what do I need to pass")),
    ("whatif", lambda d: whatif(d, "what if I get 40")),
]


def run():
    total = passed = 0
    for label, raw in EDGE_STUDENTS.items():
        data = normalize_student(raw)   # exactly what server.py does
        for sname, fn in SKILLS:
            total += 1
            try:
                fn(data)
                passed += 1
            except Exception as e:
                print(f"[FAIL] {label:24} {sname:12} -> {type(e).__name__}: {str(e)[:40]}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} passed",
          "— ALL GREEN" if passed == total else f"— {total - passed} CRASH(ES)")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
