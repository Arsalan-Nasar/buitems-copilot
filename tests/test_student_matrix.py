# tests/test_student_matrix.py — THE SAFETY NET across all student types.
#
# PLAIN ENGLISH:
# The report serves very different students. This test runs the FULL pipeline
# (normalize -> assemble -> intelligence -> render) for every student type and
# asserts each one behaves correctly. This is what stops "it works for one
# student but breaks for another" bugs from ever shipping again.

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.normalize import normalize_student
from report.assemble import assemble_report
from report.intelligence import build_intelligence
from report.render import render_report
from tests.fixtures.students import ALL_STUDENTS


def _pipeline(data):
    d = normalize_student(data)
    report = assemble_report(d)
    intel = build_intelligence(report)
    html = render_report(report, intel)
    return report, intel, html


def run():
    results = []

    def check(name, ok):
        results.append((name, ok))

    # ---- 1. EVERY student type completes the full pipeline without crashing ----
    for name, data in ALL_STUDENTS.items():
        try:
            report, intel, html = _pipeline(data)
            check(f"{name}: pipeline runs", True)
            check(f"{name}: produces full HTML", "<!DOCTYPE html>" in html)
            check(f"{name}: health score 0-100",
                  intel["health_score"]["score"] is None or
                  0 <= intel["health_score"]["score"] <= 100)
            check(f"{name}: has suggestions", len(intel["suggestions"]) > 0)
            check(f"{name}: has at least one flag", len(intel["flags"]) > 0)
        except Exception as e:
            check(f"{name}: pipeline runs (ERROR: {e})", False)

    # ---- 2. GRADUATED student: NO "improve your CGPA" advice ----
    _, grad_intel, grad_html = _pipeline(ALL_STUDENTS["graduated"])
    grad_sugg = " ".join(grad_intel["suggestions"]).lower()
    check("graduated: no 'improve' advice",
          "improving it would lift" not in grad_sugg and "turn it around" not in grad_sugg)
    check("graduated: mentions congratulations",
          "congratulation" in grad_sugg or "completed" in grad_sugg or "completing" in grad_sugg)
    check("graduated: flag is green (not urgent)",
          all(f["level"] == "green" for f in grad_intel["flags"]))
    check("graduated: standing flags graduated", grad_intel["standing"]["graduated"] is True)

    # ---- 3. PROBATION student: gets urgent standing advice ----
    _, prob_intel, _ = _pipeline(ALL_STUDENTS["probation"])
    prob_sugg = " ".join(prob_intel["suggestions"]).lower()
    check("probation: tier is probation", prob_intel["standing"]["tier"] == "probation")
    check("probation: advises advisor/recovery",
          "advisor" in prob_sugg or "recovery" in prob_sugg or "good-standing" in prob_sugg)
    check("probation: does NOT meet good standing",
          prob_intel["standing"]["meets_good_standing"] is False)

    # ---- 4. WARNING student: borderline messaging ----
    _, warn_intel, _ = _pipeline(ALL_STUDENTS["warning"])
    check("warning: tier is warning", warn_intel["standing"]["tier"] == "warning")

    # ---- 5. HONORS student: recognition ----
    _, hon_intel, _ = _pipeline(ALL_STUDENTS["honors"])
    check("honors: tier is honors", hon_intel["standing"]["tier"] == "honors")
    check("honors: high health score", hon_intel["health_score"]["score"] >= 85)

    # ---- 6. FIRST SEMESTER: no trend talk, encouragement instead ----
    _, first_intel, _ = _pipeline(ALL_STUDENTS["first_semester"])
    first_sugg = " ".join(first_intel["suggestions"]).lower()
    check("first_sem: flagged as first semester",
          first_intel["standing"]["is_first_semester"] is True)
    check("first_sem: no 'trending' talk",
          "trending upward" not in first_sugg and "dipped recently" not in first_sugg)

    # ---- 7. FIVE-YEAR program: degree progress uses 10 semesters ----
    five_report, _, _ = _pipeline(ALL_STUDENTS["five_year"])
    check("five_year: program_length is 10",
          five_report["student"]["program_length"] == 10)

    # ---- 8. FRESH student (no results yet): no crash, no fake CGPA ----
    fresh_report, fresh_intel, _ = _pipeline(ALL_STUDENTS["fresh"])
    check("fresh: CGPA is None (no fake number)", fresh_report["cgpa"]["cgpa"] is None)
    check("fresh: standing tier no_data", fresh_intel["standing"]["tier"] == "no_data")
    check("fresh: health score is pending (not a low number)",
          fresh_intel["health_score"].get("pending") is True)
    check("fresh: band is not 'At Risk'",
          fresh_intel["health_score"]["band"] != "At Risk")
    check("fresh: still produces suggestions", len(fresh_intel["suggestions"]) > 0)

    # ---- 9. XSS safety holds for every student type ----
    import re
    for name, data in ALL_STUDENTS.items():
        evil = dict(data)
        evil["name"] = "<script>alert('x')</script>"
        _, _, html = _pipeline(evil)
        live = re.search(r"<script>alert", html)
        check(f"{name}: XSS-safe (name escaped)", live is None)

    passed = sum(1 for _, ok in results if ok)
    for nm, ok in results:
        if not ok:
            print(f"[FAIL] {nm}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else f"— {len(results) - passed} FAIL")
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
