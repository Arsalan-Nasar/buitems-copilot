# report/render.py — THE REPORT UI (premium BUITEMS-themed HTML report).
#
# PLAIN ENGLISH:
# Turns the structured report (R1) + intelligence (R2) into one self-contained,
# animated, mobile-first HTML page in BUITEMS's official blue + gold identity.
# No external calls, no LLM. Every value HTML-escaped (XSS-safe).
#
# Design language: deep BUITEMS navy hero, markhor-gold health ring (animated
# sweep + count-up), self-drawing GPA trend chart, staggered card reveals,
# Sora display type + Inter body. Fully responsive; respects reduced-motion.

import html as _html
import json as _json

EM_DASH = "\u2014"   # kept out of f-string expressions (older-Python safe)


def _esc(v):
    return _html.escape(str(v), quote=True)


# ---------------------------------------------------------------------------
# Small render helpers
# ---------------------------------------------------------------------------
def _band_from_score(score):
    if score >= 85: return "Excellent"
    if score >= 70: return "Good"
    if score >= 55: return "Fair"
    if score >= 40: return "Needs Attention"
    return "At Risk"


def _breakdown_rows(breakdown):
    out = []
    for b in breakdown:
        pct = round(b["points"] / b["max"] * 100, 1) if b["max"] else 0
        label = _esc(b["factor"].split(" (")[0])   # "Academic (CGPA)" -> "Academic"
        out.append(
            f'<div class="bd-row"><span class="lb">{label}</span>'
            f'<span class="bd-track"><span class="bd-fill" style="--w:{pct}%"></span></span>'
            f'<span class="bd-val num">{_esc(b["points"])}/{_esc(b["max"])}</span></div>'
        )
    return "".join(out)


def _flag_cards(flags):
    icon = {"red": "!", "amber": "!", "green": "\u2713"}
    out = []
    for f in flags:
        lvl = f["level"] if f["level"] in ("red", "amber", "green") else "green"
        out.append(
            f'<div class="flag {lvl} rise"><div class="flag-ico">{icon[lvl]}</div>'
            f'<div class="flag-tx">{_esc(f["message"])}</div></div>'
        )
    return "".join(out)


def _sw_items(items, direction):
    if not items:
        return '<div class="sw-item"><span class="muted" style="font-size:13px">None identified yet.</span></div>'
    cls = "up" if direction == "up" else "dn"
    out = []
    for c in items:
        out.append(
            f'<div class="sw-item"><span class="sw-badge {cls}">{_esc(c["grade"])}</span>'
            f'<span>{_esc(c["title"])}</span></div>'
        )
    return "".join(out)


def _attendance_rows(attendance):
    threshold = attendance["threshold"]
    out = []
    for c in attendance["courses"]:
        pct = c["percent"]
        if pct is None:
            bar = f'<span class="att-pct" style="color:var(--muted)">{EM_DASH}</span>'
        else:
            color = "var(--green)" if pct >= threshold else "var(--red)"
            bar = (f'<span class="att-bar"><span class="att-track">'
                   f'<span class="att-f" style="width:{_esc(pct)}%;background:{color}"></span></span>'
                   f'<span class="att-pct" style="color:{color}">{_esc(pct)}%</span></span>')
        out.append(
            f'<tr><td>{_esc(c["title"])}</td>'
            f'<td class="c num">{_esc(c["present"])}/{_esc(c["total"])}</td>'
            f'<td class="r">{bar}</td></tr>'
        )
    return "".join(out)


def _recovery_note(recovery):
    parts = []
    for a in recovery:
        if a["classes_to_attend"]:
            parts.append(
                f'<div class="rec"><span>&#9873;</span><div>To reach 75% in '
                f'<b>{_esc(a["title"])}</b>, attend the next <b>{_esc(a["classes_to_attend"])}</b> '
                f'classes without missing any.</div></div>'
            )
    return "".join(parts)


def _combined_semesters(report):
    """ONE combined section (per the layout note): each semester card lists its
    courses, and each course expands to show its Mid/Final/Sessional breakdown.
    Rendered two-per-row on wide screens. Merges the old Semester Breakdown +
    Marks Detail into a single, cleaner block."""
    semesters = report["semesters"]
    # map semester_id -> its marks breakdown (per-course component detail)
    mb_by_sem = {}
    for msem in report["marks_breakdown"]["semesters"]:
        by_code = {}
        for c in msem["courses"]:
            by_code[(c["code"], c["title"])] = c["breakdown"]
        mb_by_sem[str(msem["semester"])] = by_code

    def _bar(comp):
        pct = comp["percent"]
        if pct is None:
            return ('<div class="md-row"><span class="md-lbl">' + _esc(comp["component"])
                    + '</span><span class="md-track"></span><span class="md-val">'
                    + EM_DASH + '</span></div>')
        color = "var(--green)" if pct >= 80 else ("var(--blue)" if pct >= 60 else "var(--red)")
        return ('<div class="md-row"><span class="md-lbl">' + _esc(comp["component"])
                + '</span><span class="md-track"><span class="md-fill" style="width:'
                + str(pct) + '%;background:' + color + '"></span></span>'
                '<span class="md-val num">' + _esc(comp["obtained"]) + '/' + _esc(comp["max"])
                + '</span></div>')

    cards = []
    for s in sorted(semesters,
                    key=lambda x: int(x["semester"]) if str(x["semester"]).isdigit() else 0,
                    reverse=True):
        if not s["courses"]:
            continue
        sem_marks = mb_by_sem.get(str(s["semester"]), {})
        course_rows = []
        for c in s["courses"]:
            grade = c["grade"]
            posted = grade is not None
            chip = (f'<span class="chip">{_esc(grade)}</span>' if posted
                    else f'<span class="chip" style="background:var(--line);color:var(--muted)">{EM_DASH}</span>')
            bd = sem_marks.get((c["code"], c["title"]))
            if posted and bd:
                bars = "".join(_bar(b) for b in bd)
                course_rows.append(
                    '<details class="md-course"><summary>'
                    '<span class="md-title">' + _esc(c["title"]) + '</span>'
                    '<span class="md-summary">' + chip + '</span></summary>'
                    '<div class="md-body">' + bars + '</div></details>'
                )
            else:
                course_rows.append(
                    '<div class="md-course static"><div class="md-flat">'
                    '<span class="md-title">' + _esc(c["title"]) + '</span>' + chip
                    + '</div></div>'
                )
        if s["status"] == "complete" and s["gpa"] is not None:
            gpa_badge = f'<span class="sem-gpa done num">GPA {_esc(s["gpa"])}</span>'
        else:
            gpa_badge = '<span class="sem-gpa prog">In progress</span>'
        term = f'<small>&middot; {_esc(s["term"])}</small>' if s["term"] else ""
        cards.append(
            '<div class="sem"><div class="sem-h">'
            '<span class="t">Semester ' + _esc(s["semester"]) + ' ' + term + '</span>'
            + gpa_badge + '</div><div class="sem-courses">' + "".join(course_rows) + '</div></div>'
        )
    return '<div class="sem-grid">' + "".join(cards) + '</div>'


def _suggestion_items(suggestions):
    out = []
    for i, s in enumerate(suggestions, 1):
        out.append(f'<li><span class="n">{i}</span><div>{_esc(s)}</div></li>')
    return "".join(out)


# ---------------------------------------------------------------------------
# A short original reflection (written by us, not scripture) that carries the
# spirit of seeking knowledge, effort with trust, and hope. Anchored by the
# well-known du'a "Rabbi zidni ilma" (My Lord, increase me in knowledge).
# Deliberately NOT a direct Quran/Hadith quote to keep it appropriate and safe
# for an official university tool.
# ---------------------------------------------------------------------------
def _islamic_reminder():
    return (
        '<div class="ir-card glow rise">'
        '<div class="ir-arabic">\u0631\u0628\u0651\u0650 \u0632\u0650\u062f\u0652\u0646\u0650\u064a \u0639\u0650\u0644\u0652\u0645\u064b\u0627</div>'
        '<div class="ir-translit">Rabbi zidni \u02bfilma \u2014 \u201cMy Lord, increase me in knowledge.\u201d</div>'
        '<div class="ir-quote">Give your effort and trust your Lord \u2014 for He suffices '
        'the one who relies on Him, He grants the one who seeks, and after every '
        'hardship, He brings ease.</div>'
        '</div>'
    )


def _marks_detail(marks_breakdown):
    """Expandable per-course marks breakdown (Mid / Final / Sessional vs max).
    Mirrors the portal's 'View My Assignments'. Uses native <details> so each
    course expands on click with no JavaScript. Older-Python-safe (plain concat)."""
    # component colour by percentage
    def _bar(component):
        pct = component["percent"]
        if pct is None:
            return ('<div class="md-row"><span class="md-lbl">'
                    + _esc(component["component"]) + '</span>'
                    '<span class="md-track"></span>'
                    '<span class="md-val">' + EM_DASH + '</span></div>')
        if pct >= 80:
            color = "var(--green)"
        elif pct >= 60:
            color = "var(--blue)"
        else:
            color = "var(--red)"
        return ('<div class="md-row"><span class="md-lbl">'
                + _esc(component["component"]) + '</span>'
                '<span class="md-track"><span class="md-fill" style="width:'
                + str(pct) + '%;background:' + color + '"></span></span>'
                '<span class="md-val num">' + _esc(component["obtained"])
                + '/' + _esc(component["max"]) + '</span></div>')

    sections = []
    # newest semester first, only semesters with at least one posted course
    sems = sorted(marks_breakdown["semesters"],
                  key=lambda x: int(x["semester"]) if str(x["semester"]).isdigit() else 0,
                  reverse=True)
    for s in sems:
        posted_courses = [c for c in s["courses"] if c["total"] is not None]
        if not posted_courses:
            continue
        course_blocks = []
        for c in posted_courses:
            bars = "".join(_bar(b) for b in c["breakdown"])
            term = ' &middot; ' + _esc(s["term"]) if s["term"] else ""
            course_blocks.append(
                '<details class="md-course"><summary>'
                '<span class="md-title">' + _esc(c["title"]) + '</span>'
                '<span class="md-summary"><span class="md-total num">'
                + _esc(c["total"]) + '/100</span>'
                '<span class="chip">' + _esc(c["grade"]) + '</span></span>'
                '</summary><div class="md-body">' + bars + '</div></details>'
            )
        sections.append(
            '<div class="md-sem"><div class="md-sem-h">Semester '
            + _esc(s["semester"]) + (' <span class="muted">&middot; ' + _esc(s["term"])
            + '</span>' if s["term"] else "") + '</div>'
            + "".join(course_blocks) + '</div>'
        )
    if not sections:
        return ('<div class="card"><p class="muted" style="font-size:13px">'
                'Detailed marks appear here once results are posted.</p></div>')
    return "".join(sections)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def _degree_progress(credits):
    """The degree-completion centerpiece — highlighted as a marketing moment
    (navy/blue gradient, gold fill, glowing edge). Adapts wording to the program
    level: a BS/MS shows progress toward the degree; a PhD shows the coursework
    phase (since a doctorate is research-based, not credit-driven)."""
    pct = credits["percent"]
    est = " (estimated)" if credits.get("is_estimate") else ""
    if credits.get("coursework_only"):
        heading = "Coursework Progress"
        caption = (str(credits["completed"]) + " of " + str(credits["total_required"])
                   + " coursework credit hours" + est
                   + " \u2014 the doctorate is completed through research and dissertation")
    else:
        heading = "Degree Progress"
        caption = (str(credits["completed"]) + " of " + str(credits["total_required"])
                   + " credit hours toward your degree" + est)
    return (
        f'<div class="lbl rise d4" id="progress"><span class="dot"></span><b>{heading}</b><span class="rule"></span></div>'
        f'<div class="card dp-hero glow rise d4">'
        f'<div class="dp-top"><span class="dp-pct num">{_esc(pct)}%</span>'
        f'<span class="dp-cap">{_esc(caption)}</span></div>'
        f'<div class="dp-track"><span class="dp-fill" style="--w:{_esc(pct)}%"></span></div>'
        f'<div class="dp-legend">'
        f'<span><b class="num">{_esc(credits["completed"])}</b> completed</span>'
        f'<span><b class="num">{_esc(credits["in_progress"])}</b> in progress</span>'
        f'<span><b class="num">{_esc(credits["remaining"])}</b> remaining</span>'
        f'</div></div>'
    )


def render_report(report, intelligence):
    st = report["student"]
    hs = intelligence["health_score"]
    cg = report["cgpa"]
    fe = report["fees"]
    trend = report["trend"]

    # health score may be None for a brand-new student with no results yet.
    score = hs["score"]
    is_pending = hs.get("pending") or score is None
    score_js = 0 if is_pending else score          # JS count-up target
    score_display = "\u2013" if is_pending else score
    band = hs.get("band") or _band_from_score(score or 0)

    # trend data -> JSON for the JS chart (now includes % change per semester)
    trend_points = [{"s": _esc(p["semester"]), "g": p["gpa"],
                     "c": p.get("change_pct")} for p in trend["points"]]
    trend_json = _json.dumps(trend_points)
    _has_trend = len(trend_points) >= 2
    _best = trend.get("best"); _low = trend.get("lowest")
    best_txt = f'{_best["gpa"]} (Sem {_esc(_best["semester"])})' if _best else "—"
    low_txt = f'{_low["gpa"]} (Sem {_esc(_low["semester"])})' if _low else "—"
    dir_map = {"up": "Trending up", "down": "Trending down", "flat": "Holding steady"}
    dir_txt = dir_map.get(trend["direction"], "")
    dir_arrow = "&#9650;" if trend["direction"] == "up" else ("&#9660;" if trend["direction"] == "down" else "&#9644;")
    dir_color = "var(--green)" if trend["direction"] == "up" else (
        "var(--red)" if trend["direction"] == "down" else "var(--muted)")

    cg_txt = cg["cgpa"] if cg["cgpa"] is not None else EM_DASH
    standing = _esc(cg["standing"].replace("_", " ")) if cg.get("standing") else ""

    fee_due = f"Rs {fe['due']:,}" if fe["due"] > 0 else "Rs 0"
    fee_total = f"of Rs {fe['total']:,} &middot; still due" if fe["due"] > 0 else "All clear"
    fee_pill = ("warn", "Outstanding") if fe["status"] == "outstanding" else ("good", "Cleared")

    # Build the trend card's inner HTML OUTSIDE the f-string (older-Python-safe:
    # avoids nested triple-quotes/braces inside an f-string expression). Placed
    # here, after all of cg_txt/best_txt/low_txt/dir_* are defined.
    if _has_trend:
        trend_inner = (
            '<div class="trend-head"><div class="trend-stats">'
            '<span class="tstat"><i>CGPA</i><b class="num">' + _esc(cg_txt) + '</b></span>'
            '<span class="tstat"><i>Peak</i><b class="num">' + best_txt + '</b></span>'
            '<span class="tstat"><i>Lowest</i><b class="num">' + low_txt + '</b></span>'
            '</div><span class="dir" style="color:' + dir_color + '">'
            + dir_arrow + ' ' + _esc(dir_txt) + '</span></div>'
            '<svg class="chart" viewBox="0 0 640 260">'
            '<defs>'
            '<linearGradient id="gLine" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0" stop-color="#1e5aa8"/><stop offset="1" stop-color="#123a63"/></linearGradient>'
            '<linearGradient id="gGold" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="rgba(30,90,168,.18)"/>'
            '<stop offset="1" stop-color="rgba(30,90,168,0)"/></linearGradient>'
            '</defs>'
            '<g id="grid"></g>'
            '<path class="area" id="area"/><polyline class="line" id="line" points=""/>'
            '<g id="dots"></g><g id="xlabels"></g><g id="changes"></g>'
            '</svg>'
        )
    else:
        trend_inner = (
            '<div style="text-align:center;padding:40px 20px;color:var(--muted)">'
            '<div style="font-family:Sora,sans-serif;font-weight:700;font-size:18px;'
            'color:var(--navy);margin-bottom:6px">Trend coming soon</div>'
            '<div style="font-size:13px">A GPA trend chart appears once you have '
            'at least two completed semesters.</div></div>'
        )

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Academic Report {EM_DASH} {_esc(st["name"])}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&family=Amiri:wght@400;700&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  :root{{
    --navy:#12227a;--royal:#1e3a9e;--blue:#2b4ba8;--blue-br:#3f7fd6;--blue-soft:#e9eefb;
    --gold:#e29a2e;--gold-lt:#f4b842;--gold-deep:#c47f1e;--gold-soft:#fdf3df;
    --bg:#f6f8fb;--card:#fff;--ink:#12263f;--muted:#66788f;
    --line:#e6ecf3;--green:#1f9d6b;--green-soft:#e5f5ee;--amber:#dd8a1a;--yellow-soft:#fcf4dc;--red:#d0553f;
    --shadow:0 1px 2px rgba(10,37,64,.03),0 4px 16px rgba(10,37,64,.05);
    --shadow-lg:0 8px 30px rgba(10,37,64,.10);
    --r:14px;
  }}
  /* animated glowing blue+gold edges (BUITEMS) */
  .glow{{position:relative}}
  .glow::before{{content:'';position:absolute;inset:-2px;border-radius:inherit;z-index:-1;
    background:linear-gradient(120deg,var(--blue-br),var(--gold-lt),var(--blue-br),var(--gold-lt));
    background-size:300% 300%;animation:glowmove 6s ease infinite;
    filter:blur(7px);opacity:.35}}
  .glow{{box-shadow:0 0 0 1px rgba(43,75,168,.10)}}
  @keyframes glowmove{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}

  body{{background:var(--bg);color:var(--ink);font-family:'Poppins',system-ui,-apple-system,sans-serif;font-size:13.5px;line-height:1.6;-webkit-font-smoothing:antialiased}}
  .num{{font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}}
  .disp{{font-family:'Poppins',sans-serif}}
  .muted{{color:var(--muted)}}

  /* sticky top nav */
  .nav{{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.85);backdrop-filter:saturate(180%) blur(12px);
    border-bottom:1px solid var(--line)}}
  .nav-in{{max-width:840px;margin:0 auto;padding:11px 20px;display:flex;align-items:center;gap:16px}}
  .nav-brand{{display:flex;align-items:center;gap:9px;flex-shrink:0}}
  .nav-mark{{width:34px;height:34px;border-radius:50%;overflow:hidden;flex-shrink:0;
    box-shadow:0 1px 4px rgba(10,37,64,.18)}}
  .nav-mark img{{width:100%;height:100%;object-fit:cover;display:block}}
  .nav-title{{font-family:'Poppins';font-weight:600;font-size:14px;letter-spacing:-.01em}}
  .nav-links{{display:flex;gap:4px;margin-left:auto;overflow-x:auto;scrollbar-width:none}}
  .nav-links::-webkit-scrollbar{{display:none}}
  .nav-links a{{font-size:12.5px;color:var(--muted);text-decoration:none;padding:6px 11px;border-radius:8px;
    white-space:nowrap;transition:background .15s,color .15s;font-weight:500}}
  .nav-links a:hover{{background:var(--blue-soft);color:var(--blue)}}

  .wrap{{max-width:840px;margin:0 auto;padding:26px 20px 70px}}

  /* hero — refined, calmer */
  .hero{{background:linear-gradient(140deg,#0a2540 0%,#143a66 60%,#0d2d4f 100%);border-radius:20px;
    padding:26px 28px;color:#fff;position:relative;overflow:hidden;box-shadow:var(--shadow-lg)}}
  .hero::before{{content:"";position:absolute;top:-45%;right:-8%;width:300px;height:300px;
    background:radial-gradient(circle,rgba(201,150,46,.20),transparent 62%)}}
  .hero-markhor{{position:absolute;right:-30px;bottom:-40px;width:260px;height:260px;object-fit:contain;opacity:.10;z-index:0;pointer-events:none;filter:brightness(2)}}
  .hero-inner{{position:relative;z-index:1;display:grid;grid-template-columns:auto 1fr;gap:28px;align-items:center}}
  .ring-wrap{{width:120px;height:120px;position:relative}}
  .ring-num{{position:absolute;inset:0;display:grid;place-items:center;text-align:center}}
  .ring-num b{{font-family:'Poppins';font-weight:700;font-size:34px;line-height:1;letter-spacing:-.02em;color:#fff}}
  .ring-num i{{font-style:normal;font-size:10px;color:rgba(255,255,255,.55);letter-spacing:.08em;margin-top:1px;display:block}}
  .hero-name{{font-family:'Poppins';font-weight:600;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--gold-lt);margin-bottom:3px}}
  .hero-sub{{font-size:12.5px;color:rgba(255,255,255,.68);margin-bottom:16px}}
  .band-lg{{font-family:'Poppins';font-weight:700;font-size:22px;letter-spacing:-.01em;line-height:1.1;margin-bottom:3px}}
  .band-lg small{{display:block;font-size:10px;font-weight:500;letter-spacing:.09em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-top:5px;margin-bottom:15px;font-family:'Poppins'}}
  .bd{{display:flex;flex-direction:column;gap:9px}}
  .bd-row{{display:grid;grid-template-columns:88px 1fr auto;gap:12px;align-items:center;font-size:11.5px}}
  .bd-row .lb{{color:rgba(255,255,255,.72)}}
  .bd-track{{height:6px;background:rgba(255,255,255,.13);border-radius:20px;overflow:hidden}}
  .bd-fill{{height:100%;border-radius:20px;background:linear-gradient(90deg,var(--gold),var(--gold-lt));width:0;transition:width 1.1s cubic-bezier(.22,1,.36,1) .3s}}
  .bd-val{{color:#fff;font-weight:600;font-variant-numeric:tabular-nums;font-size:11px}}

  /* section labels */
  .lbl{{display:flex;align-items:center;gap:10px;margin:34px 2px 15px;scroll-margin-top:66px}}
  .lbl b{{font-family:'Poppins';font-weight:700;font-size:15px;letter-spacing:-.01em;color:var(--royal);position:relative;padding-bottom:6px}}
  .lbl b::after{{content:'';position:absolute;left:0;bottom:0;width:100%;height:2.5px;border-radius:2px;background:linear-gradient(90deg,var(--gold-lt),var(--gold),rgba(226,154,46,0))}}
  .lbl .dot{{display:none}}
  .lbl .rule{{flex:1;height:1px;background:var(--line);align-self:flex-end;margin-bottom:8px}}

  /* priority flags */
  .flags{{display:flex;flex-direction:column;gap:9px}}
  .flag{{display:flex;gap:13px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-left-width:3px;border-radius:12px;padding:13px 15px;box-shadow:var(--shadow)}}
  .flag.red{{border-left-color:var(--red)}}.flag.amber{{border-left-color:var(--amber)}}.flag.green{{border-left-color:var(--green)}}
  .flag-ico{{width:22px;height:22px;border-radius:7px;flex-shrink:0;display:grid;place-items:center;font-weight:700;font-size:12px;color:#fff;font-family:'Poppins'}}
  .flag.red .flag-ico{{background:var(--red)}}.flag.amber .flag-ico{{background:var(--amber)}}.flag.green .flag-ico{{background:var(--green)}}
  .flag-tx{{font-size:13px;padding-top:2px;color:#33455c}}

  /* cards + grid */
  .grid{{display:grid;gap:12px}}.g2{{grid-template-columns:1fr 1fr}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:18px;box-shadow:var(--shadow)}}
  .card h3{{font-family:'Poppins';font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
  .stat{{font-family:'Poppins';font-weight:700;font-size:28px;letter-spacing:-.01em;line-height:1}}
  .stat.sm{{font-size:22px}}
  .stat-sub{{font-size:12px;color:var(--muted);margin-top:5px}}
  .pill{{display:inline-block;font-size:10.5px;font-weight:600;padding:3px 9px;border-radius:20px;margin-top:9px;text-transform:capitalize}}
  .pill.good{{background:var(--blue-soft);color:var(--blue)}}.pill.warn{{background:var(--gold-soft);color:#9a6c14}}
  .pill.gold{{background:var(--gold-soft);color:var(--gold-deep)}}
  .cgpa-card{{border-top:3px solid var(--gold)}}
  .cgpa-card .stat{{color:var(--royal)}}


  /* ============ THE GPA TREND — the shareable centerpiece ============ */
  .trend-card{{background:linear-gradient(160deg,#fff,#fbfcfe);border:1px solid var(--line);border-radius:18px;
    padding:22px 22px 16px;box-shadow:var(--shadow-lg);position:relative;overflow:hidden}}
  .trend-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}}
  .trend-stats{{display:flex;gap:22px}}
  .tstat{{display:flex;flex-direction:column;gap:2px}}
  .tstat i{{font-style:normal;font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
  .tstat b{{font-family:'Poppins';font-weight:700;font-size:16px;color:var(--navy)}}
  .dir{{font-size:12px;font-weight:600;display:inline-flex;align-items:center;gap:4px;padding:5px 11px;border-radius:20px;background:var(--bg)}}
  .trend-wm{{position:absolute;right:18px;bottom:12px;font-family:'Poppins';font-weight:600;font-size:10px;
    letter-spacing:.14em;text-transform:uppercase;color:var(--muted);opacity:.5}}
  svg.chart{{width:100%;height:auto;display:block;overflow:visible}}
  .chart .grid-l{{stroke:var(--line);stroke-width:1}}
  .chart .ax{{fill:var(--muted);font-size:11px;font-family:'Poppins'}}
  .chart .area{{fill:url(#gGold);opacity:0}}
  .chart .line{{fill:none;stroke:url(#gLine);stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1200;stroke-dashoffset:1200;animation:draw 1.7s cubic-bezier(.4,0,.2,1) .4s forwards}}
  @keyframes draw{{to{{stroke-dashoffset:0}}}}
  .chart .dot{{fill:#fff;stroke:var(--royal);stroke-width:3;opacity:0;animation:pop .4s ease forwards}}
  .chart .dv{{fill:var(--navy);font-family:'Poppins';font-weight:700;font-size:13px;text-anchor:middle;opacity:0;animation:pop .4s ease forwards}}
  .chart .chg{{font-family:'Poppins';font-weight:600;font-size:10.5px}}
  .chart .chg.up{{fill:var(--green)}}.chart .chg.down{{fill:var(--red)}}
  @keyframes pop{{to{{opacity:1}}}}
  .dl-btn{{margin-top:12px;width:100%;padding:12px;border:1px solid var(--line);background:var(--card);
    color:var(--royal);font-family:'Poppins';font-weight:600;font-size:12.5px;border-radius:12px;cursor:pointer;transition:background .2s,border-color .2s;box-shadow:var(--shadow)}}
  .dl-btn:hover{{background:var(--blue-soft);border-color:var(--blue)}}

  /* degree progress */
  .dp-hero{{background:linear-gradient(135deg,#12227a,#2b4ba8);color:#fff;border:none;position:relative;overflow:hidden}}
  .dp-hero::before{{content:'';position:absolute;top:-40%;right:-6%;width:240px;height:240px;background:radial-gradient(circle,rgba(244,184,66,.28),transparent 62%)}}
  .dp-hero .dp-pct{{color:var(--gold-lt)}}
  .dp-hero .dp-cap{{color:rgba(255,255,255,.72)}}
  .dp-hero .dp-track{{background:rgba(255,255,255,.16)}}
  .dp-hero .dp-fill{{background:linear-gradient(90deg,var(--gold),var(--gold-lt))}}
  .dp-hero .dp-legend{{color:rgba(255,255,255,.75)}}
  .dp-hero .dp-legend b{{color:#fff}}
  .dp-top{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:11px}}
  .dp-pct{{font-family:'Poppins';font-weight:700;font-size:28px;letter-spacing:-.01em;color:var(--royal)}}
  .dp-cap{{font-size:12px;color:var(--muted)}}
  .dp-track{{height:10px;background:var(--line);border-radius:20px;overflow:hidden;margin-bottom:12px}}
  .dp-fill{{display:block;height:100%;border-radius:20px;background:linear-gradient(90deg,var(--royal),var(--blue));width:0;transition:width 1.3s cubic-bezier(.22,1,.36,1) .4s}}
  .dp-legend{{display:flex;gap:20px;font-size:12px;color:var(--muted)}}
  .dp-legend b{{color:var(--ink);font-family:'Poppins';font-weight:700;margin-right:4px}}

  /* strengths / weaknesses */
  .card.strengths{{border-top:3px solid var(--green)}}
  .card.needsfocus{{border-top:3px solid var(--gold)}}
  .card.strengths h3{{color:var(--green)}}
  .card.needsfocus h3{{color:var(--gold-deep)}}
  .sw{{display:flex;flex-direction:column;gap:8px}}
  .sw-item{{display:flex;align-items:center;gap:10px}}
  .sw-badge{{font-family:'Poppins';font-weight:700;font-size:11px;min-width:36px;height:24px;padding:0 8px;border-radius:7px;display:grid;place-items:center}}
  .sw-badge.up{{background:var(--green-soft);color:var(--green)}}.sw-badge.dn{{background:var(--yellow-soft);color:#a5761a}}
  .sw-item span{{font-size:13px;color:#33455c}}

  /* tables */
  .tbl{{width:100%;border-collapse:collapse;font-size:13px}}
  .tbl th{{text-align:left;font-family:'Poppins';font-weight:600;font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);padding:0 8px 9px}}
  .tbl th.r,.tbl td.r{{text-align:right}}.tbl th.c,.tbl td.c{{text-align:center}}
  .tbl td{{padding:10px 8px;border-top:1px solid var(--line);color:#33455c}}
  .tbl tr:first-child td{{border-top:none}}
  .att-bar{{display:inline-flex;align-items:center;gap:8px}}
  .att-track{{width:50px;height:6px;background:var(--line);border-radius:20px;overflow:hidden}}
  .att-f{{height:100%;border-radius:20px}}
  .att-pct{{font-weight:700;font-variant-numeric:tabular-nums;font-size:12px;min-width:32px;text-align:right}}
  .chip{{font-family:'Poppins';font-weight:700;font-size:11px;padding:3px 9px;border-radius:6px;background:var(--blue-soft);color:var(--royal)}}
  .rec{{margin-top:13px;font-size:12px;color:#8a5a12;background:var(--gold-soft);border-radius:10px;padding:11px 13px;display:flex;gap:9px;align-items:flex-start}}
  .rec b{{color:#6e4708}}

  /* semester cards */
  .sem{{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px 18px;box-shadow:var(--shadow);margin-bottom:10px}}
  .sem-h{{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}}
  .sem-h .t{{font-family:'Poppins';font-weight:600;font-size:14px}}
  .sem-h .t small{{color:var(--muted);font-weight:400;font-family:'Poppins'}}
  .sem-gpa{{font-family:'Poppins';font-weight:700;font-size:11.5px;padding:4px 10px;border-radius:7px}}
  .sem-gpa.done{{background:linear-gradient(135deg,var(--gold),var(--gold-deep));color:#fff;box-shadow:0 2px 8px rgba(226,154,46,.35)}}
  .sem-gpa.prog{{background:var(--blue-soft);color:var(--blue)}}
  .sem-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}}
  .sem-courses{{display:flex;flex-direction:column;gap:6px;margin-top:10px}}
  .md-course.static .md-flat{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 14px}}
  .sem-courses .md-course{{margin-bottom:0}}
  .sem-courses .md-course summary{{padding:11px 14px}}
  .sem-courses .md-title{{font-size:12.5px}}

  /* marks detail */
  .md-sem{{margin-bottom:14px}}
  .md-sem-h{{font-family:'Poppins';font-weight:600;font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin:0 2px 8px}}
  .md-course{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin-bottom:7px;box-shadow:var(--shadow);overflow:hidden}}
  .md-course summary{{list-style:none;cursor:pointer;padding:13px 15px;display:flex;align-items:center;justify-content:space-between;gap:12px;user-select:none}}
  .md-course summary::-webkit-details-marker{{display:none}}
  .md-course summary::after{{content:"\\203A";color:var(--muted);font-size:17px;transition:transform .2s;margin-left:2px}}
  .md-course[open] summary::after{{transform:rotate(90deg)}}
  .md-title{{font-weight:500;font-size:13px;color:#33455c;flex:1}}
  .md-summary{{display:flex;align-items:center;gap:10px}}
  .md-total{{font-family:'Poppins';font-weight:700;font-size:12.5px;color:var(--navy)}}
  .md-body{{padding:3px 15px 14px;border-top:1px solid var(--line)}}
  .md-row{{display:grid;grid-template-columns:72px 1fr auto;gap:10px;align-items:center;padding:5px 0;font-size:12px}}
  .md-lbl{{color:var(--muted)}}
  .md-track{{height:6px;background:var(--line);border-radius:20px;overflow:hidden}}
  .md-fill{{display:block;height:100%;border-radius:20px}}
  .md-val{{font-variant-numeric:tabular-nums;color:var(--ink);font-weight:600;min-width:46px;text-align:right}}

  /* suggestions */
  .tips{{list-style:none;display:flex;flex-direction:column;gap:10px}}
  .tips li{{display:flex;gap:11px;font-size:13px;color:#33455c;align-items:flex-start}}
  .tips .n{{width:21px;height:21px;border-radius:6px;background:var(--blue-soft);color:var(--blue);font-family:'Poppins';font-weight:700;font-size:10.5px;display:grid;place-items:center;flex-shrink:0;margin-top:1px}}

  /* original reflection card (Rabbi zidni ilma) */
  .ir-card{{background:linear-gradient(160deg,#0b1f5c,#1e3a9e);border:none;border-radius:18px;
    padding:30px 28px;margin-top:34px;color:#fff;position:relative;overflow:hidden;box-shadow:var(--shadow-lg);text-align:center}}
  .ir-card::before{{content:'';position:absolute;top:-30%;left:50%;transform:translateX(-50%);width:280px;height:280px;
    background:radial-gradient(circle,rgba(244,184,66,.16),transparent 62%)}}
  .ir-arabic{{position:relative;z-index:1;font-family:'Amiri',serif;font-size:34px;font-weight:700;
    color:var(--gold-lt);line-height:1.4;margin-bottom:10px;direction:rtl}}
  .ir-translit{{position:relative;z-index:1;font-size:12.5px;color:rgba(255,255,255,.7);font-style:italic;
    margin-bottom:16px;letter-spacing:.02em}}
  .ir-quote{{position:relative;z-index:1;font-size:14.5px;line-height:1.7;font-weight:400;
    color:rgba(255,255,255,.94);max-width:560px;margin:0 auto}}
  /* ZIRA brand footer (real logo) */
  .brandfoot{{display:flex;align-items:center;justify-content:center;gap:18px;margin-top:24px;
    padding:20px 24px;background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);flex-wrap:wrap}}
  .bf-logo{{height:34px;width:auto;object-fit:contain}}
  .bf-line{{width:1px;height:34px;background:var(--line)}}
  .bf-txt{{text-align:left}}
  .bf-txt b{{display:block;font-family:'Poppins';font-weight:600;font-size:13.5px;color:var(--ink);line-height:1.2}}
  .bf-txt small{{font-size:11.5px;color:var(--muted)}}
  .foot{{text-align:center;margin-top:36px;padding-top:18px;border-top:1px solid var(--line);font-size:11.5px;color:var(--muted);display:flex;align-items:center;justify-content:center;gap:8px}}

  .rise{{opacity:0;transform:translateY(14px);animation:rise .65s cubic-bezier(.22,1,.36,1) forwards}}
  @keyframes rise{{to{{opacity:1;transform:none}}}}
  .d1{{animation-delay:.04s}}.d2{{animation-delay:.1s}}.d3{{animation-delay:.16s}}.d4{{animation-delay:.22s}}.d5{{animation-delay:.28s}}.d6{{animation-delay:.34s}}.d7{{animation-delay:.4s}}

  @media (max-width:720px){{
    .hero{{padding:22px 20px}}
    .hero-inner{{grid-template-columns:1fr;gap:20px;text-align:center}}
    .ring-wrap{{margin:0 auto}}.bd{{text-align:left}}.bd-row{{grid-template-columns:78px 1fr auto}}
    .g2{{grid-template-columns:1fr}}.sem-grid{{grid-template-columns:1fr}}.nav-title{{display:none}}
    .trend-stats{{gap:16px}}
  }}
  @media print{{
    .nav{{display:none}}body{{background:#fff}}.wrap{{max-width:100%;padding:0}}
    .rise{{opacity:1!important;transform:none!important}}
    .dl-btn{{display:none}}.hero{{box-shadow:none}}
    .card,.trend-card,.sem,.flag,.md-course{{box-shadow:none;break-inside:avoid}}
    .chart .line{{stroke-dashoffset:0!important}}.chart .dot,.chart .dv,.chart .chg,.area{{opacity:1!important}}
  }}
  @media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}
    .chart .line{{stroke-dashoffset:0}}.chart .dot,.chart .dv,.chart .chg,.area{{opacity:1}}.rise{{opacity:1;transform:none}}}}
</style></head>
<body>
  <nav class="nav"><div class="nav-in">
    <div class="nav-brand"><div class="nav-mark"><img src="/static/markhor2.png" alt="Markhor" width="34" height="34"></div><span class="nav-title">Academic Report</span></div>
    <div class="nav-links">
      <a href="#priorities">Priorities</a>
      <a href="#trend">GPA Trend</a>
      <a href="#progress">Progress</a>
      <a href="#attendance">Attendance</a>
      <a href="#semesters">Grades</a>
      <a href="#next">Next Steps</a>
    </div>
  </div></nav>
  <div class="wrap">

  <div class="hero rise d1">
    <img src="/static/markhor2.png" alt="" class="hero-markhor" aria-hidden="true">
    <div class="hero-inner">
      <div class="ring-wrap">
        <svg width="120" height="120" viewBox="0 0 120 120" style="transform:rotate(-90deg)">
          <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="9"/>
          <circle id="ring" cx="60" cy="60" r="52" fill="none" stroke="url(#gRing)" stroke-width="9"
            stroke-linecap="round" stroke-dasharray="327" stroke-dashoffset="327"/>
          <defs><linearGradient id="gRing" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#e8b84b"/><stop offset="1" stop-color="#c69534"/></linearGradient></defs>
        </svg>
        <div class="ring-num"><div><b class="num" id="scoreNum">0</b><i>/ 100</i></div></div>
      </div>
      <div>
        <div class="hero-name">{_esc(st["name"])}</div>
        <div class="hero-sub">{_esc(st["program"])} &middot; Semester {_esc(st["current_semester"])}</div>
        <div class="band-lg">{_esc(band)}<small>Academic Health Score</small></div>
        <div class="bd">{_breakdown_rows(hs["breakdown"])}</div>
      </div>
    </div>
  </div>

  <div class="lbl rise d2" id="priorities"><span class="dot"></span><b>Priorities</b><span class="rule"></span></div>
  <div class="flags">{_flag_cards(intelligence["flags"])}</div>

  <div class="lbl rise d3" id="trend"><span class="dot"></span><b>GPA Trend</b><span class="rule"></span></div>
  <div class="trend-card glow rise d3">
    {trend_inner}
    <div class="trend-wm">BUITEMS</div>
  </div>
  <button class="dl-btn rise d3" onclick="window.print()">&#8681; Download report (PDF)</button>

  <div class="grid g2" style="margin-top:14px">
    <div class="card cgpa-card glow rise d4"><h3>Overall CGPA</h3><div class="stat num">{_esc(cg_txt)}</div><span class="pill gold">{standing} standing</span></div>
    <div class="card glow rise d4"><h3>Fees</h3><div class="stat sm num">{_esc(fee_due)}</div><div class="stat-sub">{fee_total}</div><span class="pill {fee_pill[0]}">{fee_pill[1]}</span></div>
  </div>

  {_degree_progress(report["credits"])}

  <div class="grid g2" style="margin-top:14px">
    <div class="card strengths rise d5"><h3>Strengths</h3><div class="sw">{_sw_items(intelligence["strengths"], "up")}</div></div>
    <div class="card needsfocus rise d5"><h3>Needs Focus</h3><div class="sw">{_sw_items(intelligence["weaknesses"], "dn")}</div></div>
  </div>

  <div class="lbl rise d5" id="attendance"><span class="dot"></span><b>Attendance</b><span class="rule"></span></div>
  <div class="card rise d5">
    <table class="tbl"><thead><tr><th>Course</th><th class="c">Classes</th><th class="r">Rate</th></tr></thead>
      <tbody>{_attendance_rows(report["attendance"])}</tbody></table>
    {_recovery_note(intelligence["attendance_recovery"])}
  </div>

  <div class="lbl rise d6" id="semesters"><span class="dot"></span><b>Grades &amp; Marks Detail</b><span class="rule"></span></div>
  <p class="muted" style="font-size:12px;margin:0 2px 14px">Each semester with its courses. Tap any course to see how the grade was composed (Mid-Term 25 &middot; Final 50 &middot; Sessional 25).</p>
  <div class="rise d6">{_combined_semesters(report)}</div>

  <div class="lbl rise d7" id="next"><span class="dot"></span><b>What to do next</b><span class="rule"></span></div>
  <div class="card rise d7"><ul class="tips">{_suggestion_items(intelligence["suggestions"])}</ul></div>

  {_islamic_reminder()}

  <div class="brandfoot rise">
    <img src="/static/zira-logo.png" alt="ZIRA Technologies" class="bf-logo">
    <div class="bf-line"></div>
    <div class="bf-txt"><b>Developed by Arsalan Nasar</b><small>ZIRA Technologies &middot; AI Solutions</small></div>
  </div>

  <div class="foot"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>Generated on your device &middot; No data leaves the university network</div>

</div>
<script>
  var score={score_js}, scorePending={"true" if is_pending else "false"};
  var ring=document.getElementById('ring');
  var C=327, off=C-C*(score/100);
  requestAnimationFrame(function(){{ring.style.transition='stroke-dashoffset 1.5s cubic-bezier(.22,1,.36,1) .3s';ring.style.strokeDashoffset=off;}});
  var numEl=document.getElementById('scoreNum'),s=0;
  if(scorePending){{numEl.textContent='–';}}else{{
    function step(){{s+=2;if(s>=score){{numEl.textContent=score;}}else{{numEl.textContent=s;requestAnimationFrame(step);}}}}
    setTimeout(function(){{requestAnimationFrame(step);}},400);
  }}
  var fills=document.querySelectorAll('.bd-fill,.dp-fill');
  for(var i=0;i<fills.length;i++){{(function(f){{requestAnimationFrame(function(){{f.style.width=getComputedStyle(f).getPropertyValue('--w');}});}})(fills[i]);}}

  var pts={trend_json};
  var SVGNS='http://www.w3.org/2000/svg';
  function mk(tag,attrs,cls){{var e=document.createElementNS(SVGNS,tag);for(var k in attrs)e.setAttribute(k,attrs[k]);if(cls)e.setAttribute('class',cls);return e;}}
  if(pts.length){{
    var X0=64,X1=600,TOP=34,BOT=196;
    var Y=function(g){{return TOP+(4.0-g)/(4.0-2.0)*(BOT-TOP);}};
    var xs=pts.map(function(p,i){{return X0+(X1-X0)*(pts.length>1?i/(pts.length-1):0.5);}});
    // gridlines 2.0-4.0
    var grid=document.getElementById('grid');
    [2.0,2.5,3.0,3.5,4.0].forEach(function(g){{
      var y=Y(g);
      grid.appendChild(mk('line',{{x1:X0,y1:y,x2:X1,y2:y}},'grid-l'));
      grid.appendChild(mk('text',{{x:X0-10,y:y+4,'text-anchor':'end'}},'ax')).textContent=g.toFixed(1);
    }});
    document.getElementById('line').setAttribute('points',xs.map(function(x,i){{return x+','+Y(pts[i].g);}}).join(' '));
    var area='M'+xs[0]+','+Y(pts[0].g)+' '+xs.map(function(x,i){{return 'L'+x+','+Y(pts[i].g);}}).join(' ')+' L'+xs[xs.length-1]+','+BOT+' L'+xs[0]+','+BOT+' Z';
    var areaEl=document.getElementById('area');areaEl.setAttribute('d',area);
    setTimeout(function(){{areaEl.style.transition='opacity 1s ease';areaEl.style.opacity=1;}},1400);
    var dots=document.getElementById('dots'),xl=document.getElementById('xlabels'),chg=document.getElementById('changes');
    var gmax=Math.max.apply(null,pts.map(function(p){{return p.g;}}));
    var gmin=Math.min.apply(null,pts.map(function(p){{return p.g;}}));
    pts.forEach(function(p,i){{
      var cx=xs[i],cy=Y(p.g);
      var isPeak=(p.g===gmax),isLow=(p.g===gmin);
      var c=mk('circle',{{cx:cx,cy:cy,r:isPeak||isLow?6.5:5}},'dot');
      if(isPeak)c.style.stroke='#1f9d6b';if(isLow)c.style.stroke='#d0553f';
      c.style.animationDelay=(1.1+i*.14)+'s';dots.appendChild(c);
      var t=mk('text',{{x:cx,y:cy-14,'text-anchor':'middle'}},'dv');
      t.textContent=Number(p.g).toFixed(2);t.style.animationDelay=(1.2+i*.14)+'s';dots.appendChild(t);
      // x label
      var xt=mk('text',{{x:cx,y:BOT+22,'text-anchor':'middle'}},'ax');
      xt.textContent='Sem '+p.s;xl.appendChild(xt);
      // % change label between points
      if(p.c!==null&&p.c!==undefined&&i>0){{
        var midx=(xs[i-1]+xs[i])/2, midy=(Y(pts[i-1].g)+Y(p.g))/2 - 10;
        var up=p.c>=0;
        var ct=mk('text',{{x:midx,y:midy,'text-anchor':'middle'}},'chg '+(up?'up':'down'));
        ct.textContent=(up?'▲ +':'▼ ')+p.c+'%';
        ct.style.opacity=0;ct.style.animation='pop .4s ease '+(1.6+i*.12)+'s forwards';
        chg.appendChild(ct);
      }}
    }});
  }}
</script>
</body></html>'''
