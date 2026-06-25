# skills/predictor.py — Feature 6: what final mark is needed for a target grade.
import os, sys, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# minimum total (out of 100) for each grade, real BUITEMS scale
GRADE_MIN = {"A":85,"A-":80,"B+":75,"B":70,"B-":65,"C+":61,"C":58,"C-":55,"D":50}


def _find_course(data, text):
    text = text.lower()
    for sem in data["semesters"].values():
        for c in sem["courses"]:
            if c["code"].lower().replace(" ", "") in text.replace(" ", ""):
                return c
            if any(w in text for w in c["title"].lower().split() if len(w) > 3):
                return c
    return None


def _find_grade(text):
    import re
    t = text.lower()
    # find all standalone grade-like tokens
    found = re.findall(r"\b(a-|b\+|b-|c\+|c-|[abcd])\b", t)
    # drop the article "a" ONLY if a stronger grade also exists
    real = [g for g in found if g not in ("a",)]
    if real:
        return real[0].upper()
    if "a" in found:          # "get an A" with no other grade -> A
        return "A"
    return None

def predictor(data, message):
    course = _find_course(data, message)
    if not course:
        return ("Which course? Try **\"what do I need in the final to get a B in Data Structures?\"**")

    grade = _find_grade(message) or "B"   # default target if none named
    target_total = GRADE_MIN.get(grade)

    have = course["mid"] + course["sessional"]          # marks already secured
    needed_final = target_total - have                  # final needed for the target

    lines = [f"**Grade Predictor — {course['title']}**", ""]
    lines.append(f"You already have **{have}/50** secured (Mid {course['mid']} + Sessional {course['sessional']}).")
    lines.append(f"Target grade: **{grade}** (needs {target_total}/100 total).")
    lines.append("")

    if needed_final <= 0:
        lines.append(f"Good news — you've **already secured a {grade}** even with 0 in the final.")
    elif needed_final > 50:
        lines.append(f"To get a **{grade}** you'd need **{needed_final}/50** in the final — but the final is only out of 50, so a {grade} isn't reachable this time. "
                     f"Let's aim for the next achievable grade instead.")
    else:
        lines.append(f"You need **{needed_final}/50** in the final to get a **{grade}**.")
        ease = "very achievable" if needed_final <= 25 else ("achievable with effort" if needed_final <= 40 else "tough but possible")
        lines.append(f"That's {ease}. Plan your preparation around this target.")

    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(predictor(data, "what do I need in the final to get a B in Data Structures"))
    print("\n" + "="*50 + "\n")
    print(predictor(data, "what final marks for an A in Artificial Intelligence"))