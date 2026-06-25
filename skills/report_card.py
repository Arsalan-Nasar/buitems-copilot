# skills/report_card.py — Feature 1: the full report card for a semester (simple wording).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import total_marks, marks_to_grade, semester_gpa


def detect_semester(text):
    import re
    text = text.lower()
    m = re.search(r"sem(?:ester)?\s*(\d+)", text) or re.search(r"(\d+)\s*(?:st|nd|rd|th)?\s*sem", text)
    if m:
        return int(m.group(1))
    words = {"first":1,"second":2,"third":3,"fourth":4,"fifth":5,"sixth":6,"seventh":7,"eighth":8}
    for w, n in words.items():
        if w in text:
            return n
    return None


def report_card(data, message):
    sem = detect_semester(message)
    sems = data["semesters"]

    if sem is None:
        sem = data.get("current_semester", len(sems))
    sem = str(sem)

    if sem not in sems:
        return f"I could not find Semester {sem} in your record."

    s = sems[sem]
    lines = [f"**Your Result — Semester {sem} ({s['term']})**", ""]
    lines.append("| Subject | Mid/25 | Final/50 | Sess/25 | Total | Grade |")
    lines.append("|---|---|---|---|---|---|")

    pending = 0
    for c in s["courses"]:
        tot = total_marks(c)
        if tot is None:
            final_str = "Not yet" if c.get("final") is None else c.get("final")
            lines.append(f"| {c['title']} | {c['mid']} | {final_str} | {c['sessional']} | Waiting | — |")
            pending += 1
        else:
            grade = marks_to_grade(tot)
            lines.append(f"| {c['title']} | {c['mid']} | {c['final']} | {c['sessional']} | {tot} | {grade} |")

    lines.append("")
    gpa = semester_gpa(s["courses"])
    if gpa is not None:
        lines.append(f"**Your GPA this semester: {gpa}**")
    else:
        lines.append(f"**GPA: not ready yet** — {pending} subject(s) still need final marks. I will work out your GPA once all marks are in.")

    return "\n".join(lines)