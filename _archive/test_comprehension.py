# test_comprehension.py — DEPARTMENT 2: does the agent understand messy human input?
#
# PLAIN ENGLISH:
# Real students type with typos, casual SMS style, mixed English/Urdu, polite
# fluff, and indirect phrasing. A demo works on clean input; a PRODUCT must
# understand mess. This suite checks the router still picks the right skill when
# the input is realistically messy.
#
# Usage:  python test_comprehension.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.router import route


CASES = [
    # typos & misspellings
    ("wht is my cgpaa", "cgpa"),
    ("show my atendance", "attendance"),
    ("my feee status", "fees"),
    ("reslt dikhao", "report_card"),
    ("my resalt please", "report_card"),

    # casual / SMS style
    ("how m i doing", "cgpa"),
    ("hws my attendance", "attendance"),
    ("cgpa?", "cgpa"),
    ("fees?", "fees"),

    # polite fluff around the real question
    ("hi can you please tell me my cgpa thanks", "cgpa"),
    ("sorry to bother but what is my attendance", "attendance"),
    ("could you kindly show my result", "report_card"),

    # mixed english + roman urdu
    ("mera cgpa kya hai", "cgpa"),
    ("meri fees kitni hai bhai", "fees"),
    ("attendance kitni hai meri", "attendance"),
    ("bhai result dikha do", "report_card"),

    # scrambled word order
    ("cgpa my whats", "cgpa"),
    ("attendance show me the", "attendance"),

    # indirect phrasing
    ("am i doing well academically", "cgpa"),
    ("do i have any dues", "fees"),
    ("will i be allowed to sit exams", "attendance"),
]


def run():
    total = len(CASES)
    passed = 0
    for message, expected in CASES:
        got, _lang = route(message)
        ok = (got == expected)
        if ok:
            passed += 1
        else:
            print(f"[FAIL] want={expected:<12} got={got:<12} <- {message!r}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} passed",
          "— ALL GREEN" if passed == total else f"— {total - passed} comprehension gap(s)")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
