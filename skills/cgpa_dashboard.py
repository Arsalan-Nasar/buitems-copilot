# skills/cgpa_dashboard.py — Feature 2: all semesters' GPA + overall CGPA (simple wording).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import semester_gpa, cgpa


def cgpa_dashboard(data, message):
    sems = data["semesters"]
    lines = [f"**Your CGPA — {data['name']}**", f"_{data['program']}_", ""]
    lines.append("| Semester | Term | GPA |")
    lines.append("|---|---|---|")

    prev = None
    for num in sorted(sems.keys(), key=int):
        s = sems[num]
        gpa = semester_gpa(s["courses"])
        if gpa is None:
            lines.append(f"| {num} | {s['term']} | Waiting |")
        else:
            arrow = ""
            if prev is not None:
                arrow = " (up)" if gpa > prev else (" (down)" if gpa < prev else "")
            lines.append(f"| {num} | {s['term']} | {gpa}{arrow} |")
            prev = gpa

    overall = cgpa(sems)
    lines.append("")
    lines.append(f"**Your overall CGPA: {overall}**")

    if overall is not None:
        if overall >= 3.5:
            lines.append("\nVery good — you are doing great. Keep it up.")
        elif overall >= 3.0:
            lines.append("\nGood work — you are doing well.")
        elif overall >= 2.0:
            lines.append("\nYou are passing. A little more effort can raise this.")
        else:
            lines.append("\nThis is low. Let's make a plan to bring it up.")

    return "\n".join(lines)