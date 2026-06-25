# skills/whatif.py — Feature 5: What-If grade simulator.
import os, sys, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import marks_to_grade, semester_gpa


def _find_course(data, text):
    """Match a course the student names (by title word or code)."""
    text = text.lower()
    for sem in data["semesters"].values():
        for c in sem["courses"]:
            words = c["title"].lower().split()
            if c["code"].lower().replace(" ", "") in text.replace(" ", ""):
                return sem, c
            if any(w in text for w in words if len(w) > 3):
                return sem, c
    return None, None


def whatif(data, message):
    # find the final mark the student is imagining (a number in the message)
    nums = re.findall(r"\d+", message)
    if not nums:
        return ("Tell me the final mark you want to try, e.g. "
                "**\"what if I get 40 in my final for Data Structures?\"**")
    imagined_final = int(nums[-1])

    sem, course = _find_course(data, message)
    if not course:
        return ("Which course? Try naming it, e.g. "
                "**\"what if I get 40 in the final for Data Structures?\"**")

    if imagined_final > 50:
        return f"The final is out of 50, so {imagined_final} isn't possible. Try a number up to 50."

    # compute the hypothetical result
    total = course["mid"] + imagined_final + course["sessional"]
    grade = marks_to_grade(total)

    # build a temporary copy of the semester with this final filled in, to preview GPA
    preview_courses = []
    for c in sem["courses"]:
        if c is course:
            cc = dict(c); cc["final"] = imagined_final
            preview_courses.append(cc)
        else:
            preview_courses.append(c)
    preview_gpa = semester_gpa(preview_courses)

    lines = [f"**What-If — {course['title']}**", ""]
    lines.append(f"If you score **{imagined_final}/50** in the final:")
    lines.append(f"- Mid {course['mid']} + Final {imagined_final} + Sessional {course['sessional']} = **{total}/100**")
    lines.append(f"- Grade: **{grade}**")
    if preview_gpa is not None:
        lines.append(f"- Your Semester GPA would become **{preview_gpa}**")
    else:
        lines.append("- (Other finals are still pending, so the full semester GPA can't be previewed yet — but this course's grade is shown above.)")
    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(whatif(data, "what if I get 45 in my final for Data Structures"))
    print("\n" + "="*50 + "\n")
    print(whatif(data, "what if I get 30 in the final for Artificial Intelligence"))