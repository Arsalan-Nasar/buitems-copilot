# core/authz.py — THE AUTHORIZATION LAYER (the one and only door to student data)
#
# PLAIN-ENGLISH PURPOSE:
# This file's ONLY job is to make sure a logged-in student can read ONLY their
# own records — enforced here, in code, so no message a user types can ever
# change whose data comes back.
#
# GOLDEN RULE:
#   The LOGGED-IN identity decides whose data is returned.
#   The user's request does NOT get to pick a different student.
#
# Every skill must fetch data through this door. No skill touches the raw
# database directly. That way there is exactly ONE place to secure, review,
# and log — instead of the security being scattered (and forgotten) across
# ten different skill files.

class AuthorizationError(Exception):
    """Raised when someone tries to access data they are not allowed to see."""
    pass


def fetch_student(database, logged_in_id, requested_id=None):
    """Return ONLY the logged-in student's record.

    Args:
        database:      the full student store (dict of {student_id: record}).
                       In real integration this is the portal/DB connection.
        logged_in_id:  the id proven at login. THIS decides whose data returns.
        requested_id:  whatever id the request *asked* for. Intentionally ignored
                       for access control — it can only ever be the caller's own.

    Security behaviour:
        - If requested_id is given and it is NOT the logged-in student, we do NOT
          return the other student. We refuse — loudly — rather than silently
          returning the wrong person, so the attempt is visible and log-able.
        - A blank/None request simply returns the logged-in student's own data.
    """
    if logged_in_id is None:
        # No proven identity = no data. Never guess.
        raise AuthorizationError("No authenticated student; access denied.")

    # The core rule: if the request names a DIFFERENT student, refuse.
    if requested_id is not None and str(requested_id) != str(logged_in_id):
        raise AuthorizationError(
            f"Access denied: a student may only read their own records "
            f"(logged in as {logged_in_id}, requested {requested_id})."
        )

    record = database.get(str(logged_in_id))
    if record is None:
        # Authenticated, but no record found — that's a data problem, not a leak.
        raise AuthorizationError(f"No record found for student {logged_in_id}.")

    return record


def fetch_student_safe(database, logged_in_id, requested_id=None):
    """Same as fetch_student, but returns None instead of raising.

    Useful where the caller wants a simple 'my data or nothing' with no
    exception handling. Still NEVER returns another student's data.
    """
    try:
        return fetch_student(database, logged_in_id, requested_id)
    except AuthorizationError:
        return None
