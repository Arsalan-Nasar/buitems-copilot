# core/grading.py — THE math engine. Real BUITEMS scheme: Mid 25 + Final 50 + Sessional 25 = 100
# Every feature uses these functions, so the numbers are always correct and consistent.
#
# ---------------------------------------------------------------------------
# GRADING SCALE — VERIFIED against BUITEMS official policy (19 Aug 2026).
# Source: BUITEMS official grade table (confirmed from the portal grading UI).
#
# Marks -> Grade (official bands):
#     A  85-100 | A- 80-84 | B+ 75-79 | B 70-74 | B- 65-69
#     C+ 61-64  | C  58-60 | C- 55-57 | D 50-54 | F 0-49
#   (BUITEMS has NO "A+" grade — A is the top grade, starting at 85.)
#
# Grade -> Grade Point (standard 4.0 scale, confirmed used by BUITEMS):
#     A 4.0 | A- 3.7 | B+ 3.3 | B 3.0 | B- 2.7
#     C+ 2.3 | C 2.0 | C- 1.7 | D 1.0 | F 0.0
#
# If BUITEMS ever revises its policy, update ONLY the two mappings below
# (marks_to_grade and grade_to_point) — everything else derives from them.
# ---------------------------------------------------------------------------


def total_marks(course):
    """Total mark for a course (out of 100).

    The FINAL is what completes a course. BUITEMS posts the sessional together
    with the final, and the mid comes earlier. So:
      - once the FINAL is posted, the course is graded. A missing mid or sessional
        is treated as 0 (the student missed that component — e.g. skipped the mid
        for health reasons but sat the final). They still get a real grade.
      - if the final isn't posted yet, the result isn't complete -> None.
    """
    final = course.get("final")
    if final is None:
        return None              # no final yet -> course not graded
    mid = course.get("mid") or 0        # missing component counts as 0
    sessional = course.get("sessional") or 0
    return mid + final + sessional


def marks_to_grade(marks):
    """Real BUITEMS grade scale (out of 100)."""
    if marks is None:
        return "—"
    if marks >= 85: return "A"
    elif marks >= 80: return "A-"
    elif marks >= 75: return "B+"
    elif marks >= 70: return "B"
    elif marks >= 65: return "B-"
    elif marks >= 61: return "C+"
    elif marks >= 58: return "C"
    elif marks >= 55: return "C-"
    elif marks >= 50: return "D"
    else: return "F"


def grade_to_point(grade):
    """Grade letter -> grade point (4.0 scale)."""
    points = {
        "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0, "C-": 1.7, "D": 1.0, "F": 0.0,
    }
    return points.get(grade, 0.0)


def course_grade_point(course):
    """Full chain for one course: marks -> grade -> point. None if incomplete."""
    marks = total_marks(course)
    if marks is None:
        return None
    return grade_to_point(marks_to_grade(marks))


def course_status(course):
    """Where a course is in its result lifecycle.

      'posted'    -> FINAL is in (course is graded). A missed mid/sessional still
                     counts — the student gets a real grade (e.g. skipped the mid
                     but sat the final).
      'mid_only'  -> mid is in but final isn't yet (awaiting final result)
      'pending'   -> nothing posted yet
    """
    mid = course.get("mid")
    final = course.get("final")
    if final is not None:
        return "posted"          # final posted -> graded regardless of mid
    if mid is not None:
        return "mid_only"
    return "pending"


def semester_gpa(courses):
    """STRICT semester GPA: only returns a number when EVERY course is fully
    posted (the official end-of-semester GPA). Returns None if any course is
    still incomplete."""
    total_points = 0.0
    total_credits = 0
    for c in courses:
        gp = course_grade_point(c)
        if gp is None:
            return None          # semester not finished -> no official GPA yet
        ch = c.get("credit_hours")
        if not ch:               # missing/zero credit hours -> skip, don't crash
            continue
        total_points += gp * ch
        total_credits += ch
    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)


def semester_gpa_so_far(courses):
    """LIVE GPA from the courses posted SO FAR, ignoring pending ones.

    This is what a student wants to see mid-semester: "based on results already
    out, here's where I stand." Unlike semester_gpa(), one un-posted course does
    NOT hide the grades that ARE in. Returns None only if NOTHING is posted yet.
    """
    total_points = 0.0
    total_credits = 0
    for c in courses:
        gp = course_grade_point(c)
        if gp is None:
            continue             # skip courses not yet posted (don't discard the rest)
        ch = c.get("credit_hours")
        if not ch:
            continue
        total_points += gp * ch
        total_credits += ch
    if total_credits == 0:
        return None              # nothing posted yet
    return round(total_points / total_credits, 2)


def cgpa(semesters):
    """CGPA across all COMPLETED semesters."""
    total_points = 0.0
    total_credits = 0
    for sem in semesters.values():
        for c in sem.get("courses", []):
            gp = course_grade_point(c)
            if gp is None:
                continue          # skip incomplete courses
            ch = c.get("credit_hours")
            if not ch:            # missing/zero credit hours -> skip safely
                continue
            total_points += gp * ch
            total_credits += ch
    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)


# Quick self-test when run directly
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json"))
    sems = data["semesters"]
    print("=== Grading engine test ===")
    for num, sem in sems.items():
        gpa = semester_gpa(sem["courses"])
        print(f"Semester {num} ({sem['term']}): GPA = {gpa if gpa else 'Awaiting (results incomplete)'}")
    print(f"\nOverall CGPA (completed courses): {cgpa(sems)}")