# skills/attendance.py — Feature 4: attendance with low-attendance warnings (simple wording).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THRESHOLD = 75   # you need at least 75% to sit the exam


def attendance_summary(data, message):
    records = data.get("attendance", [])
    if not records:
        return "No attendance records found."

    lines = [f"**Your Attendance — {data['name']}**", ""]
    lines.append("| Subject | Present | Total | % | Status |")
    lines.append("|---|---|---|---|---|")

    warnings = []
    for r in records:
        pct = round(r["present"] / r["total"] * 100) if r["total"] else 0
        if pct >= THRESHOLD:
            status = "OK"
        else:
            status = "Low"
            warnings.append((r["title"], pct))
        lines.append(f"| {r['title']} | {r['present']} | {r['total']} | {pct}% | {status} |")

    lines.append("")
    if warnings:
        lines.append(f"**Careful:** you need at least {THRESHOLD}% to sit the exam. Your attendance is low in:")
        for title, pct in warnings:
            lines.append(f"- {title} ({pct}%) — try not to miss the next classes.")
    else:
        lines.append(f"All your subjects are above {THRESHOLD}%. Well done.")

    return "\n".join(lines)