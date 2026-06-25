# core/language.py — detects English vs Roman Urdu so the agent can reply in the student's language.

# Common Roman Urdu words students actually type. If a message has these, it's Roman Urdu.
ROMAN_URDU_HINTS = {
    "mera", "meri", "mujhe", "kya", "kia", "hai", "ka", "ki", "ke", "kitni", "kitna",
    "dikhao", "batao", "kaise", "kese", "konsa", "kaunsa", "result", "natija",
    "fees", "fee", "baqi", "jama", "haziri", "attendance", "semester", "gpa", "cgpa",
    "ap", "aap", "apna", "apni", "chahiye", "zaroorat", "kab", "kahan", "warning",
}

def detect_language(message):
    """Roman Urdu only if it contains words that are NEVER English."""
    words = set(message.lower().split())
    pure_urdu = {
        "mera", "meri", "mere", "mujhe", "mujhy", "apna", "apni", "ap", "aap",
        "kya", "kia", "kitni", "kitna", "kaise", "kese", "konsa", "kaunsa",
        "dikhao", "batao", "bata", "baqi", "jama", "haziri", "chahiye",
        "hai", "kab", "kahan", "kr", "kro", "krna", "ho", "hain",
    }
    if words & pure_urdu:
        return "roman_urdu"
    return "english"


# Quick test
if __name__ == "__main__":
    tests = [
        "show my result",
        "mera result dikhao",
        "what is my cgpa",
        "meri fees kitni baqi hai",
        "mujhe apni attendance batao",
        "how am I doing this semester",
    ]
    for t in tests:
        print(f"{detect_language(t):>12}  <-  {t}")