# Archived files — chat/LLM version

These files belong to the original **chat + LLM** version of BUITEMS Copilot.
They are kept for reference (and in case a future internet-connected deployment
wants them), but are NOT used by the current **report-generator** version, which
runs fully offline with no external LLM calls.

Retired because the BUITEMS portal runs on a closed university network where
external LLM (Groq) calls are not suitable:

- `router.py`        — chat intent router (no chat = not needed)
- `roman_urdu.py`    — Roman Urdu translation via Groq (external LLM call)
- `pii.py`           — PII masking for LLM calls (no LLM = not needed)
- `rag.py`           — document Q&A via LangChain/FAISS/Groq (external)
- `guide.html`       — chat UI guide page
- `stress_test.py`, `test_comprehension.py`, `test_pii.py` — router/LLM tests
- `test_dos.py`, `test_xss.py`, `test_headers.py`, `test_audit.py`, `pentest.py`
  — tested the chat server flow; will be rewritten for the report server.

The security *logic* they proved (XSS escaping, headers, audit, rate limiting)
is being carried into the new report server, with fresh tests.
