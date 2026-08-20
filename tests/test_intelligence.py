# tests/test_intelligence.py — verifies the intelligence layer (Phase R2).
#
# PLAIN ENGLISH:
# Checks that the health score, strengths/weaknesses, risk flags, attendance
# recovery, and suggestions are all correct and coherent — recomputing the key
# numbers independently so a logic drift is caught.

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.normalize import normalize_student
from report.assemble import assemble_report
from report.intelligence import (
    build_intelligence, academic_health_score, attendance_recovery,
)

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "student.json")


def run():
    report = assemble_report(normalize_student(json.load(open(_DATA, encoding="utf-8"))))
    intel = build_intelligence(report)
    results = []

    def check(name, ok):
        results.append((name, ok))

    # ---- health score ----
    hs = intel["health_score"]
    check("health score in 0-100", 0 <= hs["score"] <= 100)
    check("health score is 91", hs["score"] == 91)
    check("band is Excellent", hs["band"] == "Excellent")
    check("breakdown has 3 factors", len(hs["breakdown"]) == 3)
    # component sum equals total
    check("breakdown sums to score",
          sum(b["points"] for b in hs["breakdown"]) == hs["score"])

    # ---- strengths / weaknesses ----
    check("has strengths", len(intel["strengths"]) > 0)
    check("top strength is an A-grade course",
          intel["strengths"][0]["grade_point"] >= 3.7)
    check("weaknesses are lower grades", all(w["grade_point"] < 3.0 for w in intel["weaknesses"]))

    # ---- risk flags ----
    flags = intel["flags"]
    check("flags present", len(flags) >= 1)
    check("flags are ordered by urgency",
          [f["level"] for f in flags] == sorted([f["level"] for f in flags],
                                                key=lambda l: {"red": 0, "amber": 1, "green": 2}[l]))

    # ---- attendance recovery (independently verified) ----
    rec = attendance_recovery(report)
    check("recovery is a list", isinstance(rec, list))
    # verify recovery math correctness on a synthetic below-threshold case
    from report.assemble import assemble_report as _ar
    test_low = normalize_student({"student_id":"L","name":"L","current_semester":1,
        "semesters":{}, "fees":[], "schedule":[],
        "attendance":[{"code":"X","title":"X","present":19,"total":30}]})
    lr = _ar(test_low); lrec = attendance_recovery(lr)
    check("recovery math: 19/30 needs 14", lrec and lrec[0]["classes_to_attend"] == 14)

    # ---- suggestions ----
    check("has suggestions", len(intel["suggestions"]) > 0)
    check("suggestions are non-empty strings",
          all(isinstance(s, str) and s for s in intel["suggestions"]))

    # ---- edge: perfect student gets a green flag, high score ----
    perfect = normalize_student({
        "student_id": "P", "name": "Perfect", "current_semester": 2,
        "semesters": {"1": {"term": "F", "courses": [
            {"code": "C1", "title": "C1", "credit_hours": 3, "mid": 25, "final": 50, "sessional": 25}]}},
        "fees": [{"term": "F", "total": 1000, "paid": 1000}],
        "attendance": [{"code": "C1", "title": "C1", "present": 30, "total": 30}],
        "schedule": [],
    })
    pr = assemble_report(perfect)
    pintel = build_intelligence(pr)
    check("perfect student scores high", pintel["health_score"]["score"] >= 95)
    check("perfect student has a green flag",
          any(f["level"] == "green" for f in pintel["flags"]))

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
