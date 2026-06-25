# core/roman_urdu.py — turns an English answer into natural Roman Urdu (wording only, numbers untouched).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GROQ_API_KEY, MODEL_NAME

_client = None

def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def to_roman_urdu(english_text):
    """Rewrite an English answer in Roman Urdu. Keeps ALL numbers, names, grades, tables exactly."""
    try:
        client = _get_client()
        prompt = (
            "Rewrite the following student message in natural Roman Urdu (Urdu written in English letters), "
            "the way Pakistani students actually talk. RULES:\n"
            "- Keep ALL numbers, grades, GPA/CGPA values, course names, and amounts EXACTLY the same.\n"
            "- Keep any markdown tables exactly as they are (do not translate table contents).\n"
            "- Only translate the sentences/explanations into Roman Urdu.\n"
            "- Keep it friendly and clear.\n\n"
            f"Message:\n{english_text}"
        )
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # if the LLM fails, fall back to the English answer (never crash)
        return english_text


# quick test
if __name__ == "__main__":
    sample = "Your CGPA is 3.28. You are in good standing. Keep working hard."
    print(to_roman_urdu(sample))