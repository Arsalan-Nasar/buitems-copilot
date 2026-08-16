# server.py — Flask backend: serves the premium interface + formats replies as clean cards.
import json
import os
import re
import shutil
from flask import Flask, render_template, request, jsonify

from config import DATA_FILE
from core.router import route
from core.roman_urdu import to_roman_urdu
from skills.report_card import report_card
from skills.cgpa_dashboard import cgpa_dashboard
from skills.fees import fees_summary
from skills.attendance import attendance_summary
from skills.whatif import whatif
from skills.predictor import predictor
from skills.goal_planner import goal_planner
from skills.schedule import schedule_summary
from skills.alerts import alerts_summary
from skills.trend_chart import trend_chart
from knowledge.rag import answer_question, _IDENTITY_ANSWER
from core.authz import fetch_student, AuthorizationError
from core.normalize import normalize_student

# ---------------------------------------------------------------------------
# DATA STORE
# Today: one student loaded from a file, wrapped into a {id: record} database
#        so the code already looks like the real portal (many students by id).
# Later: replace _load_database() with a real portal/DB connection — nothing
#        else in this file has to change.
# ---------------------------------------------------------------------------
def _load_database():
    record = json.load(open(DATA_FILE, encoding="utf-8"))
    return {str(record["student_id"]): record}


DATABASE = _load_database()


def get_logged_in_id():
    """Return the id of the student who is logged in RIGHT NOW.

    THIS IS THE PORTAL SLOT. Today it returns the single demo student's id.
    When the BUITEMS portal is connected, this one function will instead read
    the verified student id from the portal's session token — and every skill
    stays protected automatically, because they all go through fetch_student().
    """
    # --- placeholder until portal integration ---
    return next(iter(DATABASE.keys()))
    # --- real version will be roughly: ---
    # return read_verified_id_from_portal_session(request)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# DoS / ABUSE PROTECTION (application layer)
# ---------------------------------------------------------------------------
# NOTE: This stops CHEAP abuse — oversized payloads and simple request floods.
# It does NOT replace infrastructure-level DDoS protection (Cloudflare, a
# reverse proxy, or the university firewall), which must sit in front of this
# app in production. Code alone cannot stop a large distributed attack.

# 1) Cap the size of any incoming request body (reject giant payloads early).
MAX_MESSAGE_CHARS = 2000          # a real student question is never this long
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024   # 64 KB hard cap on request body

# 2) Simple in-memory per-client rate limit.
#    (For a single-server deployment this is fine; a multi-server deployment
#    would use Redis instead. Flagged for the BUITEMS deployment.)
import time as _time
from collections import deque

_RATE_MAX = 20                    # max requests...
_RATE_WINDOW = 10                 # ...per this many seconds, per client
_hits = {}                        # client_key -> deque[timestamps]


def _rate_limited(client_key):
    """Return True if this client has exceeded the allowed request rate."""
    now = _time.time()
    dq = _hits.setdefault(client_key, deque())
    # drop timestamps older than the window
    while dq and now - dq[0] > _RATE_WINDOW:
        dq.popleft()
    if len(dq) >= _RATE_MAX:
        return True
    dq.append(now)
    return False


# ---------- markdown -> clean HTML cards ----------
def md_to_card(md, downloadable=False):
    """Turn a skill's markdown (title + table/lines) into a clean horizontal-table card."""
    lines = [l for l in md.split("\n")]
    html = ['<div class="result-card">']
    table_rows = []
    in_table = False
    title_done = False

    def flush_table():
        nonlocal table_rows
        if not table_rows:
            return ""
        header = table_rows[0]
        body = table_rows[1:]
        out = ['<table class="rtable">']
        out.append("<tr>")
        for i, h in enumerate(header):
            cls = "" if i == 0 else ' class="c"'
            out.append(f"<th{cls}>{h}</th>")
        out.append("</tr>")
        for row in body:
            out.append("<tr>")
            for i, v in enumerate(row):
                h = header[i].lower() if i < len(header) else ""
                if i == 0:
                    out.append(f'<td class="subj">{v}</td>')
                elif "grade" in h:
                    cell = f'<span class="gd">{v}</span>' if v not in ("", "—") else "—"
                    out.append(f'<td class="c">{cell}</td>')
                elif "total" in h:
                    out.append(f'<td class="tot">{v}</td>')
                else:
                    out.append(f'<td class="c">{v}</td>')
            out.append("</tr>")
        out.append("</table>")
        table_rows = []
        return "".join(out)

    for line in lines:
        s = line.strip()
        if not s:
            continue
        img = re.search(r"!\[.*?\]\((.*?)\)", s)
        if img:
            html.append(f'<img src="{img.group(1)}" alt="GPA Trend">')
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.split("|")[1:-1]]
            if all(re.match(r"^-+$", c) for c in cells):
                continue
            in_table = True
            table_rows.append(cells)
            continue
        else:
            if in_table:
                html.append(flush_table())
                in_table = False
        clean = s.replace("**", "").replace("_", "")
        if not title_done and ("**" in line or clean.startswith("Your")):
            html.append(f'<div class="rc-title">{clean}</div>')
            title_done = True
            continue

        is_bullet = s.startswith("-") or s.startswith("*")
        strict_match = re.match(r'^([^:]{2,60}(?:GPA|CGPA)[^:]{0,20}):\s*(\d+\.?\d*)\s*$', clean)
        if strict_match and not is_bullet:
            lbl = strict_match.group(1).strip()
            val = strict_match.group(2)
            html.append(f'<div class="rc-foot"><span class="lbl">{lbl}</span><span class="val">{val}</span></div>')
            continue

        bold = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
        html.append(f'<div style="font-size:13.5px;line-height:1.55;margin:3px 0;">{bold}</div>')

    if in_table:
        html.append(flush_table())
    if downloadable:
        html.append('<div class="dl"><button class="dl-png">⬇ Save as PNG</button></div>')
    html.append("</div>")
    return "".join(html)


def build_reply(message):
    intent, language = route(message)
    text = message.lower()

    # ---- SECURITY GUARDS FIRST (before any data access) ----
    if intent == "identity":
        reply = _IDENTITY_ANSWER
        if language == "roman_urdu":
            reply = to_roman_urdu(reply)
        return md_to_card(reply, downloadable=False), language

    if intent == "out_of_scope":
        reply = ("I can only show you your own academic information — I can't change grades, "
                 "contact anyone on your behalf, or access another student's data. "
                 "Is there something about your own results, fees, or attendance I can help with?")
        if language == "roman_urdu":
            reply = to_roman_urdu(reply)
        return md_to_card(reply, downloadable=False), language

    # ---- AUTHORIZATION: fetch ONLY the logged-in student's data, once ----
    # Every skill below receives this verified record. No skill can reach
    # another student's data, because none of them touch the raw database.
    logged_in_id = get_logged_in_id()
    try:
        DATA = fetch_student(DATABASE, logged_in_id)
        DATA = normalize_student(DATA)   # guarantee a safe, complete shape
    except AuthorizationError:
        return md_to_card("I couldn't verify your account. Please log in again "
                          "through the portal.", downloadable=False), language

    # GPA trend chart (image) — only reached once the message is known-safe
    if any(w in text for w in ["trend", "graph", "chart"]):
        path = trend_chart(DATA)
        if path:
            shutil.copy(path, os.path.join("static", "gpa_trend.png"))
            md = "Your GPA Trend\n\n![GPA Trend](/static/gpa_trend.png)"
            return md_to_card(md, downloadable=True), "english"
        return "I need at least two completed semesters to draw your GPA trend.", "english"

    if intent == "report_card": reply = report_card(DATA, message); dl=True
    elif intent == "cgpa": reply = cgpa_dashboard(DATA, message); dl=True
    elif intent == "fees": reply = fees_summary(DATA, message); dl=True
    elif intent == "attendance": reply = attendance_summary(DATA, message); dl=True
    elif intent == "whatif": reply = whatif(DATA, message); dl=False
    elif intent == "predictor": reply = predictor(DATA, message); dl=False
    elif intent == "goal": reply = goal_planner(DATA, message); dl=False
    elif intent == "schedule": reply = schedule_summary(DATA, message); dl=True
    elif intent == "alerts": reply = alerts_summary(DATA); dl=False
    else: reply = answer_question(message); dl=False

    if language == "roman_urdu":
        reply = to_roman_urdu(reply)

    return md_to_card(reply, downloadable=dl), language


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/guide")
def guide():
    return render_template("guide.html")


@app.route("/chat", methods=["POST"])
def chat():
    # per-client rate limit (uses IP; behind a proxy this reads X-Forwarded-For)
    client_key = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    if _rate_limited(client_key):
        return jsonify({"html": "You're sending messages too quickly. "
                                "Please wait a few seconds and try again."}), 429

    data = request.get_json(silent=True)
    message = (data or {}).get("message", "")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"html": "Please type a question."})

    # cap message length (defends against oversized single payloads)
    if len(message) > MAX_MESSAGE_CHARS:
        message = message[:MAX_MESSAGE_CHARS]

    try:
        html, _ = build_reply(message)
    except Exception:
        # Never leak internal error detail to the user or logs shown to them.
        # (Log to a proper server-side logger in production, not stdout.)
        html = "Sorry, something went wrong while processing that."
    return jsonify({"html": html})


if __name__ == "__main__":
    # debug=False for production. Never ship with debug=True — it exposes an
    # interactive debugger that can run arbitrary code.
    app.run(debug=False, port=5000)