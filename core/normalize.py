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


def _num(value, default=0):
    """Return a number, treating None/missing/bad values as the default.
    Booleans are rejected (in Python bool is a subclass of int, so True would
    otherwise sneak through as 1)."""
    if value is None or isinstance(value, bool):
        return default
    try:
        return type(default)(value)
    except (TypeError, ValueError):
        return default


def _mark(value):
    """Clean a single assessment mark. Returns None if not posted, and guards
    against bad portal data: booleans are rejected, and out-of-range values are
    clamped to a sane 0-100 (a mark can never be negative or above 100)."""
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value < 0:
        return 0
    if value > 100:
        return 100
    return value


def _clean_course(c):
    c = c or {}
    return {
        "code": c.get("code") or "",
        "title": c.get("title") or c.get("code") or "Course",
        "credit_hours": _num(c.get("credit_hours"), 0),
        # marks stay None if genuinely not posted yet (skills rely on this to
        # detect "result not ready"), but never a broken/garbage/out-of-range value.
        "mid": _mark(c.get("mid")),
        "final": _mark(c.get("final")),
        "sessional": _mark(c.get("sessional")),
    }


def _clean_fee(f):
    f = f or {}
    return {
        "term": f.get("term") or "—",
        "total": _num(f.get("total"), 0),
        "paid": _num(f.get("paid"), 0),
    }


def _clean_attendance(a):
    a = a or {}
    return {
        "code": a.get("code") or "",
        "title": a.get("title") or a.get("code") or "Course",
        "present": _num(a.get("present"), 0),
        "total": _num(a.get("total"), 0),
    }


def _clean_schedule(s):
    s = s or {}
    return {
        "code": s.get("code") or "",
        "title": s.get("title") or s.get("code") or "Course",
        "day": s.get("day") or "",
        "time": s.get("time") or "",
        "room": s.get("room") or "",
    }


def normalize_student(record):
    """Return a record guaranteed to have a complete, safe shape.

    Missing keys are added, None values are replaced with safe defaults, and
    lists are guaranteed to be lists. Skills that receive a normalized record
    never have to defend against missing/None fields.
    """
    record = record or {}

    semesters = {}
    for sem_id, sem in (record.get("semesters") or {}).items():
        sem = sem or {}
        semesters[sem_id] = {
            "term": sem.get("term") or "—",
            "courses": [_clean_course(c) for c in (sem.get("courses") or [])],
        }

    return {
        "student_id": str(record.get("student_id") or ""),
        "name": record.get("name") or "Student",
        "program": record.get("program") or "",
        "current_semester": _num(record.get("current_semester"), 1),
        # total semesters in the program (8 for a 4-year, 10 for a 5-year degree).
        # Defaults to 8 if not given.
        "program_length": _num(record.get("program_length"), 8),
        # True once the student has completed the degree. Kept through
        # normalization so the report can switch to a retrospective tone
        # (no "improve your CGPA" advice for someone who has graduated).
        "graduated": bool(record.get("graduated")),
        "semesters": semesters,
        "fees": [_clean_fee(f) for f in (record.get("fees") or [])],
        "attendance": [_clean_attendance(a) for a in (record.get("attendance") or [])],
        "schedule": [_clean_schedule(s) for s in (record.get("schedule") or [])],
    }
