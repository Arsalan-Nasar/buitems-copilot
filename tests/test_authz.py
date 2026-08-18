# test_authz.py — AUTHORIZATION TESTS (Phase 0 → Phase 1)
#
# PLAIN-ENGLISH PURPOSE:
# These tests pretend the app is connected to the REAL portal, which has MANY
# students (not just one). They then try to make the system leak data belonging
# to a DIFFERENT student than the one who is "logged in".
#
# RIGHT NOW (Phase 0) these tests are EXPECTED TO FAIL — that failure is the
# proof that the security hole is real. In Phase 1 we build the authorization
# layer, and these same tests must all turn GREEN.
#
# Usage:  python test_authz.py
#
# The rule we are protecting:
#   A logged-in student must ONLY ever be able to read their OWN records —
#   enforced by code, no matter what they type.

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Build a fake "portal database" of MANY students (this mimics real integration).
# ---------------------------------------------------------------------------
def build_fake_portal():
    me = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "student.json"), encoding="utf-8"))
    me_id = me["student_id"]

    # a second student — their data is PRIVATE and must never leak to 'me'
    other = {
        "student_id": "99999",
        "name": "Private Other Student",
        "program": "BS Computer Science",
        "current_semester": 2,
        "semesters": {},
        "fees": [{"term": "Fall 2024", "total": 80000, "paid": 10000}],
        "attendance": [],
        "schedule": [],
    }
    database = {me_id: me, "99999": other}
    return database, me_id, "99999"


# ---------------------------------------------------------------------------
# The authorization function we WANT to exist.
# In Phase 1 we will build a real one. For Phase 0, we try to import it; if it
# doesn't exist yet, that itself is a failing test (the layer is missing).
# ---------------------------------------------------------------------------
def get_authorized_data(database, logged_in_id, requested_id=None):
    """Fetch through the real authorization layer if it exists.

    Returns the record on success, or None if access was correctly refused.
    A refusal (None) for another student's data is the CORRECT, secure outcome.
    """
    try:
        from core.authz import fetch_student_safe
        return fetch_student_safe(database, logged_in_id, requested_id)
    except Exception:
        # No authorization layer at all — simulate the CURRENT naive behavior:
        # the app just returns whatever id is asked for. THIS is the hole.
        target = requested_id or logged_in_id
        return database.get(target)


# ---------------------------------------------------------------------------
# TESTS
# ---------------------------------------------------------------------------
def run():
    database, me_id, other_id = build_fake_portal()
    results = []

    # TEST 1: I can read my own data (must always work)
    mine = get_authorized_data(database, me_id, me_id)
    ok1 = mine is not None and mine["student_id"] == me_id
    results.append(("read my own data works", ok1))

    # TEST 2: I must NOT be able to read another student's data by asking for their id
    stolen = get_authorized_data(database, me_id, other_id)
    ok2 = (stolen is None) or (stolen["student_id"] == me_id)
    results.append(("cannot read another student's data by id", ok2))

    # TEST 3: even a blank/None request must default to ONLY my data, never a leak
    default = get_authorized_data(database, me_id, None)
    ok3 = default is not None and default["student_id"] == me_id
    results.append(("blank request returns only my data", ok3))

    # TEST 4: the returned object must never contain the other student's private fee
    leaked_fee = False
    if stolen and stolen.get("student_id") == other_id:
        leaked_fee = True
    results.append(("other student's private fees never leak", not leaked_fee))

    # ---- report ----
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else "— HOLE STILL OPEN")
    print("=" * 60)
    if passed != len(results):
        print("\nThis FAILURE is expected in Phase 0. It proves the authorization")
        print("hole is real. Phase 1 builds core/authz.py to make these pass.")
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
