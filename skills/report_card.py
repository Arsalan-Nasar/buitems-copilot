# skills/report_card.py — Feature 1: the full report card for a semester.
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import total_marks, marks_to_grade, semester_gpa


def detect_semester(text):
    """Find a semester number in the message (digits or words)."""
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

    # if no semester named, use the most recent COMPLETED one
    if sem is None:
        sem = data.get("current_semester", len(sems))
    sem = str(sem)

    if sem not in sems:
        return f"I couldn't find Semester {sem} in your record."

    s = sems[sem]
    lines = [f"📋 **Report Card — Semester {sem} ({s['term']})**", ""]
    lines.append("| Course | Cr | Mid/25 | Final/50 | Sess/25 | Total | Grade |")
    lines.append("|---|---|---|---|---|---|---|")

    pending = 0
    for c in s["courses"]:
        tot = total_marks(c)
        if tot is None:
            final_str = "⏳" if c.get("final") is None else c.get("final")
            lines.append(f"| {c['title']} | {c['credit_hours']} | {c['mid']} | {final_str} | {c['sessional']} | Awaiting | — |")
            pending += 1
        else:
            grade = marks_to_grade(tot)
            lines.append(f"| {c['title']} | {c['credit_hours']} | {c['mid']} | {c['final']} | {c['sessional']} | {tot} | {grade} |")

    lines.append("")
    gpa = semester_gpa(s["courses"])
    if gpa is not None:
        lines.append(f"**Semester GPA: {gpa}** ✅")
    else:
        lines.append(f"**GPA: pending** — {pending} of {len(s['courses'])} results not posted yet. I'll calculate it once all finals are in.")

    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(report_card(data, "show my semester 3 result"))
    print("\n" + "="*50 + "\n")
    print(report_card(data, "show my semester 4 result"))