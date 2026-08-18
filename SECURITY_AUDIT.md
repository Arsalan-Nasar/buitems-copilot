# Security Audit Record — BUITEMS Copilot

This file records the security testing and dependency audit performed on the
project, so the state is documented and reproducible.

## Dependency audit

Tool: `pip-audit` (checks installed packages against known vulnerability
databases — PyPA Advisory DB / OSV).

Method: audited the app's actual dependencies in an isolated environment (not the
whole machine, which produces misleading noise from unrelated system packages).

Result: **No known vulnerabilities** in any of the app's runtime dependencies:

| Package                   | Version  | Status |
|---------------------------|----------|--------|
| Flask                     | 3.1.3    | clean  |
| python-dotenv             | 1.2.2    | clean  |
| groq                      | 1.6.0    | clean  |
| matplotlib                | 3.11.1   | clean  |
| langchain-community       | 0.4.2    | clean  |
| langchain-text-splitters  | 1.1.2    | clean  |
| langchain-huggingface     | 1.2.2    | clean  |
| faiss-cpu                 | 1.15.0   | clean  |
| sentence-transformers     | 5.7.0    | clean  |

(The only findings were in `pip` itself — the installer tool, not a runtime
dependency of the app — and do not affect the deployed application.)

### How to re-run the audit
```
python -m pip install pip-audit
python -m pip install -r requirements.txt
python -m pip -m pip_audit        # or: pip-audit
```
Re-run periodically; new vulnerabilities are discovered over time even in
currently-clean packages.

## Automated test suites

All run locally with `python <file>.py`. Every one must be green before deploy.

| Suite                  | What it protects                                   |
|------------------------|----------------------------------------------------|
| test_authz.py          | students can only read their own data              |
| test_pii.py            | no student PII reaches the third-party LLM (Groq)  |
| test_audit.py          | events are logged; the log never contains PII      |
| test_xss.py            | no injected script can execute in the browser      |
| test_headers.py        | defensive HTTP security headers present            |
| test_dos.py            | rate limiting + request-size caps (abuse defense)  |
| pentest.py             | 6 attack surfaces, fingerprinted leak detection    |
| test_correctness.py    | CGPA / fees / attendance math is correct           |
| test_edge_cases.py     | no crash on messy / incomplete / missing data      |
| test_comprehension.py  | understands typos, casual, mixed-language input     |
| test_goal_planner.py   | goal-target extraction is correct                  |
| stress_test.py         | routing decisions (incl. injection & Roman Urdu)   |

## Known limitations / deployment requirements (not code-level)

These must be handled at deployment, in front of the app:
- **HTTPS/TLS** must terminate before the app (HSTS header assumes this).
- **DDoS**: application-layer rate limiting cannot stop a large distributed
  attack — needs Cloudflare / reverse proxy / university firewall.
- **Audit log storage** should be append-only / tamper-evident in production.
- **Real portal auth**: `get_logged_in_id()` must read the verified student id
  from the portal session token at integration time.
