# tests_fixtures.py — the ATTACK RANGE: a fingerprinted multi-student database.
#
# PLAIN ENGLISH:
# We build a fake portal with THREE students. One is the "logged-in" user
# (the attacker's own account). The other two are VICTIMS whose private data
# must never appear in any response. Their data is "fingerprinted" with unique
# canary values — strings/numbers that appear NOWHERE else — so if any leak
# happens through any path, we spot the fingerprint instantly.
#
# A "canary" is a unique marker planted in data that should never be exposed.
# If the canary ever shows up in output, we KNOW there was a leak, and exactly
# whose data leaked.

# Canary values — deliberately weird and unique so a simple substring search
# can detect them if they ever escape.
CANARY_NAME_B   = "ZZ_VICTIM_BRAVO_CANARY_ZZ"
CANARY_NAME_C   = "ZZ_VICTIM_CHARLIE_CANARY_ZZ"
CANARY_FEE_B    = 777333        # a fee number that appears nowhere else
CANARY_FEE_C    = 888444
CANARY_ID_B     = "B0000001"
CANARY_ID_C     = "C0000002"

# All canary values, for the leak scanner to check against.
ALL_CANARIES = [
    CANARY_NAME_B, CANARY_NAME_C,
    str(CANARY_FEE_B), str(CANARY_FEE_C), f"{CANARY_FEE_B:,}", f"{CANARY_FEE_C:,}",
    CANARY_ID_B, CANARY_ID_C,
]


def _victim(student_id, name, fee):
    return {
        "student_id": student_id,
        "name": name,
        "program": "BS Secret Program",
        "current_semester": 3,
        "semesters": {
            "1": {"term": "Fall 2024", "courses": [
                {"code": "SEC 101", "title": "Secret Course", "credit_hours": 3,
                 "mid": 25, "final": 50, "sessional": 25},
            ]},
        },
        "fees": [{"term": "Fall 2024", "total": fee, "paid": 0}],
        "attendance": [{"code": "SEC 101", "title": "Secret Course", "present": 1, "total": 30}],
        "schedule": [{"code": "SEC 101", "day": "Monday", "time": "9:00 AM", "room": "SECRET"}],
    }


def build_attack_range(real_student):
    """Return (database, attacker_id, victim_ids).

    real_student: the genuine demo record (the logged-in / attacker account).
    """
    attacker_id = str(real_student["student_id"])
    database = {
        attacker_id: real_student,
        CANARY_ID_B: _victim(CANARY_ID_B, CANARY_NAME_B, CANARY_FEE_B),
        CANARY_ID_C: _victim(CANARY_ID_C, CANARY_NAME_C, CANARY_FEE_C),
    }
    return database, attacker_id, [CANARY_ID_B, CANARY_ID_C]


def scan_for_leak(text):
    """Return the list of canary values found in `text` (empty list = safe)."""
    if text is None:
        return []
    hay = str(text)
    return [c for c in ALL_CANARIES if c in hay]
