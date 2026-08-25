# core/normalize.py — the DATA NORMALIZER (one safe shape for every record).
#
# PLAIN ENGLISH:
# Real portal data is messy — missing fields, None values, absent keys. Instead
# of every skill defending itself (ten places to get wrong), we clean the record
# ONCE, here, right after we fetch it. After normalize_student(), every skill can
# TRUST that the shape is complete and typed correctly. One chokepoint, not ten.
#
# This is the same principle as the authorization layer: fix it in one place that
# everything flows through, so it's impossible to forget.


import math


def _is_bad_float(value):
    """True if value is NaN or infinity — floats that pass isinstance checks but
    break arithmetic and int() conversion. Must be rejected."""
    return isinstance(value, float) and (math.isnan(value) or math.isinf(value))


def _num(value, default=0):
    """Return a number, treating None/missing/bad values as the default.
    Booleans are rejected (in Python bool is a subclass of int, so True would
    otherwise sneak through as 1). NaN/infinity are rejected too."""
    if value is None or isinstance(value, bool) or _is_bad_float(value):
        return default
    try:
        return type(default)(value)
    except (TypeError, ValueError):
        return default


def _mark(value):
    """Clean a single assessment mark. Returns None if not posted, and guards
    against bad portal data: booleans, NaN/infinity, and non-numbers are rejected,
    and out-of-range values are clamped to a sane 0-100."""
    if (value is None or isinstance(value, bool) or _is_bad_float(value)
            or not isinstance(value, (int, float))):
        return None
    if value < 0:
        return 0
    if value > 100:
        return 100
    return value


def _clamp_credits(value):
    """Credit hours for a single course, clamped to a sane range. A course can't
    have negative or absurd credit hours; bad data shouldn't distort GPA weighting."""
    n = _num(value, 0)
    if n < 0:
        return 0
    if n > 30:          # no single course exceeds this; guards against garbage
        return 30
    return n


def _clean_course(c):
    c = c or {}
    return {
        "code": _text(c.get("code"), ""),
        "title": _text(c.get("title"), "") or _text(c.get("code"), "") or "Course",
        "credit_hours": _clamp_credits(c.get("credit_hours")),
        # marks stay None if genuinely not posted yet (skills rely on this to
        # detect "result not ready"), but never a broken/garbage/out-of-range value.
        "mid": _mark(c.get("mid")),
        "final": _mark(c.get("final")),
        "sessional": _mark(c.get("sessional")),
    }


def _clean_fee(f):
    f = f or {}
    return {
        "term": _text(f.get("term"), "") or "—",
        "total": _num(f.get("total"), 0),
        "paid": _num(f.get("paid"), 0),
    }


def _clean_attendance(a):
    a = a or {}
    return {
        "code": _text(a.get("code"), ""),
        "title": _text(a.get("title"), "") or _text(a.get("code"), "") or "Course",
        "present": _num(a.get("present"), 0),
        "total": _num(a.get("total"), 0),
    }


def _clean_schedule(s):
    s = s or {}
    return {
        "code": _text(s.get("code"), ""),
        "title": _text(s.get("title"), "") or _text(s.get("code"), "") or "Course",
        "day": _text(s.get("day"), ""),
        "time": _text(s.get("time"), ""),
        "room": _text(s.get("room"), ""),
    }


def normalize_student(record):
    """Return a record guaranteed to have a complete, safe shape.

    Missing keys are added, None values are replaced with safe defaults, and
    lists are guaranteed to be lists. Skills that receive a normalized record
    never have to defend against missing/None fields.
    """
    if not isinstance(record, dict):
        record = {}                        # whole record was garbage -> empty shape

    semesters = {}
    raw_semesters = record.get("semesters")
    if not isinstance(raw_semesters, dict):
        raw_semesters = {}                 # semesters wasn't a dict -> empty
    for sem_id, sem in raw_semesters.items():
        sem_id = str(sem_id)               # keys may arrive as ints -> normalise to str
        if not isinstance(sem, dict):
            sem = {}                       # semester wasn't a dict -> treat as empty
        raw_courses = sem.get("courses")
        if not isinstance(raw_courses, list):
            raw_courses = []               # courses wasn't a list -> treat as empty
        semesters[sem_id] = {
            "term": sem.get("term") or "—",
            "courses": [_clean_course(c) for c in raw_courses if isinstance(c, dict)],
        }

    return {
        "student_id": str(record.get("student_id") or ""),
        "name": _text(record.get("name"), "Student"),
        "program": _text(record.get("program"), ""),
        "current_semester": _num(record.get("current_semester"), 1),
        "program_length": _num(record.get("program_length"), 8),
        "graduated": bool(record.get("graduated")),
        "semesters": semesters,
        "fees": [_clean_fee(f) for f in _as_list(record.get("fees")) if isinstance(f, dict)],
        "attendance": [_clean_attendance(a) for a in _as_list(record.get("attendance")) if isinstance(a, dict)],
        "schedule": [_clean_schedule(s) for s in _as_list(record.get("schedule")) if isinstance(s, dict)],
    }


def _text(value, default=""):
    """Guarantee a string. Non-string/None values become the default, so any
    downstream .lower()/.strip()/join on these fields can never crash."""
    if isinstance(value, str):
        return value
    if value is None or isinstance(value, (dict, list, bool)):
        return default
    try:
        return str(value)
    except Exception:
        return default


def _as_list(value):
    """Return value if it's a list, otherwise an empty list. Protects against
    malformed data where a field that should be a list is a string/dict/None."""
    return value if isinstance(value, list) else []
