# test_goal_planner.py — skill-level tests for the CGPA goal planner.
#
# The router stress test only checks ROUTING (does a message reach the goal skill).
# This checks the SKILL ITSELF: does it correctly extract the target numbers?
# Run alongside stress_test.py — routing correct + extraction correct = working feature.
#
# Usage:  python test_goal_planner.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.goal_planner import _find_goals


# (message, expected_goals) — expected_goals is a list of (value, semester_or_None)
CASES = [
    # previously broken: number with no 'cgpa'/'semester' anchor nearby
    ("is it realistic to finish with a 3.7", [(3.7, None)]),
    ("can i still hit 3.9 before i graduate", [(3.9, None)]),
    ("what average do i need for a 3.6 overall", [(3.6, None)]),

    # previously broken: multiple bare numbers, only first was caught
    ("give me a target for a 3.5 3.6 3.7 3.8 3.9 cgpa",
     [(3.5, None), (3.6, None), (3.7, None), (3.8, None), (3.9, None)]),

    # roman urdu goal phrasings
    ("main 3.8 tak pahunch sakta hun kya", [(3.8, None)]),
    ("possible hai ke main 4.0 le lun graduation tak", [(4.0, None)]),

    # regression: these already worked and must keep working
    ("give me a target to graduate with a cgpa of 3.7 to 3.8", [(3.8, None)]),
    ("can i reach 3.5 by semester 5, and also 3.9 by graduation", [(3.5, 5), (3.9, None)]),
    ("what do i need for a 4.0 cgpa by semester 7", [(4.0, 7)]),
    ("i want to graduate with a 3.5", [(3.5, None)]),
]


def run():
    total = len(CASES)
    passed = 0
    for message, expected in CASES:
        got = _find_goals(message)
        ok = (got == expected)
        if ok:
            passed += 1
            print(f"[PASS] {message!r}")
        else:
            print(f"[FAIL] {message!r}")
            print(f"        got={got}")
            print(f"        exp={expected}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} passed",
          "— ALL GREEN" if passed == total else f"— {total - passed} FAILING")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
