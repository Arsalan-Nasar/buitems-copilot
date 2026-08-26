# test_edge_cases.py — does the report survive messy / extreme data?
#
# Real portal data is never as clean as one perfect demo record. Students can be
# brand new (no results), failing (all F), graduated, or have records with missing
# fields, None values, or garbage types. This suite runs the FULL report pipeline
# (normalize -> assemble -> intelligence -> render) against every one of those
# situations and asserts nothing crashes and the output is always valid HTML.
#
# Usage:  python tests/test_edge_cases.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.normalize import normalize_student
from report.assemble import assemble_report
from report.intelligence import build_intelligence
from report.render import render_report


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
        "student_id": "G", "name": "Grad", "current_semester": 8, "graduated": True,
        "semesters": {str(i): _sem([
            {"code": "C%d" % i, "title": "C%d" % i, "credit_hours": 3,
             "mid": 22, "final": 45, "sessional": 23}]) for i in range(1, 9)},
        "fees": [], "attendance": [], "schedule": [],
    },
    "missing fields": {
        "student_id": "B", "name": "B", "current_semester": 1,
        "semesters": {"1": _sem([{"code": "C1", "mid": 20, "final": 40, "sessional": 20}])},
        "fees": [{"term": "F", "total": 50000}],
        "attendance": [{"code": "C1"}], "schedule": [],
    },
    "partial semester (some posted)": {
        "student_id": "P", "name": "Partial", "current_semester": 3,
        "semesters": {"3": _sem([
            {"code": "A", "title": "A", "credit_hours": 3, "mid": 22, "final": 44, "sessional": 22},
            {"code": "B", "title": "B", "credit_hours": 3, "mid": 20, "final": None, "sessional": None},
            {"code": "C", "title": "C", "credit_hours": 3, "mid": None, "final": None, "sessional": None},
        ])},
        "fees": [], "attendance": [], "schedule": [],
    },
    "missed mid, sat final": {
        "student_id": "M", "name": "Missed", "current_semester": 3,
        "semesters": {"3": _sem([
            {"code": "A", "title": "A", "credit_hours": 3, "mid": None, "final": 44, "sessional": 22}])},
        "fees": [], "attendance": [], "schedule": [],
    },
    "skipped whole semester": {
        "student_id": "S", "name": "Skip", "current_semester": 3,
        "semesters": {
            "1": _sem([{"code": "C", "title": "C", "credit_hours": 3, "mid": 20, "final": 40, "sessional": 20}]),
            "2": _sem([]),
            "3": _sem([{"code": "D", "title": "D", "credit_hours": 3, "mid": 21, "final": 42, "sessional": 21}]),
        },
        "fees": [], "attendance": [], "schedule": [],
    },
    "None values everywhere": {
        "student_id": None, "name": None, "program": None, "current_semester": None,
        "program_length": None, "graduated": None, "semesters": None,
        "fees": None, "attendance": None, "schedule": None,
    },
    "garbage types": {
        "student_id": [1, 2], "name": {"x": 1}, "program": 42,
        "current_semester": "three", "graduated": "yes",
        "semesters": {"1": {"term": 99, "courses": "not a list"}},
        "fees": "nope", "attendance": 5, "schedule": {},
    },
    "out-of-range marks": {
        "student_id": "R", "name": "Range", "current_semester": 1,
        "semesters": {"1": _sem([
            {"code": "C", "title": "C", "credit_hours": 3, "mid": 999, "final": -50, "sessional": 200}])},
        "fees": [], "attendance": [], "schedule": [],
    },
    "xss attempt in title": {
        "student_id": "X", "name": "<script>alert(1)</script>", "current_semester": 1,
        "semesters": {"1": _sem([
            {"code": "C", "title": "<img src=x onerror=alert(1)>", "credit_hours": 3,
             "mid": 22, "final": 44, "sessional": 22}])},
        "fees": [], "attendance": [], "schedule": [],
    },
}


def run():
    total = passed = 0
    for label, raw in EDGE_STUDENTS.items():
        # each edge student runs the full real pipeline, exactly like server.py
        checks = []
        try:
            data = normalize_student(raw)
            report = assemble_report(data)
            intel = build_intelligence(report)
            html = render_report(report, intel)
            checks.append(("pipeline runs", True))
            checks.append(("produces html", isinstance(html, str) and len(html) > 1000))
            checks.append(("valid doctype", html.lstrip().startswith("<!DOCTYPE html>")))
            # XSS: raw script tags must never appear unescaped in output
            checks.append(("no unescaped <script>alert", "<script>alert(1)</script>" not in html))
            # CGPA, if present, is always in range
            cg = report["cgpa"]["cgpa"]
            checks.append(("cgpa in range", cg is None or (0.0 <= cg <= 4.0)))
        except Exception as e:
            checks.append(("pipeline runs", False))
            print("[CRASH] %-28s -> %s: %s" % (label, type(e).__name__, str(e)[:50]))

        for cname, ok in checks:
            total += 1
            if ok:
                passed += 1
            else:
                print("[FAIL] %-28s %s" % (label, cname))

    print("=" * 60)
    print("TOTAL: %d/%d passed" % (passed, total),
          "— ALL GREEN" if passed == total else "— %d FAIL(S)" % (total - passed))
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
