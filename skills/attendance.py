# skills/attendance.py — Feature 4: attendance with low-attendance warnings.
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

THRESHOLD = 75   # BUITEMS minimum attendance % to sit exams


def attendance_summary(data, message):
    records = data.get("attendance", [])
    if not records:
        return "No attendance records found."

    lines = [f"**Attendance — {data['name']}**", ""]
    lines.append("| Course | Present | Total | % | Status |")
    lines.append("|---|---|---|---|---|")

    warnings = []
    for r in records:
        pct = round(r["present"] / r["total"] * 100) if r["total"] else 0
        if pct >= THRESHOLD:
            status = "Safe"
        else:
            status = "Low — at risk"
            warnings.append((r["title"], pct))
        lines.append(f"| {r['title']} | {r['present']} | {r['total']} | {pct}% | {status} |")

    lines.append("")
    if warnings:
        lines.append(f"**Warning:** your attendance is below the {THRESHOLD}% requirement in:")
        for title, pct in warnings:
            lines.append(f"- {title} ({pct}%) — you may be barred from the exam. Attend the next classes.")
    else:
        lines.append(f"All courses are above the {THRESHOLD}% requirement. Well done — keep it up.")

    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(attendance_summary(data, "what is my attendance"))