# test_dos.py — DEPARTMENT 6: does the agent resist floods and abuse?
#
# PLAIN ENGLISH:
# A Denial-of-Service (DoS) attack tries to overwhelm the server so real students
# can't get through — by flooding it with requests or sending giant payloads.
# This suite checks the APPLICATION-LAYER defenses: rate limiting, request-size
# caps, and safe handling of malformed input.
#
# IMPORTANT LIMIT: code alone cannot stop a large DISTRIBUTED attack. Real DDoS
# protection lives in front of the app (Cloudflare / reverse proxy / firewall)
# and must be part of the BUITEMS deployment. This suite verifies what the code
# itself is responsible for.
#
# Usage:  python test_dos.py

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if "groq" not in sys.modules:
    sys.modules["groq"] = types.SimpleNamespace(Groq=lambda **k: None)

import server


def run():
    results = []

    def check(name, ok):
        results.append((name, ok))

    client = server.app.test_client()

    # ---- rate limiting: a flood must start getting blocked (429) ----
    server._hits.clear()
    blocked = 0
    for _ in range(server._RATE_MAX + 15):
        r = client.post("/chat", json={"message": "my cgpa"})
        if r.status_code == 429:
            blocked += 1
    check("flood gets rate-limited (429s appear)", blocked > 0)

    # ---- allowed count should respect the configured max ----
    server._hits.clear()
    allowed = 0
    for _ in range(server._RATE_MAX + 5):
        r = client.post("/chat", json={"message": "my cgpa"})
        if r.status_code == 200:
            allowed += 1
    check(f"allowed requests capped near limit ({allowed}<= {server._RATE_MAX})",
          allowed <= server._RATE_MAX)

    # ---- oversized single payload rejected fast (413), not processed ----
    server._hits.clear()
    huge = "a" * 1_000_000
    r = client.post("/chat", json={"message": huge})
    check("oversized payload rejected (413)", r.status_code == 413)

    # ---- message length capped internally even if under body limit ----
    server._hits.clear()
    long_msg = "cgpa " * 300   # ~1500 chars, under body limit but long
    r = client.post("/chat", json={"message": long_msg})
    check("long-but-legal message handled without crash", r.status_code == 200)

    # ---- malformed bodies never crash the server ----
    server._hits.clear()
    for bad in [None, {}, {"message": None}, {"message": 123}, {"notmessage": "x"}]:
        r = client.post("/chat", json=bad)
        if r.status_code >= 500:
            check(f"malformed body crashes: {bad}", False)
            break
    else:
        check("malformed bodies never crash (no 500s)", True)

    # ---- debug mode must be OFF for production safety ----
    # (we can't read app.run args, but we assert debug isn't force-enabled)
    check("app not running in forced debug mode", not server.app.debug)

    # ---- report ----
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        if not ok:
            print(f"[FAIL] {name}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else f"— {len(results) - passed} GAP(S)")
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
