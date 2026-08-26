# BUITEMS Copilot

**An AI academic assistant for BUITEMS students — your whole portal, answered in one place.**

BUITEMS Copilot lets students check their results, CGPA, fees, attendance, and schedule by simply asking a question in plain English or Roman Urdu. Instead of clicking through the university portal's many pages and dense tables, students get a clear, accurate answer in seconds — calculated directly from their academic record, never guessed.

Built by **ZIRA Technologies**. _Where Intelligence Begins._

---

## Why it exists

The BUITEMS student portal (Oracle PeopleSoft) holds everything a student needs, but it is slow and scattered: grades are buried in dense tables, there is no clean report card, no single CGPA overview, and attendance and fees are hard to read at a glance. BUITEMS Copilot is a calm, intelligent layer over that data — ask a question, get a clear answer.

---

## Features

BUITEMS Copilot answers naturally in **English or Roman Urdu**, and every number it shows is calculated by code (never by the language model), so answers are always accurate.

- **Report Card** — every subject's marks and grade for a semester, in one clean table.
- **CGPA Dashboard** — all semesters, the trend, and the overall CGPA in a single view.
- **Fee Summary** — total billed, paid, and still due, in clear numbers.
- **Attendance Tracker** — per-course percentage with early low-attendance warnings.
- **What-If Simulator** — preview the grade and GPA a given final mark would produce.
- **Grade Predictor** — the marks needed in the final to reach a target grade.
- **CGPA Goal Planner** — the average GPA needed in remaining semesters to graduate at a target CGPA.
- **GPA Trend Chart** — a visual line chart of GPA across semesters.
- **Smart Alerts** — a quick look at fees due, low attendance, and pending results.
- **Schedule Assistant** — class timetable and day-wise schedule.
- **Document Q&A (RAG)** — answers fee and scholarship questions from official documents.
- **Roman Urdu support** — understands and replies the way most students actually type.

---

## How it works

The system follows a **trust-first** design: a small, reliable code engine performs all calculations (grades, GPA, CGPA, fees, attendance), while the language model is used only to phrase answers naturally and to translate replies into Roman Urdu. The model never touches the numbers.

```
Student question
      │
      ▼
  Router  ──►  detects intent + language
      │
      ▼
  Skill (report card, fees, attendance, …)
      │
      ├─►  Grading engine  (marks → grade → GPA/CGPA)
      ├─►  Student data
      └─►  Document search (RAG) for policy questions
      │
      ▼
  Clear answer  (in English or Roman Urdu)
```

### Marking scheme

Calculations use the real BUITEMS scheme — **Mid 25 + Final 50 + Sessional 25 = 100** — with the official grade scale (A at 85, down to D at 50).

---

## Tech stack

- **Language:** Python
- **Backend / Interface:** Flask, with a custom responsive front-end (HTML, CSS, JavaScript)
- **AI / NLP:** Groq (Llama models) for natural phrasing and Roman Urdu
- **Document Q&A:** LangChain, FAISS, HuggingFace embeddings (RAG)
- **Data visualisation:** Matplotlib (GPA trend chart)

---

## Project structure

```
buitems-copilot/
├── server.py            Flask backend + chat API
├── app.py               Gradio version (alternate interface)
├── config.py            settings and keys
├── core/
│   ├── router.py        routes each message to the right skill
│   ├── grading.py       the calculation engine (marks → GPA/CGPA)
│   ├── language.py      English / Roman Urdu detection
│   └── roman_urdu.py    Roman Urdu reply formatting
├── skills/              one file per feature
├── knowledge/
│   ├── rag.py           document question-answering
│   └── docs/            source documents
├── data/                sample student data
├── templates/           the web interface
└── static/              styles, scripts, assets
```

---

## Running locally

```bash
# 1. install dependencies
pip install flask groq python-dotenv langchain langchain-community \
            langchain-huggingface langchain-text-splitters faiss-cpu \
            sentence-transformers matplotlib

# 2. add your API key
#    create a .env file containing:
#    GROQ_API_KEY=your_key_here

# 3. run the app
python server.py
#    then open http://127.0.0.1:5000
```

> Note: the data in this repository is sample data for demonstration. The production version is designed to connect to the university portal through an authorised, secure integration.

---

## Team

| | | |
|---|---|---|
| **Arsalan Nasar** | Founder & Lead Developer | Architecture, engine, product |
| **Zarak Khan** | Documents & Retrieval | RAG and document Q&A |
| **Sami Ullah** | Interface & Testing | UI and quality |

Built by **ZIRA Technologies** — _Where Intelligence Begins._

---

## Status

Active development. The core assistant is complete and working; portal integration and the university-facing experience are planned in collaboration with BUITEMS.

---

## License

This project is shared for demonstration and educational purposes. Please contact the team before reuse.
