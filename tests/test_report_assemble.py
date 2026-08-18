# tests/test_report_assemble.py — verifies the report-assembly engine.
#
# PLAIN ENGLISH:
# The report engine is the backbone — every section of the visual report reads
# from it. This test confirms it produces correct, complete, structured data:
# right CGPA, right trend, right fee dues, right attendance flags, and safe
# handling of an in-progress semester.

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.normalize import normalize_student
from report.assemble import assemble_report

_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "student.json")


def run():
    data = normalize_student(json.load(open(_DATA_PATH, encoding="utf-8")))
    r = assemble_report(data)
    results = []

    def check(name, ok):
        results.append((name, ok))

    # student section
    check("student name present", bool(r["student"]["name"]))
    check("program present", bool(r["student"]["program"]))

    # cgpa section
    check("CGPA is 3.28", r["cgpa"]["cgpa"] == 3.28)
    check("standing is 'good'", r["cgpa"]["standing"] == "good")

    # trend section
    pts = r["trend"]["points"]
    check("trend has 3 completed points", len(pts) == 3)
    check("trend direction is up", r["trend"]["direction"] == "up")
    check("trend gpas correct", [p["gpa"] for p in pts] == [3.17, 3.0, 3.67])

    # fees section
    check("fees total correct", r["fees"]["total"] == 228250)
    check("fees due correct", r["fees"]["due"] == 39415)
    check("fees status outstanding", r["fees"]["status"] == "outstanding")

    # attendance section
    below = r["attendance"]["below_threshold"]
    check("one course below threshold", len(below) == 1)
    check("AI flagged at 63%", below[0]["percent"] == 63)
    check("threshold is 75", r["attendance"]["threshold"] == 75)

    # semesters section
    sems = r["semesters"]
    check("four semesters present", len(sems) == 4)
    complete = [s for s in sems if s["status"] == "complete"]
    check("three complete semesters", len(complete) == 3)
    inprog = [s for s in sems if s["status"] == "in_progress"]
    check("semester 4 is in_progress", len(inprog) == 1 and inprog[0]["semester"] == "4")
    check("in_progress semester has no gpa", inprog[0]["gpa"] is None)

    # ---- edge: empty/new student must not crash and must be coherent ----
    empty = normalize_student({"student_id": "N", "name": "New", "current_semester": 1,
                               "semesters": {}, "fees": [], "attendance": [], "schedule": []})
    er = assemble_report(empty)
    check("empty student: cgpa no_data", er["cgpa"]["standing"] == "no_data")
    check("empty student: no trend points", er["trend"]["points"] == [])
    check("empty student: fees clear", er["fees"]["status"] == "clear")

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        if not ok:
            print(f"[FAIL] {name}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else f"— {len(results) - passed} FAIL")
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
