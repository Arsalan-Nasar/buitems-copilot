# core/logging_util.py — STRUCTURED LOGGING for Evora.
#
# PLAIN ENGLISH:
# Instead of scattering print() statements, we use Python's logging system, which
# gives every message a LEVEL (INFO / WARNING / ERROR ...), a TIMESTAMP, and the
# name of the component it came from. This is "observability": when something goes
# wrong in production, the logs are how we find out what, when, and where.
#
# LEVELS (least to most severe):
#   DEBUG    - fine-grained detail, for developers only
#   INFO     - normal, expected events ("report generated")
#   WARNING  - something unusual but handled ("attendance missing, using default")
#   ERROR    - an operation failed ("trend section crashed")
#   CRITICAL - the application itself is in danger
#
# Privacy note: logs must never contain sensitive student data (names, marks).
# We log IDENTIFIERS and EVENTS, not personal content — the same privacy-first
# principle used in core/audit.py.

import logging
import os
import sys

# The level can be tuned per environment without touching code:
#   LOG_LEVEL=DEBUG   (development — see everything)
#   LOG_LEVEL=WARNING (production — only problems)
# Defaults to INFO if not set.
_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
_LEVEL = getattr(logging, _LEVEL_NAME, logging.INFO)

# One shared format for every log line, e.g.:
#   2026-01-15 09:42:03 | INFO     | evora.render | report generated
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_once():
    """Set up the root logging configuration a single time. Safe to call from
    anywhere; only the first call takes effect."""
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root = logging.getLogger("evora")
    root.setLevel(_LEVEL)
    # avoid duplicate handlers if this runs more than once
    if not root.handlers:
        root.addHandler(handler)
    root.propagate = False
    _configured = True


def get_logger(name):
    """Return a logger for a named component (e.g. 'render', 'server').

    Usage:
        from core.logging_util import get_logger
        log = get_logger("render")
        log.info("report generated for %s", student_id)
        log.warning("attendance data missing")
        log.error("trend section failed: %s", err)
    """
    _configure_once()
    return logging.getLogger("evora").getChild(name)
