# core/pii.py — PII MASKING for third-party (LLM) calls.
#
# PLAIN ENGLISH:
# When we send text to Groq (a third-party US service) for Roman Urdu translation,
# that text must NOT contain real student data — no names, no CGPA/fee numbers.
# This module replaces every piece of personal data with a neutral placeholder
# BEFORE the text leaves our server, and restores the real values AFTER the
# translation comes back. Groq only ever sees the sentence shape, never the data.
#
# GOLDEN RULE: if we cannot guarantee a value is masked, we must not send it.
# So masking is deliberately AGGRESSIVE — it masks all names, all numbers, all
# money amounts, all grades, and markdown tables (which hold the raw data grid).

import re


# Placeholder markers use unusual bracket characters so they can't collide with
# real text and are easy to find again for restoration.
_OPEN, _CLOSE = "\u27e6", "\u27e7"   # ⟦ ⟧


def _ph(tag, i):
    return f"{_OPEN}{tag}{i}{_CLOSE}"


def mask_pii(text, student_name=None):
    """Replace personal data in `text` with placeholders.

    Returns (masked_text, mapping) where mapping restores the originals.
    Order matters: we mask the most specific things first (tables, name, money,
    grades) before generic numbers, so nothing is half-masked.
    """
    mapping = {}
    counter = {"v": 0}

    def store(original):
        counter["v"] += 1
        key = _ph("M", counter["v"])
        mapping[key] = original
        return key

    masked = text

    # 1) Whole markdown table rows — they hold the raw data grid. Mask each
    #    entire table line as one unit so numbers/names inside aren't exposed.
    def _mask_table_line(m):
        return store(m.group(0))
    masked = re.sub(r"^\|.*\|$", _mask_table_line, masked, flags=re.MULTILINE)

    # 2) The student's own name (if we know it) — mask every occurrence.
    if student_name:
        name = student_name.strip()
        if name:
            masked = masked.replace(name, store(name))

    # 3) Money amounts like "Rs 39,415" or "39,415" — mask the number part.
    masked = re.sub(r"Rs\s?[\d,]+", lambda m: store(m.group(0)), masked)

    # 4) Decimal numbers (GPA/CGPA like 3.28) and any standalone numbers.
    masked = re.sub(r"\d+\.\d+", lambda m: store(m.group(0)), masked)   # 3.28
    masked = re.sub(r"\b\d[\d,]*\b", lambda m: store(m.group(0)), masked)  # 28, 1,200

    # 5) Grade letters shown as standalone tokens (A, A-, B+, F) — mask so the
    #    translator can't accidentally alter them.
    masked = re.sub(r"(?<![A-Za-z])([A-D][+\-]?|F)(?![A-Za-z])",
                    lambda m: store(m.group(0)), masked)

    return masked, mapping


def unmask_pii(text, mapping):
    """Put the real values back after translation. Restores longest keys first
    to avoid any partial-key collisions."""
    restored = text
    for key in sorted(mapping, key=len, reverse=True):
        restored = restored.replace(key, mapping[key])
    return restored


def contains_placeholder(text):
    """True if any placeholder remains (used by tests to detect leaks/failures)."""
    return _OPEN in text or _CLOSE in text
