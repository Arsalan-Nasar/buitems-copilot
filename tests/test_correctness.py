# test_correctness.py — DEPARTMENT 3: are the ANSWERS actually correct?
#
# PLAIN ENGLISH:
# Security = no one sees the WRONG PERSON'S data.
# Correctness = no one sees WRONG DATA.
# A confidently wrong CGPA or fee amount is a real harm to a real student.
# This suite recomputes every number INDEPENDENTLY (not using the app's own
# functions) and checks the app agrees. If the app's math ever drifts, this
# catches it.
#
# Usage:  python test_correctness.py

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "student.json"), encoding="utf-8"))


# ---- independent re-implementations (deliberately NOT importing the app's) ----
def indep_grade_point(marks):
    table = [(85, 4.0), (80, 3.7), (75, 3.3), (70, 3.0), (65, 2.7),
             (61, 2.3), (58, 2.0), (55, 1.7), (50, 1.0)]
    for cutoff, pt in table:
        if marks >= cutoff:
            return pt
    return 0.0


def indep_cgpa(data):
    tp = tc = 0
    for sem in data["semesters"].values():
        for c in sem["courses"]:
            if c.get("final") is None or c.get("mid") is None or c.get("sessional") is None:
                continue
            marks = c["mid"] + c["final"] + c["sessional"]
            tp += indep_grade_point(marks) * c["credit_hours"]
            tc += c["credit_hours"]
    return round(tp / tc, 2) if tc else None


def indep_fees(data):
    total = sum(f["total"] for f in data["fees"])
    paid = sum(f["paid"] for f in data["fees"])
    return total, paid, total - paid


def indep_attendance(data):
    return {a["code"]: round(a["present"] / a["total"] * 100) for a in data["attendance"]}


def run():
    results = []

    def check(name, ok):
        results.append((name, ok))

    # ---- CGPA: engine must equal independent calc ----
    from core.grading import cgpa as engine_cgpa
    ind = indep_cgpa(DATA)
    eng = engine_cgpa(DATA["semesters"])
    check(f"CGPA engine matches independent calc ({ind})", ind == eng)

    # ---- CGPA must appear correctly in the dashboard output ----
    from skills.cgpa_dashboard import cgpa_dashboard
    dash = cgpa_dashboard(DATA, "my cgpa")
    check("CGPA value appears in dashboard", str(ind) in dash)

    # ---- Fees: independent totals must appear in the skill output ----
    from skills.fees import fees_summary
    total, paid, due = indep_fees(DATA)
    fout = fees_summary(DATA, "my fees")
    check(f"fees total correct ({total:,})", f"{total:,}" in fout)
    check(f"fees paid correct ({paid:,})", f"{paid:,}" in fout)
    check(f"fees due correct ({due:,})", f"{due:,}" in fout)

    # ---- Attendance: each percentage must appear ----
    from skills.attendance import attendance_summary
    aout = attendance_summary(DATA, "attendance")
    for code, pct in indep_attendance(DATA).items():
        check(f"attendance {code} = {pct}%", f"{pct}%" in aout)

    # ---- Attendance: the <75% course must be flagged LOW ----
    # The app flags by course TITLE (more student-friendly than the code),
    # so we verify the title appears in the low-attendance warning.
    title_by_code = {a["code"]: a.get("title", a["code"]) for a in DATA["attendance"]}
    low_courses = [c for c, p in indep_attendance(DATA).items() if p < 75]
    for c in low_courses:
        title = title_by_code.get(c, c)
        check(f"low-attendance course '{title}' is flagged", title in aout)

    # ---- Grade boundaries: spot-check the scale is exact ----
    from core.grading import marks_to_grade
    boundary_checks = [
        (85, "A"), (84, "A-"), (80, "A-"), (79, "B+"), (50, "D"), (49, "F"),
    ]
    for marks, expected_grade in boundary_checks:
        check(f"marks {marks} -> {expected_grade}", marks_to_grade(marks) == expected_grade)

    # ---- Incomplete semester must NOT produce a fake GPA ----
    # (tested with a synthetic incomplete semester so it doesn't depend on the
    #  demo dataset, which may be a fully-completed student.)
    from core.grading import semester_gpa
    incomplete = [
        {"code": "X", "title": "X", "credit_hours": 3, "mid": 20, "final": None, "sessional": 18},
        {"code": "Y", "title": "Y", "credit_hours": 3, "mid": 22, "final": 44, "sessional": 22},
    ]
    check("incomplete semester returns no GPA", semester_gpa(incomplete) is None)

    # ---- report ----
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        if not ok:
            print(f"[FAIL] {name}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else f"— {len(results) - passed} WRONG ANSWER(S)")
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
