# report/assemble.py — THE REPORT-ASSEMBLY ENGINE.
#
# PLAIN ENGLISH:
# This runs the whole academic audit at once and returns ONE structured report
# object (a plain dict of facts and numbers). It does NOT produce HTML — the UI
# layer turns this data into the visual report later. Keeping data separate from
# display means we can test the logic without a browser and restyle the report
# without touching the math.
#
# Every number here comes from the proven core grading functions.

from core.grading import (
    total_marks, marks_to_grade, course_grade_point, semester_gpa, cgpa,
)


def _round1(x):
    return round(x, 1) if x is not None else None


def _round2(x):
    return round(x, 2) if x is not None else None


def build_semester_section(data):
    """Per-semester breakdown: each course with marks, grade, and the semester GPA.
    Incomplete semesters (no posted marks) are marked as in-progress, not scored."""
    semesters = []
    for sem_id in sorted(data.get("semesters", {}), key=lambda s: int(s) if s.isdigit() else 0):
        sem = data["semesters"][sem_id]
        courses = []
        complete = True
        for c in sem.get("courses", []):
            posted = c.get("final") is not None and c.get("mid") is not None
            if not posted:
                complete = False
            marks = total_marks(c) if posted else None
            courses.append({
                "code": c.get("code", ""),
                "title": c.get("title", c.get("code", "Course")),
                "credit_hours": c.get("credit_hours", 0),
                "mid": c.get("mid"),
                "final": c.get("final"),
                "sessional": c.get("sessional"),
                "total": marks,
                "grade": marks_to_grade(marks) if marks is not None else None,
                "grade_point": course_grade_point(c) if posted else None,
            })
        gpa = semester_gpa(sem.get("courses", []))
        semesters.append({
            "semester": sem_id,
            "term": sem.get("term", ""),
            "courses": courses,
            "gpa": _round2(gpa),
            "status": "complete" if complete and gpa is not None else "in_progress",
        })
    return semesters


def build_cgpa_section(data):
    """Overall CGPA + a simple standing band."""
    value = cgpa(data.get("semesters", {}))
    if value is None:
        return {"cgpa": None, "standing": "no_data", "message": "No completed semesters yet."}

    if value >= 3.5:
        standing = "excellent"
    elif value >= 3.0:
        standing = "good"
    elif value >= 2.5:
        standing = "satisfactory"
    elif value >= 2.0:
        standing = "at_risk"
    else:
        standing = "probation"

    return {"cgpa": _round2(value), "standing": standing}


def build_fees_section(data):
    """Fee totals and outstanding dues."""
    fees = data.get("fees", [])
    total = sum((f.get("total") or 0) for f in fees)
    paid = sum((f.get("paid") or 0) for f in fees)
    due = total - paid
    return {
        "total": total,
        "paid": paid,
        "due": due,
        "status": "clear" if due <= 0 else "outstanding",
        "terms": [
            {"term": f.get("term", "—"),
             "total": f.get("total") or 0,
             "paid": f.get("paid") or 0,
             "due": (f.get("total") or 0) - (f.get("paid") or 0)}
            for f in fees
        ],
    }


def build_attendance_section(data):
    """Per-course attendance %, and which courses are below the 75% exam threshold."""
    THRESHOLD = 75
    courses = []
    below = []
    for a in data.get("attendance", []):
        total = a.get("total") or 0
        present = a.get("present") or 0
        pct = round(present / total * 100) if total else None
        entry = {
            "code": a.get("code", ""),
            "title": a.get("title", a.get("code", "Course")),
            "present": present,
            "total": total,
            "percent": pct,
            "eligible": (pct is not None and pct >= THRESHOLD),
        }
        courses.append(entry)
        if pct is not None and pct < THRESHOLD:
            # classes needed to reach the threshold if they attend all remaining
            below.append(entry)
    return {"threshold": THRESHOLD, "courses": courses, "below_threshold": below}


def build_trend_section(data):
    """GPA per completed semester — the data behind the GPA trend chart."""
    points = []
    for sem_id in sorted(data.get("semesters", {}), key=lambda s: int(s) if s.isdigit() else 0):
        gpa = semester_gpa(data["semesters"][sem_id].get("courses", []))
        if gpa is not None:
            points.append({"semester": sem_id,
                           "term": data["semesters"][sem_id].get("term", ""),
                           "gpa": _round2(gpa)})
    # direction reading
    direction = "flat"
    if len(points) >= 2:
        if points[-1]["gpa"] > points[0]["gpa"]:
            direction = "up"
        elif points[-1]["gpa"] < points[0]["gpa"]:
            direction = "down"
    return {"points": points, "direction": direction}


def assemble_report(data):
    """Run every section and return ONE structured report object.

    `data` must already be a normalized, AUTHORIZED student record (the caller
    fetches it through the authorization layer + normalizer first).
    """
    return {
        "student": {
            "name": data.get("name", "Student"),
            "program": data.get("program", ""),
            "current_semester": data.get("current_semester"),
        },
        "cgpa": build_cgpa_section(data),
        "semesters": build_semester_section(data),
        "fees": build_fees_section(data),
        "attendance": build_attendance_section(data),
        "trend": build_trend_section(data),
    }
