# tests/fixtures/students.py — a MATRIX of student types the report must handle.
#
# PLAIN ENGLISH:
# The report is used by very different students. Building/testing against only one
# (a graduating honors student) hid real bugs. This fixture defines the full range
# so every student type is exercised by the test suite:
#
#   probation      — CGPA below 2.0, needs urgent intervention
#   warning        — CGPA 2.0-2.5, borderline
#   good           — solid mid-range student
#   honors         — Dean's-List-range student
#   graduated      — completed the degree (retrospective, no "improve" advice)
#   first_semester — only one semester on record (no trend yet)
#   five_year      — a 10-semester program (e.g. Pharm-D / Engineering)
#   fresh          — brand new, no results posted yet (all in-progress)

def _c(code, title, ch, mid, final, sess):
    return {"code": code, "title": title, "credit_hours": ch,
            "mid": mid, "final": final, "sessional": sess}


def _sem(term, courses):
    return {"term": term, "courses": courses}


# ---- helpers to hit target grade bands ----
# marks: A>=85, A-80, B+75, B70, B-65, C+61, C58, C-55, D50, F<50
def _A(ch):   return _c("X", "Course", ch, 23, 45, 23)   # 91 A
def _B(ch):   return _c("X", "Course", ch, 18, 36, 19)   # 73 B
def _C(ch):   return _c("X", "Course", ch, 15, 30, 15)   # 60 C
def _D(ch):   return _c("X", "Course", ch, 13, 25, 13)   # 51 D
def _F(ch):   return _c("X", "Course", ch, 10, 20, 10)   # 40 F
def _inprog(ch): return _c("X", "Course", ch, None, None, None)


PROBATION = {
    "student_id": "P001", "name": "Probation Student",
    "program": "BS Information Technology", "current_semester": 3,
    "program_length": 8, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2024", [_D(3), _F(3), _C(3)]),
        "2": _sem("Spring 2025", [_F(3), _D(3), _D(3)]),
    },
    "fees": [{"term": "Fall 2024", "total": 50000, "paid": 30000}],
    "attendance": [{"code": "X", "title": "Networks", "present": 15, "total": 30}],
    "schedule": [],
}

WARNING = {
    "student_id": "W001", "name": "Warning Student",
    "program": "BS Information Technology", "current_semester": 3,
    "program_length": 8, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2024", [_C(3), _B(3), _C(3)]),
        "2": _sem("Spring 2025", [_C(3), _C(3), _B(3)]),
    },
    "fees": [{"term": "Fall 2024", "total": 50000, "paid": 50000}],
    "attendance": [{"code": "X", "title": "Databases", "present": 24, "total": 30}],
    "schedule": [],
}

GOOD = {
    "student_id": "G001", "name": "Good Student",
    "program": "BS Information Technology", "current_semester": 4,
    "program_length": 8, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2024", [_B(3), _B(3), _C(3)]),
        "2": _sem("Spring 2025", [_B(3), _A(3), _B(3)]),
        "3": _sem("Fall 2025", [_A(3), _B(3), _B(3)]),
    },
    "fees": [{"term": "Fall 2025", "total": 50000, "paid": 40000}],
    "attendance": [{"code": "X", "title": "AI", "present": 26, "total": 34}],
    "schedule": [],
}

HONORS = {
    "student_id": "H001", "name": "Honors Student",
    "program": "BS Information Technology", "current_semester": 5,
    "program_length": 8, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2023", [_A(3), _A(3), _B(3)]),
        "2": _sem("Spring 2024", [_A(3), _A(3), _A(3)]),
        "3": _sem("Fall 2024", [_A(3), _B(3), _A(3)]),
        "4": _sem("Spring 2025", [_A(3), _A(3), _A(3)]),
    },
    "fees": [{"term": "Spring 2025", "total": 50000, "paid": 50000}],
    "attendance": [{"code": "X", "title": "ML", "present": 32, "total": 34}],
    "schedule": [],
}

GRADUATED = {
    "student_id": "GR01", "name": "Graduate Student",
    "program": "BS Information Technology", "current_semester": 8,
    "program_length": 8, "graduated": True,
    "semesters": {
        str(i): _sem(f"Term {i}", [_A(3), _B(3), _A(3)]) for i in range(1, 9)
    },
    "fees": [{"term": "Term 8", "total": 50000, "paid": 50000}],
    "attendance": [],
    "schedule": [],
}

FIRST_SEMESTER = {
    "student_id": "F001", "name": "First Sem Student",
    "program": "BS Information Technology", "current_semester": 1,
    "program_length": 8, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2025", [_B(3), _A(3), _C(3)]),
    },
    "fees": [{"term": "Fall 2025", "total": 50000, "paid": 50000}],
    "attendance": [{"code": "X", "title": "Programming", "present": 28, "total": 30}],
    "schedule": [],
}

FIVE_YEAR = {
    "student_id": "5Y01", "name": "Five Year Student",
    "program": "Pharm-D", "current_semester": 6,
    "program_length": 10, "graduated": False,
    "semesters": {
        str(i): _sem(f"Term {i}", [_B(3), _A(3), _B(3)]) for i in range(1, 6)
    },
    "fees": [{"term": "Term 5", "total": 80000, "paid": 60000}],
    "attendance": [{"code": "X", "title": "Pharmacology", "present": 27, "total": 34}],
    "schedule": [],
}

FRESH = {
    "student_id": "FR01", "name": "Fresh Student",
    "program": "BS Information Technology", "current_semester": 1,
    "program_length": 8, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2025", [_inprog(3), _inprog(3), _inprog(3)]),
    },
    "fees": [{"term": "Fall 2025", "total": 50000, "paid": 0}],
    "attendance": [{"code": "X", "title": "Intro", "present": 10, "total": 12}],
    "schedule": [],
}


MS_STUDENT = {
    "student_id": "MS01", "name": "MS Student",
    "program": "MS Computer Science", "current_semester": 2,
    "program_length": 4, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2024", [_A(3), _A(3), _B(3)]),
    },
    "fees": [{"term": "Fall 2024", "total": 80000, "paid": 80000}],
    "attendance": [{"code": "X", "title": "Advanced Algorithms", "present": 28, "total": 30}],
    "schedule": [],
}

PHD_STUDENT = {
    "student_id": "PHD01", "name": "PhD Student",
    "program": "PhD Computer Science", "current_semester": 2,
    "program_length": 6, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2024", [_A(3), _A(3)]),
    },
    "fees": [{"term": "Fall 2024", "total": 100000, "paid": 100000}],
    "attendance": [],
    "schedule": [],
}

ALL_STUDENTS = {
    "probation": PROBATION, "warning": WARNING, "good": GOOD, "honors": HONORS,
    "graduated": GRADUATED, "first_semester": FIRST_SEMESTER,
    "five_year": FIVE_YEAR, "fresh": FRESH,
    "ms": MS_STUDENT, "phd": PHD_STUDENT,
}
