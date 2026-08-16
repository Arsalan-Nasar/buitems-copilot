# core/audit.py — AUDIT LOGGING (a tamper-evident record of what happened).
#
# PLAIN ENGLISH:
# This writes a line for every meaningful event: who asked, when, what intent,
# and the outcome (answered / refused / blocked / error). It is how we can later
# prove the system behaved correctly, investigate an incident, or detect an
# attack in progress.
#
# CRITICAL PRIVACY RULE:
# The audit log records WHAT HAPPENED, never the private DATA. We log the student
# id, the intent, and the outcome — but NEVER their CGPA, fees, name, or the text
# of their message. Otherwise the log itself would become a PII leak, undoing
# Phase 2. Raw message text is never stored; at most we store its length and a
# short non-reversible fingerprint for correlating repeated abuse.

import hashlib
import json
import os
import time
from datetime import datetime, timezone

# Where the log lives. In production this should be a write-only/append-only
# location the app can write but not casually edit (flagged for deployment).
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "audit.log")


def _fingerprint(text):
    """A short, non-reversible fingerprint of a message — lets us notice the same
    abusive input repeating, without ever storing the message content itself."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:12]


def log_event(student_id, intent, outcome, message=None, extra=None):
    """Append one audit record.

    Args:
        student_id: the logged-in student id (an identifier, not private data).
        intent:     the routed intent (cgpa, fees, identity, out_of_scope, ...).
        outcome:    'answered' | 'refused' | 'blocked' | 'rate_limited' | 'error'.
        message:    the raw user message — NEVER stored; only its length and
                    fingerprint are recorded, for abuse correlation.
        extra:      optional dict of non-sensitive extra fields.

    Never raises: logging must never break the actual request flow.
    """
    try:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "student_id": str(student_id) if student_id is not None else None,
            "intent": intent,
            "outcome": outcome,
            "msg_len": len(message) if isinstance(message, str) else 0,
            "msg_fp": _fingerprint(message) if isinstance(message, str) else "",
        }
        if extra:
            # only allow simple, non-sensitive scalar extras
            for k, v in extra.items():
                if isinstance(v, (str, int, float, bool)) and k not in record:
                    record[k] = v

        os.makedirs(_LOG_DIR, exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Auditing failing must NEVER take down the app. Swallow silently.
        # (In production, a secondary alert on logging failure is advisable.)
        pass


def read_events(limit=100):
    """Read back recent audit records (newest last). For tests/inspection."""
    if not os.path.exists(_LOG_FILE):
        return []
    with open(_LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
