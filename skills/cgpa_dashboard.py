# skills/cgpa_dashboard.py — Feature 2: all semesters' GPA + overall CGPA in one view.
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import semester_gpa, cgpa


def cgpa_dashboard(data, message):
    sems = data["semesters"]
    lines = [f"📊 **CGPA Dashboard — {data['name']}**", f"_{data['program']}_", ""]
    lines.append("| Semester | Term | GPA |")
    lines.append("|---|---|---|")

    prev = None
    for num in sorted(sems.keys(), key=int):
        s = sems[num]
        gpa = semester_gpa(s["courses"])
        if gpa is None:
            lines.append(f"| {num} | {s['term']} | ⏳ Awaiting |")
        else:
            arrow = ""
            if prev is not None:
                arrow = " 🟢▲" if gpa > prev else (" 🔴▼" if gpa < prev else " ➖")
            lines.append(f"| {num} | {s['term']} | {gpa}{arrow} |")
            prev = gpa

    overall = cgpa(sems)
    lines.append("")
    lines.append(f"**Overall CGPA: {overall}** 🎯")

    # a short, honest standing note
    if overall is not None:
        if overall >= 3.5:
            lines.append("\n_Excellent standing — keep it up!_")
        elif overall >= 3.0:
            lines.append("\n_Good standing — solid progress._")
        elif overall >= 2.0:
            lines.append("\n_Satisfactory — a strong push can lift this higher._")
        else:
            lines.append("\n_Below target — let's plan how to improve._")

    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(cgpa_dashboard(data, "what is my cgpa"))