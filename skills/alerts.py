# skills/alerts.py — proactive alerts + "semester at a glance" summary.
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import semester_gpa, cgpa

ATT_THRESHOLD = 75


def get_alerts(data):
    """Return a list of alert strings based on the student's current data."""
    alerts = []

    # 1. pending fees
    fees = data.get("fees", [])
    pending = sum(f["total"] - f["paid"] for f in fees)
    if pending > 0:
        alerts.append(f"You have **Rs {pending:,}** in pending fees. Clear it before the deadline to avoid a late fee.")

    # 2. low attendance
    for r in data.get("attendance", []):
        pct = round(r["present"] / r["total"] * 100) if r["total"] else 0
        if pct < ATT_THRESHOLD:
            alerts.append(f"Your attendance in **{r['title']}** is **{pct}%** — below the {ATT_THRESHOLD}% requirement. Attend the next classes.")

    # 3. pending results (finals not posted)
    for num, sem in data["semesters"].items():
        if semester_gpa(sem["courses"]) is None:
            alerts.append(f"Your **Semester {num}** results are awaiting final marks. I'll calculate your GPA as soon as they're posted.")

    return alerts


def at_a_glance(data):
    """One-line semester summary."""
    overall = cgpa(data["semesters"])
    fees = data.get("fees", [])
    pending = sum(f["total"] - f["paid"] for f in fees)

    # lowest attendance %
    att = data.get("attendance", [])
    low = min((round(r["present"]/r["total"]*100) for r in att if r["total"]), default=None)

    parts = []
    if overall is not None:
        parts.append(f"CGPA {overall}")
    if low is not None:
        parts.append(f"lowest attendance {low}%")
    parts.append(f"fees pending Rs {pending:,}" if pending > 0 else "fees cleared")
    return " · ".join(parts)


def alerts_summary(data, message=""):
    glance = at_a_glance(data)
    alerts = get_alerts(data)

    lines = [f"**Semester at a glance:** {glance}", ""]
    if alerts:
        lines.append("**Things that need your attention:**")
        for a in alerts:
            lines.append(f"- {a}")
    else:
        lines.append("Everything looks good — no pending fees, attendance is fine, and your results are up to date.")
    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(alerts_summary(data))