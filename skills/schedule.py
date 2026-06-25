# skills/schedule.py — class schedule & datesheet assistant.
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _course_title(data, code):
    for sem in data["semesters"].values():
        for c in sem["courses"]:
            if c["code"] == code:
                return c["title"]
    return code


def schedule_summary(data, message):
    sched = data.get("schedule", [])
    if not sched:
        return "No class schedule found on your record."

    text = message.lower()

    # did they ask about a specific day?
    asked_day = next((d for d in DAYS if d in text), None)
    # "today" -> use the real current weekday
    if "today" in text:
        import datetime
        asked_day = DAYS[datetime.datetime.now().weekday()]

    if asked_day:
        todays = [s for s in sched if s["day"].lower() == asked_day]
        title = asked_day.capitalize()
        if not todays:
            return f"**{title}:** You have no classes scheduled. Enjoy the free day."
        lines = [f"**Classes on {title}**", ""]
        for s in todays:
            lines.append(f"- **{_course_title(data, s['code'])}** ({s['code']}) — {s['time']}, Room: {s['room']}")
        return "\n".join(lines)

    # otherwise: full weekly schedule
    lines = ["**Your Weekly Class Schedule**", ""]
    lines.append("| Day | Course | Time | Room |")
    lines.append("|---|---|---|---|")
    for d in DAYS:
        for s in sched:
            if s["day"].lower() == d:
                lines.append(f"| {s['day']} | {_course_title(data, s['code'])} | {s['time']} | {s['room']} |")
    return "\n".join(lines)


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    print(schedule_summary(data, "what is my schedule"))
    print("\n" + "="*50 + "\n")
    print(schedule_summary(data, "what are my classes on monday"))