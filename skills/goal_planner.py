# skills/goal_planner.py — Feature 7: honest, precise, and human CGPA goal planning.
import os, sys, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.grading import semester_gpa, cgpa

TOTAL_SEMESTERS = 8
MAX_CGPA = 4.0


def _completed_semesters(data):
    done = 0
    for num, sem in data["semesters"].items():
        if semester_gpa(sem["courses"]) is not None:
            done += 1
    return done


def _required_avg(current_cgpa, completed, target_cgpa, remaining):
    if remaining <= 0:
        return None
    total_needed = target_cgpa * (completed + remaining)
    earned_so_far = (current_cgpa or 0) * completed
    return (total_needed - earned_so_far) / remaining


def _ordinal(n):
    suf = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _mask(s, e, buf):
    lst = list(buf)
    for i in range(s, e):
        lst[i] = "#"
    return "".join(lst)


def _scan_clause_for_goals(text):
    """Scan a single clause (no 'and also' boundary inside it) for a CGPA number + optional semester."""
    goals = []
    for m in re.finditer(r'(\d\.\d{1,2})', text):
        v = float(m.group(1))
        if v <= 0:
            continue
        window = text[max(0, m.start()-40): m.end()+40]
        sem_m = (re.search(r'by\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+semester', window)
                 or re.search(r'by\s+(?:the\s+)?semester\s+(\d+)', window))
        sem = int(sem_m.group(1)) if sem_m else None
        goals.append((v, sem))
    return goals


def _find_goals(message):
    working = message.lower()
    goals = []
    sem_after = r'(?:[^.]{0,35}?\bby\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+semester)?'
    sem_before = r'(?:[^.]{0,35}?\bby\s+(?:the\s+)?semester\s+(\d+))?'

    range_patterns = [
        re.compile(r'cgpa\s+(?:of\s+)?(\d\.\d{1,2})\s*(?:to|-)\s*(\d\.\d{1,2})' + sem_after + sem_before),
        re.compile(r'(\d\.\d{1,2})\s*(?:to|-)\s*(\d\.\d{1,2})\s*cgpa' + sem_after + sem_before),
    ]
    for pat in range_patterns:
        for m in list(pat.finditer(working)):
            hi = float(m.group(2))
            sem_val = m.group(3) or m.group(4)
            sem = int(sem_val) if sem_val else None
            goals.append((hi, sem))
            working = _mask(m.start(), m.end(), working)

    single_patterns = [
        re.compile(r'cgpa\s+(?:of\s+)?(\d\.\d{1,2})' + sem_after + sem_before),
        re.compile(r'(\d\.\d{1,2})\s*cgpa' + sem_after + sem_before),
    ]
    for pat in single_patterns:
        for m in list(pat.finditer(working)):
            v = float(m.group(1))
            if v <= 0:
                continue
            sem_val = m.group(2) or m.group(3)
            sem = int(sem_val) if sem_val else None
            goals.append((v, sem))
            working = _mask(m.start(), m.end(), working)

    # Goal-intent context: any of these words means the remaining bare numbers
    # in the message are goal targets (e.g. "give me a target for a 3.5 3.6 3.7",
    # "is it realistic to finish with a 3.7"). We SWEEP leftover numbers whenever
    # this context is present — not only when nothing was found yet — so a message
    # listing several targets doesn't stop after the first.
    intent_words = (
        "need", "graduate", "reach", "target", "possible", "achievable",
        "achieve", "goal", "want", "get a", "finish", "end with", "hit",
        "realistic", "aim", "plan", "overall", "by semester", "by the",
        "tak",           # roman urdu: "3.8 tak" (up to 3.8)
        "pahunch",       # roman urdu: "pahunch sakta" (can reach)
        "le lun", "le lu", "hasil",  # roman urdu: "le lun" (take/get), "hasil" (achieve)
    )
    if any(w in working for w in intent_words):
        clauses = re.split(r'\band also\b|\balso\b|;', working)
        for clause in clauses:
            for v, sem in _scan_clause_for_goals(clause):
                goals.append((v, sem))

    seen = set()
    unique = []
    for v, sem in goals:
        key = (round(v, 2), sem)
        if key not in seen:
            seen.add(key)
            unique.append((v, sem))

    # Sort by GPA value (then semester) so a list like "3.5 3.6 3.7 3.8 3.9"
    # is presented in natural ascending order regardless of match order.
    unique.sort(key=lambda g: (g[0], g[1] if g[1] is not None else 99))
    return unique


def _sentence_for(value, semester, current, completed, remaining_total, is_first, impossible_count):
    connector = "" if is_first else "Similarly, "

    # invalid target — above the highest possible CGPA
    if value > MAX_CGPA:
        sentence = (f"{connector}a {value:.2f} CGPA isn't possible to aim for, since "
                    f"**{MAX_CGPA:.2f} is the highest CGPA achievable** here. "
                    f"If you're aiming for the top, a {MAX_CGPA:.2f} would be the real target.")
        return sentence, None

    if semester is not None:
        remaining = semester - completed
        label = f"a {value:.2f} CGPA by the {_ordinal(semester)} semester"
    else:
        remaining = remaining_total
        label = f"a {value:.2f} CGPA at graduation"

    if remaining <= 0:
        return (f"{connector}that semester has already passed or is your current one, "
                f"so a new target can't be set for it."), None

    req = _required_avg(current, completed, value, remaining)

    if req > MAX_CGPA:
        closings = [
            "which is above the 4.00 maximum, so it isn't achievable from where you stand right now.",
            "it's again above the 4.00 maximum, so this one isn't achievable either.",
            "that's also beyond the 4.00 ceiling, so this target is out of reach too.",
        ]
        closing = closings[min(impossible_count, len(closings) - 1)]
        sentence = (f"{connector}reaching {label} would need an average GPA of **{req:.2f}** "
                    f"in each of your remaining {remaining} semester(s) — {closing}")
    elif req <= 0:
        sentence = f"{connector}you've already secured {label} or better, so no extra push is needed there."
    else:
        sentence = (f"{connector}to reach {label}, you'd need to average **{req:.2f}** GPA "
                    f"across your remaining {remaining} semester(s) — a realistic target if you stay consistent.")
    return sentence, req


def goal_planner(data, message):
    current = cgpa(data["semesters"])
    completed = _completed_semesters(data)
    remaining_total = TOTAL_SEMESTERS - completed

    if current is None:
        return "I don't have enough completed semesters yet to work out a CGPA goal for you."

    goals = _find_goals(message)
    if not goals:
        return ("I couldn't find a specific CGPA goal or semester in your question. "
                "Try asking something like \"what CGPA do I need to graduate with a 3.7\" "
                "or \"can I reach a 3.9 by semester 7\", and I'll work it out from your record.")

    sentences = []
    all_impossible = True
    any_valid_target = False
    best_ceiling = None
    impossible_count = 0

    for i, (value, semester) in enumerate(goals):
        sentence, req = _sentence_for(value, semester, current, completed, remaining_total, i == 0, impossible_count)
        sentences.append(sentence)
        if req is not None:
            any_valid_target = True
            if req <= MAX_CGPA:
                all_impossible = False
            else:
                impossible_count += 1
            ceiling = min(req, MAX_CGPA)
            if best_ceiling is None or ceiling < best_ceiling:
                best_ceiling = ceiling

    body = f"Your current CGPA is **{current}** after {completed} completed semester(s). " + " ".join(sentences)

    if not any_valid_target:
        closing = ""
    elif all_impossible and best_ceiling is not None and remaining_total > 0:
        low_anchor = max(best_ceiling - 0.2, 3.0)
        closing = (f"\n\nThat said, this doesn't mean you can't graduate with a strong CGPA. "
                   f"If you perform well and aim to maintain roughly **{low_anchor:.2f} to {best_ceiling:.2f} GPA** "
                   f"in the semesters ahead, you can still finish with a genuinely impressive result.")
    elif remaining_total > 0:
        closing = ("\n\nStay consistent each semester and you'll get there — "
                   "feel free to ask again after your next results to see how the target shifts.")
    else:
        closing = ""

    return body + closing


if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    tests = [
        "Give me a GPA target to graduate with a CGPA of 3.8 to 3.9, and also tell me if it is possible to achieve a 4.0 CGPA by the 8th semester.",
        "Can I get a 5.0 CGPA?",
        "Can I reach 3.5 by semester 5, and also 3.9 by graduation?",
        "What do I need for a 4.0 CGPA by semester 7?",
    ]
    for t in tests:
        print(">>>", t)
        print(goal_planner(data, t))
        print()