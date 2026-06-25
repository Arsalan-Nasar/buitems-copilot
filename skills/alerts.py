# skills/alerts.py — proactive alerts + simple summary (easy wording).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import semester_gpa, cgpa

ATT_THRESHOLD = 75


def get_alerts(data):
    alerts = []

    # pending fees
    fees = data.get("fees", [])
    pending = sum(f["total"] - f["paid"] for f in fees)
    if pending > 0:
        alerts.append(f"You still need to pay **Rs {pending:,}** in fees. Please pay before the due date.")

    # low attendance
    for r in data.get("attendance", []):
        pct = round(r["present"] / r["total"] * 100) if r["total"] else 0
        if pct < ATT_THRESHOLD:
            alerts.append(f"Your attendance in **{r['title']}** is **{pct}%** — below {ATT_THRESHOLD}%. Try not to miss classes.")

    # results not ready
    for num, sem in data["semesters"].items():
        if semester_gpa(sem["courses"]) is None:
            alerts.append(f"Your **Semester {num}** result is not complete yet — some final marks are still missing.")

    return alerts


def at_a_glance(data):
    overall = cgpa(data["semesters"])
    fees = data.get("fees", [])
    pending = sum(f["total"] - f["paid"] for f in fees)
    att = data.get("attendance", [])
    low = min((round(r["present"]/r["total"]*100) for r in att if r["total"]), default=None)

    parts = []
    if overall is not None:
        parts.append(f"CGPA {overall}")
    if low is not None:
        parts.append(f"lowest attendance {low}%")
    parts.append(f"fees due Rs {pending:,}" if pending > 0 else "fees paid")
    return " · ".join(parts)


def alerts_summary(data, message=""):
    glance = at_a_glance(data)
    alerts = get_alerts(data)

    lines = [f"**Quick look:** {glance}", ""]
    if alerts:
        lines.append("**Things to take care of:**")
        for a in alerts:
            lines.append(f"- {a}")
    else:
        lines.append("Everything looks good. No fees due, attendance is fine, and your results are up to date.")
    return "\n".join(lines)