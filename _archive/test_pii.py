# test_pii.py — PHASE 2: PII boundary. No real student data may reach Groq.
#
# PLAIN ENGLISH:
# When a student asks in Roman Urdu, their reply (which contains name, CGPA, fee
# amounts) is translated by Groq — a third-party US service. This test intercepts
# the EXACT text that would be sent to Groq and asserts it contains NONE of the
# real personal data — only masked placeholders. It also confirms the real values
# are correctly restored in the final answer the student sees.
#
# Usage:  python test_pii.py

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# We capture whatever gets sent to Groq by stubbing the client.
_CAPTURED = {"sent": []}


class _FakeResp:
    class _Choice:
        class _Msg:
            content = ""
        message = _Msg()
    choices = [_Choice()]


class _FakeClient:
    def __init__(self, *a, **k):
        pass

    class chat:
        class completions:
            @staticmethod
            def create(model, messages, temperature):
                # record every message content that would be sent to Groq
                for m in messages:
                    _CAPTURED["sent"].append(m.get("content", ""))
                # echo the user text back as the "translation" (keeps placeholders)
                user_text = messages[-1]["content"]
                r = _FakeResp()
                r.choices[0].message.content = user_text.replace("TEXT:\n", "")
                return r


sys.modules["groq"] = types.SimpleNamespace(Groq=_FakeClient)

from core.roman_urdu import to_roman_urdu
from core.pii import mask_pii, unmask_pii, contains_placeholder


# A realistic reply with lots of PII.
SENSITIVE_REPLY = (
    "Your CGPA — Arsalan Khan Nasir\n"
    "Your overall CGPA: 3.28\n"
    "You still need to pay Rs 39,415 before the due date.\n"
    "| Subject | Total | Grade |\n"
    "| Object Oriented Programming | 87 | A |"
)

SECRETS = ["Arsalan Khan Nasir", "Arsalan", "Nasir", "3.28", "39,415", "39415", "87"]


def run():
    results = []

    def check(name, ok):
        results.append((name, ok))

    _CAPTURED["sent"].clear()
    final = to_roman_urdu(SENSITIVE_REPLY, student_name="Arsalan Khan Nasir")

    # everything that was "sent to Groq"
    sent_blob = "\n".join(_CAPTURED["sent"])

    # 1) NONE of the secrets may appear in what was sent to Groq
    for secret in SECRETS:
        check(f"'{secret}' NOT sent to Groq", secret not in sent_blob)

    # 2) the masked text actually reached Groq (placeholders present) — proves
    #    masking ran, not that the call was skipped
    check("masked placeholders were sent to Groq", contains_placeholder(sent_blob))

    # 3) the FINAL answer shown to the student has the real values restored
    check("final answer restores name", "Arsalan Khan Nasir" in final)
    check("final answer restores CGPA 3.28", "3.28" in final)
    check("final answer restores fee 39,415", "39,415" in final)

    # 4) no leftover placeholders in the final answer
    check("no leftover placeholders in final answer", not contains_placeholder(final))

    # 5) masking unit check on numbers-only text
    masked, mapping = mask_pii("CGPA 4.00 and 1,200 marks", student_name=None)
    check("standalone numbers get masked", "4.00" not in masked and "1,200" not in masked)
    check("numbers restore exactly", unmask_pii(masked, mapping) == "CGPA 4.00 and 1,200 marks")

    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        if not ok:
            print(f"[FAIL] {name}")
    print("=" * 60)
    print(f"TOTAL: {passed}/{len(results)} passed",
          "— ALL GREEN" if passed == len(results) else f"— {len(results) - passed} PII LEAK(S)")
    print("=" * 60)
    return passed == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
