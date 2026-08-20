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
    check("CGPA is 3.53", r["cgpa"]["cgpa"] == 3.53)
    check("standing is excellent", r["cgpa"]["standing"] == "excellent")

    # trend section
    pts = r["trend"]["points"]
    check("trend has 8 completed points", len(pts) == 8)
    check("trend direction is up", r["trend"]["direction"] == "up")
    check("trend gpas correct", [p["gpa"] for p in pts] == [3.56, 3.14, 3.19, 3.2, 3.54, 3.72, 3.96, 4.0])

    # fees section
    check("fees total correct", r["fees"]["total"] == 442250)
    check("fees due correct", r["fees"]["due"] == 0)
    check("fees status clear", r["fees"]["status"] == "clear")

    # attendance section
    check("threshold is 75", r["attendance"]["threshold"] == 75)
    check("attendance section present", "courses" in r["attendance"])

    # semesters section
    sems = r["semesters"]
    check("eight semesters present", len(sems) == 8)
    complete = [s for s in sems if s["status"] == "complete"]
    check("eight complete semesters", len(complete) == 8)
    check("all semesters have a gpa", all(s["gpa"] is not None for s in complete))

    # ---- edge: empty/new student must not crash and must be coherent ----
    empty = normalize_student({"student_id": "N", "name": "New", "current_semester": 1,
                               "semesters": {}, "fees": [], "attendance": [], "schedule": []})
    er = assemble_report(empty)
    check("empty student: cgpa no_data", er["cgpa"]["standing"] == "no_data")
    check("empty student: no trend points", er["trend"]["points"] == [])
    check("empty student: fees clear", er["fees"]["status"] == "clear")

    # ---- credits + degree progress (added after portal review) ----
    check("credits section present", "credits" in r)
    check("completed credits is 116", r["credits"]["completed"] == 116)
    check("degree percent is sane", 0 <= r["credits"]["percent"] <= 100)
    check("degree total is configurable", r["credits"]["total_required"] > 0)
    check("progress flagged as estimate", r["credits"]["is_estimate"] is True)

    # ---- course history ----
    check("course history present", "course_history" in r)
    check("course history has entries", len(r["course_history"]) > 0)
    check("history entries have status", all("status" in c for c in r["course_history"]))
    check("history status is taken/in_progress",
          all(c["status"] in ("taken", "in_progress") for c in r["course_history"]))

    # ---- per-assessment marks breakdown ----
    check("marks_breakdown present", "marks_breakdown" in r)
    mb = r["marks_breakdown"]
    check("marks scheme is 25/50/25",
          mb["scheme"] == {"mid": 25, "final": 50, "sessional": 25})
    check("marks breakdown has semesters", len(mb["semesters"]) > 0)
    # find a posted course and verify its breakdown structure + math
    first_course = None
    for sem in mb["semesters"]:
        for c in sem["courses"]:
            if c["total"] is not None:
                first_course = c
                break
        if first_course:
            break
    check("found a posted course", first_course is not None)
    if first_course:
        comps = first_course["breakdown"]
        check("breakdown has 3 components", len(comps) == 3)
        check("components are mid/final/sessional",
              [x["component"] for x in comps] == ["Mid-Term", "Final", "Sessional"])
        check("component maxes are 25/50/25",
              [x["max"] for x in comps] == [25, 50, 25])
        # obtained components should sum to the course total
        total_from_parts = sum(x["obtained"] for x in comps if x["obtained"] is not None)
        check("components sum to course total", total_from_parts == first_course["total"])
        # percentage math
        mid = comps[0]
        check("mid percentage correct",
              mid["percent"] == round(mid["obtained"] / 25 * 100))

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
