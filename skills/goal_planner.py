# skills/goal_planner.py — Feature 7: what GPA is needed in remaining semesters to hit a CGPA goal.
import os, sys, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import course_grade_point

TOTAL_SEMESTERS = 8   # a typical BS program length


def _completed_points_credits(data):
    """Sum grade points and credits from all completed courses."""
    pts = 0.0
    creds = 0
    for sem in data["semesters"].values():
        for c in sem["courses"]:
            gp = course_grade_point(c)
            if gp is not None:
                pts += gp * c["credit_hours"]
                creds += c["credit_hours"]
    return pts, creds


def goal_planner(data, message):
    # target CGPA from the message (e.g. 3.5)
    m = re.search(r"(\d\.\d+|\d)", message)
    if not m:
        return ("What CGPA do you want to graduate with? Try "
                "**\"I want to graduate with a 3.5 CGPA\"**")
    target = float(m.group(1))
    if target > 4.0:
        return "The maximum CGPA is 4.0. Please pick a target up to 4.0."

    pts, creds = _completed_points_credits(data)
    if creds == 0:
        return "I need some completed results first to plan your goal."

    current_cgpa = round(pts / creds, 2)

    # estimate credits done vs remaining (rough, based on semester count)
    completed_sems = sum(
        1 for sem in data["semesters"].values()
        if all(course_grade_point(c) is not None for c in sem["courses"])
    )
    remaining_sems = max(TOTAL_SEMESTERS - completed_sems, 0)

    lines = [f"**CGPA Goal Planner — {data['name']}**", ""]
    lines.append(f"Current CGPA: **{current_cgpa}** (from {completed_sems} completed semester(s))")
    lines.append(f"Goal: **{target} CGPA** at graduation")
    lines.append("")

    if remaining_sems == 0:
        lines.append("You've completed all semesters, so your CGPA is essentially final.")
        return "\n".join(lines)

    # assume each remaining semester carries a similar credit load to the average so far
    avg_credits_per_sem = round(creds / max(completed_sems, 1))
    remaining_credits = avg_credits_per_sem * remaining_sems
    total_credits_end = creds + remaining_credits

    # points needed overall, minus points already earned -> needed from remaining
    needed_total_points = target * total_credits_end
    needed_remaining_points = needed_total_points - pts
    needed_avg_gpa = round(needed_remaining_points / remaining_credits, 2)

    lines.append(f"You have about **{remaining_sems} semester(s)** left (~{remaining_credits} credits).")
    if needed_avg_gpa <= 0:
        lines.append(f"You've **already secured** your {target} goal — even a low performance keeps you above it. Excellent.")
    elif needed_avg_gpa > 4.0:
        lines.append(f"To reach **{target}**, you'd need an average of **{needed_avg_gpa}** GPA — above the 4.0 maximum, so this goal isn't reachable now. "
                     f"A strong, realistic target would be closer to your reach. Let's aim a bit lower.")
    else:
        ease = "very achievable" if needed_avg_gpa <= 3.0 else ("achievable with focus" if needed_avg_gpa <= 3.7 else "ambitious but possible")
        lines.append(f"You need to average **{needed_avg_gpa} GPA** in your remaining semesters to graduate with a **{target}**.")
        lines.append(f"That's {ease}. Stay consistent and you'll get there.")

    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(goal_planner(data, "I want to graduate with a 3.5 CGPA"))
    print("\n" + "="*50 + "\n")
    print(goal_planner(data, "I want to graduate with a 3.0"))