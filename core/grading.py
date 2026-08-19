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
    """Add mid + final + sessional. Returns None if the final isn't posted yet."""
    mid = course.get("mid")
    final = course.get("final")
    sessional = course.get("sessional")
    if final is None or mid is None or sessional is None:
        return None              # result not complete yet
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


def semester_gpa(courses):
    """GPA for one semester. Returns None if any course is still incomplete."""
    total_points = 0.0
    total_credits = 0
    for c in courses:
        gp = course_grade_point(c)
        if gp is None:
            return None          # semester not finished -> no GPA yet
        ch = c.get("credit_hours")
        if not ch:               # missing/zero credit hours -> skip, don't crash
            continue
        total_points += gp * ch
        total_credits += ch
    if total_credits == 0:
        return None
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