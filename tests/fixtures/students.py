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
# Each helper takes an optional realistic title so fixtures read like real data
# (not "Course, Course"). A rotating pool provides names when none is given.
_TITLE_POOL = [
    "Programming Fundamentals", "Data Structures", "Calculus I", "Calculus II",
    "Discrete Mathematics", "Computer Networks", "Operating Systems", "Databases",
    "Artificial Intelligence", "Software Engineering", "Web Technologies",
    "Digital Logic Design", "Linear Algebra", "English Composition",
]
_title_i = [0]


def _next_title():
    t = _TITLE_POOL[_title_i[0] % len(_TITLE_POOL)]
    _title_i[0] += 1
    return t


def _A(ch, title=None):   return _c("CS", title or _next_title(), ch, 23, 45, 23)   # 91 A
def _B(ch, title=None):   return _c("CS", title or _next_title(), ch, 18, 36, 19)   # 73 B
def _C(ch, title=None):   return _c("CS", title or _next_title(), ch, 15, 30, 15)   # 60 C
def _D(ch, title=None):   return _c("CS", title or _next_title(), ch, 13, 25, 13)   # 51 D
def _F(ch, title=None):   return _c("CS", title or _next_title(), ch, 10, 20, 10)   # 40 F
def _inprog(ch, title=None): return _c("CS", title or _next_title(), ch, None, None, None)
def _midonly(ch, title=None): return _c("CS", title or _next_title(), ch, 20, None, None)  # mid posted, awaiting final


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


STRUGGLING_WITH_FAILURES = {
    "student_id": "SF01", "name": "Resilient Student",
    "program": "BS Information Technology", "current_semester": 3,
    "program_length": 8, "graduated": False,
    "semesters": {
        "1": _sem("Fall 2024", [_F(3), _A(3), _B(3)]),   # failed one, aced another
        "2": _sem("Spring 2025", [_F(3), _A(3), _C(3)]),  # failed one, passed rest
    },
    "fees": [{"term": "Fall 2024", "total": 50000, "paid": 50000}],
    "attendance": [],
    "schedule": [],
}

PARTIAL_SEMESTER = {
    "student_id": "PS01", "name": "Mid-Semester Student",
    "program": "BS Information Technology", "current_semester": 5,
    "program_length": 8, "graduated": False,
    "semesters": {
        # completed earlier semesters with a REALISTIC rising journey
        "1": _sem("Fall 2023", [_C(3, "Programming Fundamentals"),
                                 _B(3, "Calculus I"),
                                 _B(3, "English Composition")]),          # ~2.9
        "2": _sem("Spring 2024", [_B(3, "Data Structures"),
                                   _B(3, "Discrete Mathematics"),
                                   _A(3, "Digital Logic Design")]),        # ~3.2
        "3": _sem("Fall 2024", [_A(3, "Object Oriented Programming"),
                                 _B(3, "Linear Algebra"),
                                 _A(3, "Database Systems")]),              # ~3.5
        "4": _sem("Spring 2025", [_A(3, "Operating Systems"),
                                   _A(3, "Software Engineering"),
                                   _A(3, "Computer Networks")]),           # 4.0
        # CURRENT semester: some results posted, one mid-only, one awaiting
        "5": _sem("Fall 2025", [
            _A(3, "Artificial Intelligence"),   # posted -> A
            _A(3, "Web Technologies"),          # posted -> A
            _midonly(3, "Machine Learning"),    # mid posted, awaiting final
            _inprog(3, "Cyber Security"),       # nothing yet
        ]),
    },
    "fees": [{"term": "Fall 2025", "total": 52000, "paid": 52000}],
    "attendance": [{"code": "CS", "title": "Machine Learning", "present": 26, "total": 30}],
    "schedule": [],
}


ALL_STUDENTS = {
    "probation": PROBATION, "warning": WARNING, "good": GOOD, "honors": HONORS,
    "graduated": GRADUATED, "first_semester": FIRST_SEMESTER,
    "five_year": FIVE_YEAR, "fresh": FRESH,
    "ms": MS_STUDENT, "phd": PHD_STUDENT,
    "struggling_failures": STRUGGLING_WITH_FAILURES,
    "partial_semester": PARTIAL_SEMESTER,
}
