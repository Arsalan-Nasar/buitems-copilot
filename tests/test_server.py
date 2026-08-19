# tests/test_server.py — verifies the report server (Phase R4) end-to-end.
#
# PLAIN ENGLISH:
# Confirms the enhancement-tab server works and is secure:
#   - opening /report generates the full HTML report
#   - a student can only ever get their OWN data (authorization holds)
#   - security headers are present
#   - abuse is rate-limited
#   - malformed / error conditions never leak internals

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server


def run():
    results = []

    def check(name, ok):
        results.append((name, ok))

    client = server.app.test_client()
    server._hits.clear()

    # ---- 1. opening /report generates the report ----
    r = client.get("/report")
    body = r.get_data(as_text=True)
    check("/report returns 200", r.status_code == 200)
    check("report contains health score", "Academic Health Score" in body)
    check("report contains the student name", "Arsalan" in body)
    check("report contains GPA trend", "GPA Trend" in body)
    check("report is full HTML", "<!DOCTYPE html>" in body)

    # ---- 2. security headers present ----
    for h in ["Content-Security-Policy", "X-Frame-Options",
              "X-Content-Type-Options", "Strict-Transport-Security"]:
        check(f"header {h} present", h in r.headers)

    # ---- 3. AUTHORIZATION: add a second student, confirm the logged-in one
    #        can never get the other's data through the report ----
    server._hits.clear()
    server.DATABASE["99999"] = {
        "student_id": "99999", "name": "ZZ_OTHER_STUDENT_ZZ", "program": "CS",
        "current_semester": 1, "semesters": {},
        "fees": [{"term": "F", "total": 777333, "paid": 0}],
        "attendance": [], "schedule": [],
    }
    r2 = client.get("/report")
    body2 = r2.get_data(as_text=True)
    check("other student's name never appears", "ZZ_OTHER_STUDENT_ZZ" not in body2)
    check("other student's fee never appears", "777,333" not in body2 and "777333" not in body2)
    check("logged-in student's own report still shows", "Arsalan" in body2)
    # restore
    del server.DATABASE["99999"]

    # ---- 4. rate limiting ----
    server._hits.clear()
    codes = [client.get("/report").status_code for _ in range(server._RATE_MAX + 10)]
    check("rate limiting kicks in (429 appears)", 429 in codes)

    # ---- 5. health endpoint works and leaks no data ----
    server._hits.clear()
    hr = client.get("/health")
    check("/health returns ok", hr.status_code == 200 and "ok" in hr.get_data(as_text=True))

    # ---- 6. render failure never leaks internals ----
    # temporarily break the renderer to simulate an error
    import report.render as rr
    original = rr.render_report
    server_render_backup = server.render_report
    def boom(*a, **k):
        raise RuntimeError("SECRET_INTERNAL_DETAIL")
    server.render_report = boom
    server._hits.clear()
    er = client.get("/report")
    check("render error returns 500", er.status_code == 500)
    check("render error hides internal detail",
          "SECRET_INTERNAL_DETAIL" not in er.get_data(as_text=True))
    server.render_report = server_render_backup

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
