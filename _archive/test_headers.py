# test_headers.py — DEPARTMENT 5 (web): HTTP security headers.
#
# PLAIN ENGLISH:
# Browsers can enforce extra protections IF the server tells them to, via special
# response headers. Missing them leaves the door open to clickjacking, MIME abuse,
# referrer leakage, and gives up a second layer of XSS defense. This suite checks
# every required header is present on every response.
#
# Usage:  python test_headers.py

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if "groq" not in sys.modules:
    sys.modules["groq"] = types.SimpleNamespace(Groq=lambda **k: None)

import server

REQUIRED = {
    "Content-Security-Policy": ["default-src 'self'", "frame-ancestors 'none'"],
    "X-Frame-Options": ["DENY"],
    "X-Content-Type-Options": ["nosniff"],
    "Referrer-Policy": ["strict-origin"],
    "Strict-Transport-Security": ["max-age="],
}


def run():
    client = server.app.test_client()
    results = []

    def check(name, ok):
        results.append((name, ok))

    # test on multiple routes to be sure the after_request hook covers all
    responses = {
        "/": client.get("/"),
        "/guide": client.get("/guide"),
        "/chat": client.post("/chat", json={"message": "my cgpa"}),
    }

    for path, r in responses.items():
        for header, must_contain in REQUIRED.items():
            present = header in r.headers
            check(f"{path}: {header} present", present)
            if present:
                val = r.headers[header]
                for token in must_contain:
                    check(f"{path}: {header} contains {token!r}", token in val)

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        if not ok:
            print(f"[FAIL] {name}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else f"— {len(results) - passed} MISSING")
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
