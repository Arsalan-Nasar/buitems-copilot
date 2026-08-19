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
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
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


if __name__ == "__main__":
    app.run(debug=False, port=5000)
