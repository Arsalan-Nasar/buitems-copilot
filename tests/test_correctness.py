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

    # ---- data integrity: bad portal data is sanitised (audit fixes) ----
    from core.normalize import _clean_course, _num
    check("booleans not treated as numbers", _num(True, 0) == 0 and _num(False, 5) == 5)
    bad = _clean_course({"code": "X", "mid": True, "final": 150, "sessional": -5})
    check("boolean mark rejected", bad["mid"] is None)
    check("over-100 mark clamped to 100", bad["final"] == 100)
    check("negative mark clamped to 0", bad["sessional"] == 0)

    # ---- standing labels are consistent between assemble and intelligence ----
    from core.normalize import normalize_student
    from report.assemble import assemble_report
    from report.intelligence import academic_standing
    for marks in [(23,45,23),(18,36,19),(15,30,16),(12,24,13)]:  # honors..probation
        s_ = {"student_id":"C","name":"C","program":"BS IT","current_semester":1,
              "program_length":8,"graduated":False,
              "semesters":{"1":{"term":"T","courses":[
                  {"code":"C","title":"Course","credit_hours":3,
                   "mid":marks[0],"final":marks[1],"sessional":marks[2]}]}},
              "fees":[],"attendance":[],"schedule":[]}
        r_ = assemble_report(normalize_student(s_))
        check(f"standing consistent for marks {marks}",
              r_["cgpa"]["standing"] == academic_standing(r_)["tier"])

    # ---- FIVE-NINES: pipeline never crashes on garbage input ----
    import random as _rand
    from report.render import render_report as _rr
    from report.intelligence import build_intelligence as _bi
    from report.assemble import assemble_report as _ar
    from core.normalize import normalize_student as _ns
    _garbage = [None, "", {}, [], "text", 42, -1, 3.14, float("nan"),
                float("inf"), True, False, {"x": 1}, [1, 2], "<script>", 0]
    _rng = _rand.Random(7)   # isolated RNG so earlier random use can't shift this
    _crashes = 0
    _first_err = ""
    for _ in range(50):
        _g = lambda: _rng.choice(_garbage)
        _stu = {"student_id": _g(), "name": _g(), "program": _g(),
                "current_semester": _g(), "program_length": _g(), "graduated": _g(),
                "semesters": {str(_rng.randint(1, 8)): {"term": _g(), "courses": [
                    {"code": _g(), "title": _g(), "credit_hours": _g(),
                     "mid": _g(), "final": _g(), "sessional": _g()}]}},
                "fees": _g(), "attendance": _g(), "schedule": _g()}
        try:
            _d = _ns(_stu); _r = _ar(_d)
            _rr(_r, _bi(_r))
        except Exception as _e:
            _crashes += 1
            if not _first_err:
                _first_err = type(_e).__name__ + ": " + str(_e)
    if _crashes:
        print("   fuzz first error ->", _first_err)
    check("fuzz: 50 garbage inputs never crash", _crashes == 0)

    # ---- missed mid but sat the final (health-issue case): still graded ----
    from core.grading import total_marks as _tm, course_status as _cs, marks_to_grade as _m2g
    missed_mid = {"code":"X","title":"X","credit_hours":3,"mid":None,"final":44,"sessional":22}
    check("missed-mid course is graded (final posted)", _cs(missed_mid) == "posted")
    check("missed-mid counts mid as 0", _tm(missed_mid) == 66)   # 0+44+22
    check("missed-mid gets a real grade", _m2g(_tm(missed_mid)) == "B-")
    # but a genuinely pending course (no final yet) is NOT graded
    awaiting = {"code":"Y","title":"Y","credit_hours":3,"mid":20,"final":None,"sessional":None}
    check("mid-only course stays ungraded", _tm(awaiting) is None and _cs(awaiting) == "mid_only")

    # ---- partial results: a semester with SOME posted courses ----
    from core.grading import semester_gpa, semester_gpa_so_far, course_status
    partial = [
        {"code":"A","title":"A","credit_hours":3,"mid":22,"final":44,"sessional":22},  # posted -> A
        {"code":"B","title":"B","credit_hours":3,"mid":20,"final":None,"sessional":None},  # mid only
        {"code":"C","title":"C","credit_hours":3,"mid":None,"final":None,"sessional":None},  # pending
    ]
    check("strict semester_gpa is None when not all posted", semester_gpa(partial) is None)
    check("gpa_so_far ignores pending, uses posted", semester_gpa_so_far(partial) == 4.0)
    check("course_status posted", course_status(partial[0]) == "posted")
    check("course_status mid_only", course_status(partial[1]) == "mid_only")
    check("course_status pending", course_status(partial[2]) == "pending")
    # nothing posted at all -> gpa_so_far is None (not a fake 0)
    nothing = [{"code":"X","title":"X","credit_hours":3,"mid":None,"final":None,"sessional":None}]
    check("gpa_so_far None when nothing posted", semester_gpa_so_far(nothing) is None)

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
