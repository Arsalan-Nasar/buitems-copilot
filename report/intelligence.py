# report/intelligence.py — THE INTELLIGENCE LAYER.
#
# PLAIN ENGLISH:
# Phase R1 gave us the FACTS. This turns facts into INSIGHT — what the numbers
# mean and what to do about them. It reads the structured report object and adds:
#   - an Academic Health Score (0-100, the signature number)
#   - strengths & weaknesses (ranked subjects)
#   - risk flags (red / amber / green, most urgent first)
#   - personalized, rule-based suggestions
#   - an attendance-recovery calculator
#
# 100% rules and math. No LLM. Fully offline.


# ---------------------------------------------------------------------------
# ACADEMIC HEALTH SCORE (0-100) — the signature feature.
# A single number combining the three things that matter, each weighted:
#   - Academic performance (CGPA)      -> 60 points
#   - Attendance / exam-eligibility    -> 25 points
#   - Financial standing (fees clear)  -> 15 points
# The weighting says: grades matter most, attendance is critical (you can't sit
# exams without it), fees matter but are administrative. Tunable in one place.
# ---------------------------------------------------------------------------
_W_CGPA = 60
_W_ATTENDANCE = 25
_W_FEES = 15


def _cgpa_component(cgpa_value):
    """CGPA (0-4 scale) -> up to _W_CGPA points, proportional."""
    if cgpa_value is None:
        return 0, "no data yet"
    frac = max(0.0, min(cgpa_value / 4.0, 1.0))
    return round(_W_CGPA * frac), f"CGPA {cgpa_value}"


def _attendance_component(attendance_section):
    """Average attendance vs the 75% threshold -> up to _W_ATTENDANCE points.
    Being below the exam threshold in any course is penalised extra, because it
    is a hard blocker (you literally cannot sit that exam)."""
    courses = [c for c in attendance_section["courses"] if c["percent"] is not None]
    if not courses:
        return _W_ATTENDANCE, "no attendance data"  # don't punish absence of data
    avg = sum(c["percent"] for c in courses) / len(courses)
    frac = max(0.0, min(avg / 100.0, 1.0))
    pts = _W_ATTENDANCE * frac
    # hard penalty: each course below threshold loses a chunk
    below = len(attendance_section["below_threshold"])
    if below:
        pts *= max(0.4, 1 - 0.25 * below)
    return round(pts), f"avg attendance {round(avg)}%"


def _fees_component(fees_section):
    """Fees clear -> full points; outstanding -> partial based on how much is paid."""
    total = fees_section["total"]
    if total <= 0:
        return _W_FEES, "no fees on record"
    paid_frac = max(0.0, min(fees_section["paid"] / total, 1.0))
    return round(_W_FEES * paid_frac), (
        "fees clear" if fees_section["status"] == "clear" else "fees outstanding")


def academic_health_score(report):
    """Return the 0-100 score, a letter band, and a breakdown of how it was built."""
    cg_pts, cg_note = _cgpa_component(report["cgpa"]["cgpa"])
    at_pts, at_note = _attendance_component(report["attendance"])
    fe_pts, fe_note = _fees_component(report["fees"])
    score = cg_pts + at_pts + fe_pts

    if score >= 85:
        band = "Excellent"
    elif score >= 70:
        band = "Good"
    elif score >= 55:
        band = "Fair"
    elif score >= 40:
        band = "Needs Attention"
    else:
        band = "At Risk"

    return {
        "score": score,
        "band": band,
        "breakdown": [
            {"factor": "Academic (CGPA)", "points": cg_pts, "max": _W_CGPA, "note": cg_note},
            {"factor": "Attendance", "points": at_pts, "max": _W_ATTENDANCE, "note": at_note},
            {"factor": "Fees", "points": fe_pts, "max": _W_FEES, "note": fe_note},
        ],
    }


# ---------------------------------------------------------------------------
# STRENGTHS & WEAKNESSES — rank completed courses by grade point.
# ---------------------------------------------------------------------------
def strengths_and_weaknesses(report):
    graded = []
    for sem in report["semesters"]:
        for c in sem["courses"]:
            if c["grade_point"] is not None:
                graded.append({"title": c["title"], "code": c["code"],
                               "grade": c["grade"], "grade_point": c["grade_point"],
                               "semester": sem["semester"]})
    if not graded:
        return {"strengths": [], "weaknesses": []}
    graded.sort(key=lambda x: x["grade_point"], reverse=True)
    strengths = [c for c in graded if c["grade_point"] >= 3.3][:3]
    weaknesses = [c for c in graded if c["grade_point"] < 3.0][-3:]
    weaknesses.sort(key=lambda x: x["grade_point"])  # worst first
    return {"strengths": strengths, "weaknesses": weaknesses}


# ---------------------------------------------------------------------------
# RISK FLAGS — red / amber / green, ordered most urgent first.
# ---------------------------------------------------------------------------
def risk_flags(report):
    flags = []

    # attendance below threshold = RED (hard blocker for exams)
    for c in report["attendance"]["below_threshold"]:
        flags.append({
            "level": "red",
            "area": "attendance",
            "message": f"{c['title']}: {c['percent']}% attendance — below the "
                       f"{report['attendance']['threshold']}% needed to sit the exam.",
        })

    # outstanding fees = AMBER
    if report["fees"]["status"] == "outstanding":
        flags.append({
            "level": "amber",
            "area": "fees",
            "message": f"Fee due of Rs {report['fees']['due']:,} — clear it before the deadline.",
        })

    # low CGPA standing = RED/AMBER
    standing = report["cgpa"]["standing"]
    if standing in ("at_risk", "probation"):
        flags.append({
            "level": "red",
            "area": "cgpa",
            "message": f"CGPA {report['cgpa']['cgpa']} is low — focus on raising it this semester.",
        })
    elif standing == "satisfactory":
        flags.append({
            "level": "amber",
            "area": "cgpa",
            "message": f"CGPA {report['cgpa']['cgpa']} is okay but has room to grow.",
        })

    # everything good -> a GREEN reassurance
    if not flags:
        flags.append({
            "level": "green",
            "area": "overall",
            "message": "No urgent issues — you're on track. Keep it up.",
        })

    order = {"red": 0, "amber": 1, "green": 2}
    flags.sort(key=lambda f: order[f["level"]])
    return flags


# ---------------------------------------------------------------------------
# ATTENDANCE RECOVERY — how many classes must be attended to reach the threshold.
# ---------------------------------------------------------------------------
def attendance_recovery(report):
    """For each below-threshold course, compute classes-to-attend to reach 75%,
    assuming they attend every remaining class (best case)."""
    THRESHOLD = report["attendance"]["threshold"] / 100.0
    out = []
    for c in report["attendance"]["below_threshold"]:
        present, total = c["present"], c["total"]
        # need (present + x) / (total + x) >= THRESHOLD  -> solve for x
        # x >= (THRESHOLD*total - present) / (1 - THRESHOLD)
        if THRESHOLD >= 1:
            needed = None
        else:
            needed = (THRESHOLD * total - present) / (1 - THRESHOLD)
            needed = max(0, -(-int(needed // 1)) if needed == int(needed) else int(needed) + 1)
        out.append({
            "title": c["title"],
            "current_percent": c["percent"],
            "classes_to_attend": needed,
        })
    return out


# ---------------------------------------------------------------------------
# SUGGESTIONS — rule-based, tied to the actual findings.
# ---------------------------------------------------------------------------
def suggestions(report, sw=None):
    sw = sw or strengths_and_weaknesses(report)
    tips = []

    for c in report["attendance"]["below_threshold"]:
        tips.append(f"Attend every remaining {c['title']} class — your attendance "
                    f"({c['percent']}%) is below the exam threshold.")

    for w in sw["weaknesses"]:
        tips.append(f"Give extra focus to {w['title']} (grade {w['grade']}) — "
                    f"improving it would lift your CGPA the most.")

    if report["fees"]["status"] == "outstanding":
        tips.append(f"Clear your outstanding fee of Rs {report['fees']['due']:,} "
                    f"to avoid any hold on results or registration.")

    if report["trend"]["direction"] == "up":
        tips.append("Your GPA is trending upward — keep the momentum going.")
    elif report["trend"]["direction"] == "down":
        tips.append("Your GPA has dipped recently — a focused semester can turn it around.")

    if not tips:
        tips.append("You're doing well across the board — maintain your current habits.")
    return tips


def build_intelligence(report):
    """Assemble the whole intelligence layer on top of a report object."""
    sw = strengths_and_weaknesses(report)
    return {
        "health_score": academic_health_score(report),
        "strengths": sw["strengths"],
        "weaknesses": sw["weaknesses"],
        "flags": risk_flags(report),
        "attendance_recovery": attendance_recovery(report),
        "suggestions": suggestions(report, sw),
    }
