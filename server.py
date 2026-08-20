# server.py — BUITEMS Copilot: the offline Academic Report generator.
#
# PLAIN ENGLISH:
# This is the "enhancement tab" backend. When a student opens the tab, the portal
# calls this server, which:
#   1. identifies the logged-in student (from the portal session — slot below),
#   2. fetches ONLY that student's data through the authorization layer,
#   3. normalizes it (crash-proof), assembles the report, adds the intelligence
#      layer, and renders the premium HTML — instantly, no chat, no typing.
#
# Fully offline: no LLM, no external calls. Nothing leaves the university network.

import json
import time
from collections import deque

from flask import Flask, request, Response, jsonify

from config import DATA_FILE
from core.authz import fetch_student, AuthorizationError
from core.normalize import normalize_student
from core.audit import log_event
from report.assemble import assemble_report
from report.intelligence import build_intelligence
from report.render import render_report


def _load_database():
    record = json.load(open(DATA_FILE, encoding="utf-8"))
    return {str(record["student_id"]): record}


DATABASE = _load_database()


def get_logged_in_id():
    """Return the id of the student who is logged in RIGHT NOW.

    THIS IS THE PORTAL SLOT. Today it returns the demo student's id. When the
    BUITEMS portal is connected, this reads the verified student id from the
    portal's session token — and the whole report stays scoped to that student
    automatically, because everything flows through fetch_student().
    """
    return next(iter(DATABASE.keys()))
    # real version, roughly:
    # return read_verified_id_from_portal_session(request)


app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
_RATE_MAX = 30
_RATE_WINDOW = 10
_hits = {}


def _rate_limited(client_key):
    now = time.time()
    dq = _hits.setdefault(client_key, deque())
    while dq and now - dq[0] > _RATE_WINDOW:
        dq.popleft()
    if len(dq) >= _RATE_MAX:
        return True
    dq.append(now)
    return False


@app.after_request
def _security_headers(response):
    """Defensive HTTP headers on every response (defense in depth)."""
    # Content-Security-Policy: allow the report's own inline <script> (chart +
    # count-up) and inline styles, plus Google Fonts. 'unsafe-inline' for scripts
    # is a deliberate trade-off — our PRIMARY XSS defense is HTML-escaping every
    # value in render.py (_esc), which is tested; this CSP is the secondary wall.
    # (A nonce-based CSP is the cleaner future hardening if BUITEMS requires it.)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def generate_report_html():
    """The core flow: authorize -> normalize -> assemble -> intelligence -> render.
    Returns (html, status_code). Never leaks internal errors to the user."""
    logged_in_id = get_logged_in_id()
    try:
        data = fetch_student(DATABASE, logged_in_id)
    except AuthorizationError:
        log_event(logged_in_id, "report", "error", extra={"reason": "auth_failed"})
        return ("<h1>We couldn't verify your account.</h1>"
                "<p>Please log in again through the portal.</p>", 403)

    try:
        data = normalize_student(data)
        report = assemble_report(data)
        intel = build_intelligence(report)
        html = render_report(report, intel)
        log_event(logged_in_id, "report", "generated")
        return (html, 200)
    except Exception:
        log_event(logged_in_id, "report", "error", extra={"reason": "render_failed"})
        return ("<h1>Something went wrong generating your report.</h1>"
                "<p>Please try again in a moment.</p>", 500)


@app.route("/report", methods=["GET"])
def report():
    """The enhancement-tab endpoint. Opening it auto-generates the report."""
    client_key = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
    if _rate_limited(client_key):
        return Response("Too many requests. Please wait a few seconds.", status=429)

    html, status = generate_report_html()
    return Response(html, status=status, mimetype="text/html")


@app.route("/health", methods=["GET"])
def health():
    """Simple liveness check for the portal/ops (no student data)."""
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    html, status = generate_report_html()
    return Response(html, status=status, mimetype="text/html")


# ---------------------------------------------------------------------------
# DEMO MODE — for presenting to the university. Lets you flip between different
# student types (probation, honors, graduated, 5-year, first-semester, ...) live.
# This is DEMO-ONLY tooling; the real /report route above is untouched and stays
# scoped to the single logged-in student via the authorization layer.
# ---------------------------------------------------------------------------
def _demo_students():
    """Load the demo student matrix. Returns {} if the fixtures aren't present
    (e.g. in a production deployment where the demo folder isn't shipped)."""
    try:
        import os as _os
        _here = _os.path.dirname(_os.path.abspath(__file__))
        import sys as _sys
        if _here not in _sys.path:
            _sys.path.insert(0, _here)
        from tests.fixtures.students import ALL_STUDENTS
        return ALL_STUDENTS
    except Exception:
        return {}


_DEMO_LABELS = {
    "honors": "Honors student (Dean's List)",
    "good": "Good standing student",
    "warning": "Academic warning (borderline)",
    "probation": "Probation (at risk)",
    "first_semester": "First-semester student",
    "graduated": "Graduated student",
    "five_year": "5-year program (Pharm-D)",
    "fresh": "Brand-new (no results yet)",
}


@app.route("/demo", methods=["GET"])
def demo():
    """Demo switcher: ?student=<key> renders that student type with a picker bar."""
    students = _demo_students()
    if not students:
        return Response("<h1>Demo fixtures not available.</h1>", status=404, mimetype="text/html")

    key = request.args.get("student", "honors")
    if key not in students:
        key = next(iter(students))

    try:
        data = normalize_student(students[key])
        report = assemble_report(data)
        intel = build_intelligence(report)
        report_html = render_report(report, intel)
    except Exception:
        return Response("<h1>Could not render this demo student.</h1>", status=500,
                        mimetype="text/html")

    # build the picker bar
    options = ""
    for k in _DEMO_LABELS:
        if k in students:
            sel = " selected" if k == key else ""
            options += f'<option value="{k}"{sel}>{_DEMO_LABELS[k]}</option>'
    picker = f'''<div style="position:sticky;top:0;z-index:99;background:#0a2540;color:#fff;
      padding:12px 18px;display:flex;align-items:center;gap:14px;font-family:'Sora',system-ui,sans-serif;
      box-shadow:0 2px 12px rgba(10,37,64,.25)">
      <span style="font-weight:700;font-size:13px;letter-spacing:.04em">DEMO</span>
      <span style="font-size:12px;color:rgba(255,255,255,.7)">Viewing:</span>
      <select onchange="location.href='/demo?student='+this.value"
        style="background:#123a63;color:#fff;border:1px solid rgba(255,255,255,.2);
        border-radius:8px;padding:7px 12px;font-size:13px;font-family:inherit;cursor:pointer">
        {options}
      </select>
      <span style="margin-left:auto;font-size:11px;color:rgba(255,255,255,.55)">
        Switch student types to see how the report adapts</span>
    </div>'''

    # inject the picker right after <body>
    html = report_html.replace("<body>", "<body>" + picker, 1)
    return Response(html, status=200, mimetype="text/html")


if __name__ == "__main__":
    app.run(debug=False, port=5000)
