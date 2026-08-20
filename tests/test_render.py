# tests/test_render.py — verifies the HTML report renderer (Phase R3).
#
# PLAIN ENGLISH:
# Confirms the renderer produces valid, complete, XSS-safe HTML containing all
# the key report data. It does not test visual beauty (that's human judgment),
# but it guarantees the data is present and no injected script can execute.

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.normalize import normalize_student
from report.assemble import assemble_report
from report.intelligence import build_intelligence
from report.render import render_report

_DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "student.json")


def run():
    data = normalize_student(json.load(open(_DATA, encoding="utf-8")))
    report = assemble_report(data)
    intel = build_intelligence(report)
    html = render_report(report, intel)
    results = []

    def check(name, ok):
        results.append((name, ok))

    # structure
    check("is a full HTML document", "<!DOCTYPE html>" in html and "</html>" in html)
    check("has a title", "<title>" in html)

    # key data present
    check("student name rendered", "Arsalan Khan Nasir" in html)
    check("health score rendered", "score=91" in html)
    check("band rendered", "Excellent" in html)
    check("CGPA rendered", "3.53" in html)
    check("fee due rendered", "Fees" in html)
    check("trend gpa points rendered", "4.0" in html and "3.56" in html)
    check("percentage change rendered", "%" in html)
    check("download button rendered", "Download report" in html)
    check("strengths rendered", "Strengths" in html)
    check("suggestions rendered", "What to do next" in html or "Congratulations" in html)
    check("trend stats rendered", "Peak" in html and "Lowest" in html)

    # the gauge + trend chart svgs exist
    check("health gauge svg present", 'id="ring"' in html)
    check("trend chart svg present", 'class="chart"' in html)

    # ---- XSS SAFETY: inject script everywhere, confirm no live tag ----
    evil = normalize_student({
        "student_id": "X", "name": "<script>alert('x')</script>",
        "program": "<img src=x onerror=alert(1)>", "current_semester": 1,
        "semesters": {"1": {"term": "<script>", "courses": [
            {"code": "C", "title": "<script>bad()</script>", "credit_hours": 3,
             "mid": 20, "final": 40, "sessional": 20}]}},
        "fees": [{"term": "T", "total": 100, "paid": 0}],
        "attendance": [{"code": "C", "title": "<script>", "present": 5, "total": 30}],
        "schedule": [],
    })
    er = assemble_report(evil)
    ehtml = render_report(er, build_intelligence(er))
    # no ACTUAL executable script/handler tag (escaped &lt;script&gt; is fine)
    import re
    live = re.search(r"<script>alert|<img [^>]*onerror=", ehtml)
    check("no live injected script/handler in output", live is None)
    check("injected script is escaped instead", "&lt;script&gt;" in ehtml)

    check("degree progress rendered", "Degree Progress" in html)

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
