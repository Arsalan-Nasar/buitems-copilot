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


def _semester_cards(semesters):
    # newest first, and only show semesters that have courses
    out = []
    for s in sorted(semesters, key=lambda x: int(x["semester"]) if str(x["semester"]).isdigit() else 0,
                    reverse=True):
        if not s["courses"]:
            continue
        rows = ""
        for c in s["courses"]:
            grade = c["grade"]
            if grade is None:
                chip = f'<span class="chip" style="background:var(--line);color:var(--muted)">{EM_DASH}</span>'
            else:
                chip = f'<span class="chip">{_esc(grade)}</span>'
            rows += f'<tr><td>{_esc(c["title"])}</td><td class="r">{chip}</td></tr>'
        if s["status"] == "complete" and s["gpa"] is not None:
            gpa_badge = f'<span class="sem-gpa done num">GPA {_esc(s["gpa"])}</span>'
        else:
            gpa_badge = '<span class="sem-gpa prog">In progress</span>'
        term = f' <small>&middot; {_esc(s["term"])}</small>' if s["term"] else ""
        out.append(
            f'<div class="sem"><div class="sem-h">'
            f'<span class="t">Semester {_esc(s["semester"])}{term}</span>{gpa_badge}</div>'
            f'<table class="tbl"><tbody>{rows}</tbody></table></div>'
        )
    return "".join(out)


def _suggestion_items(suggestions):
    out = []
    for i, s in enumerate(suggestions, 1):
        out.append(f'<li><span class="n">{i}</span><div>{_esc(s)}</div></li>')
    return "".join(out)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render_report(report, intelligence):
    st = report["student"]
    hs = intelligence["health_score"]
    cg = report["cgpa"]
    fe = report["fees"]
    trend = report["trend"]

    score = hs["score"]
    band = hs.get("band") or _band_from_score(score)

    # trend data -> JSON for the JS chart
    trend_points = [{"s": _esc(p["semester"]), "g": p["gpa"]} for p in trend["points"]]
    trend_json = _json.dumps(trend_points)
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

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Academic Report {EM_DASH} {_esc(st["name"])}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  :root{{
    --navy:#0a2540;--royal:#123a63;--blue:#1e5aa8;--blue-soft:#e7eef8;
    --gold:#c9962e;--gold-lt:#f5c451;--gold-soft:#faf3e0;
    --bg:#f7f9fc;--card:#fff;--ink:#0a2540;--muted:#6b7a90;
    --line:#e4eaf2;--green:#1f9d6b;--amber:#dd8a1a;--red:#d0553f;
    --shadow:0 1px 2px rgba(10,37,64,.04),0 8px 24px rgba(10,37,64,.06);
  }}
  body{{background:var(--bg);color:var(--ink);font-family:'Inter',system-ui,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased}}
  .num{{font-variant-numeric:tabular-nums}}
  .muted{{color:var(--muted)}}
  .wrap{{max-width:940px;margin:0 auto;padding:20px 18px 60px}}
  .brand{{display:flex;align-items:center;gap:12px;padding:14px 0 20px}}
  .brand-mark{{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,var(--royal),var(--navy));display:grid;place-items:center;box-shadow:var(--shadow);position:relative;overflow:hidden}}
  .brand-mark::after{{content:"";position:absolute;inset:0;background:radial-gradient(circle at 30% 20%,rgba(245,196,81,.5),transparent 60%)}}
  .brand-mark span{{color:var(--gold-lt);font-family:'Sora';font-weight:800;font-size:19px;z-index:1}}
  .brand-txt b{{font-family:'Sora';font-weight:700;font-size:15px;letter-spacing:-.01em;display:block;line-height:1.15}}
  .brand-txt small{{color:var(--muted);font-size:12px}}
  .hero{{background:linear-gradient(135deg,var(--navy),var(--royal));border-radius:22px;padding:30px;color:#fff;position:relative;overflow:hidden;box-shadow:0 12px 40px rgba(10,37,64,.22)}}
  .hero::before{{content:"";position:absolute;top:-40%;right:-10%;width:340px;height:340px;background:radial-gradient(circle,rgba(201,150,46,.22),transparent 65%)}}
  .hero::after{{content:"";position:absolute;bottom:-60%;left:-15%;width:380px;height:380px;background:radial-gradient(circle,rgba(30,90,168,.35),transparent 65%)}}
  .hero-inner{{position:relative;z-index:1;display:grid;grid-template-columns:auto 1fr;gap:32px;align-items:center}}
  .hero-name{{font-family:'Sora';font-weight:600;font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold-lt);margin-bottom:4px}}
  .hero-sub{{font-size:13px;color:rgba(255,255,255,.72);margin-bottom:22px}}
  .band-lg{{font-family:'Sora';font-weight:800;font-size:34px;letter-spacing:-.02em;line-height:1;margin-bottom:16px}}
  .band-lg small{{display:block;font-size:12px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:rgba(255,255,255,.6);margin-top:8px;font-family:'Inter'}}
  .ring-wrap{{width:172px;height:172px;position:relative}}
  .ring-num{{position:absolute;inset:0;display:grid;place-items:center;text-align:center}}
  .ring-num b{{font-family:'Sora';font-weight:800;font-size:52px;line-height:1;letter-spacing:-.03em;color:#fff}}
  .ring-num i{{font-style:normal;font-size:12px;color:rgba(255,255,255,.6);letter-spacing:.1em;margin-top:2px;display:block}}
  .bd{{display:flex;flex-direction:column;gap:11px;margin-top:4px}}
  .bd-row{{display:grid;grid-template-columns:96px 1fr auto;gap:12px;align-items:center;font-size:12.5px}}
  .bd-row .lb{{color:rgba(255,255,255,.78)}}
  .bd-track{{height:7px;background:rgba(255,255,255,.14);border-radius:20px;overflow:hidden}}
  .bd-fill{{height:100%;border-radius:20px;background:linear-gradient(90deg,var(--gold),var(--gold-lt));width:0;transition:width 1.2s cubic-bezier(.22,1,.36,1) .3s}}
  .bd-val{{color:#fff;font-weight:600;font-variant-numeric:tabular-nums;font-size:12px}}
  .lbl{{display:flex;align-items:center;gap:9px;margin:30px 4px 13px}}
  .lbl b{{font-family:'Sora';font-weight:600;font-size:12px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}}
  .lbl .dot{{width:6px;height:6px;border-radius:50%;background:var(--gold)}}
  .lbl .rule{{flex:1;height:1px;background:var(--line)}}
  .flags{{display:flex;flex-direction:column;gap:10px}}
  .flag{{display:flex;gap:14px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-left-width:4px;border-radius:14px;padding:15px 17px;box-shadow:var(--shadow)}}
  .flag.red{{border-left-color:var(--red)}}.flag.amber{{border-left-color:var(--amber)}}.flag.green{{border-left-color:var(--green)}}
  .flag-ico{{width:26px;height:26px;border-radius:8px;flex-shrink:0;display:grid;place-items:center;font-weight:700;font-size:14px;color:#fff;font-family:'Sora'}}
  .flag.red .flag-ico{{background:var(--red)}}.flag.amber .flag-ico{{background:var(--amber)}}.flag.green .flag-ico{{background:var(--green)}}
  .flag-tx{{font-size:13.5px;padding-top:3px;color:#2c3d52}}
  .flag-tx b{{color:var(--ink)}}
  .grid{{display:grid;gap:14px}}.g2{{grid-template-columns:1fr 1fr}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:var(--shadow)}}
  .card h3{{font-family:'Sora';font-weight:600;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:12px}}
  .stat{{font-family:'Sora';font-weight:800;font-size:34px;letter-spacing:-.02em;line-height:1}}
  .stat.sm{{font-size:26px}}
  .stat-sub{{font-size:12.5px;color:var(--muted);margin-top:6px}}
  .pill{{display:inline-block;font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;margin-top:10px;text-transform:capitalize}}
  .pill.good{{background:var(--blue-soft);color:var(--blue)}}.pill.warn{{background:var(--gold-soft);color:#a5761a}}
  .trend-card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 20px 14px;box-shadow:var(--shadow)}}
  .trend-head{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}}
  .trend-head h3{{font-family:'Sora';font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}}
  .trend-head .dir{{font-size:12.5px;font-weight:600}}
  svg.chart{{width:100%;height:auto;display:block;overflow:visible}}
  .chart .grid-l{{stroke:var(--line);stroke-width:1}}
  .chart .ax{{fill:var(--muted);font-size:11px;font-family:'Inter'}}
  .chart .area{{fill:url(#gGold);opacity:0}}
  .chart .line{{fill:none;stroke:url(#gLine);stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1000;stroke-dashoffset:1000;animation:draw 1.6s cubic-bezier(.4,0,.2,1) .5s forwards}}
  @keyframes draw{{to{{stroke-dashoffset:0}}}}
  .chart .dot{{fill:#fff;stroke:var(--royal);stroke-width:3;opacity:0;animation:pop .4s ease forwards}}
  .chart .dv{{fill:var(--navy);font-family:'Sora';font-weight:700;font-size:13px;text-anchor:middle;opacity:0;animation:pop .4s ease forwards}}
  @keyframes pop{{to{{opacity:1}}}}
  .sw{{display:flex;flex-direction:column;gap:9px}}
  .sw-item{{display:flex;align-items:center;gap:11px}}
  .sw-badge{{font-family:'Sora';font-weight:700;font-size:11px;min-width:38px;height:26px;padding:0 8px;border-radius:8px;display:grid;place-items:center}}
  .sw-badge.up{{background:var(--blue-soft);color:var(--blue)}}.sw-badge.dn{{background:var(--gold-soft);color:#a5761a}}
  .sw-item span{{font-size:13.5px;color:#2c3d52}}
  .tbl{{width:100%;border-collapse:collapse;font-size:13px}}
  .tbl th{{text-align:left;font-family:'Sora';font-weight:600;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);padding:0 8px 10px}}
  .tbl th.r,.tbl td.r{{text-align:right}}.tbl th.c,.tbl td.c{{text-align:center}}
  .tbl td{{padding:11px 8px;border-top:1px solid var(--line);color:#2c3d52}}
  .tbl tr:first-child td{{border-top:none}}
  .att-bar{{display:inline-flex;align-items:center;gap:8px}}
  .att-track{{width:54px;height:6px;background:var(--line);border-radius:20px;overflow:hidden}}
  .att-f{{height:100%;border-radius:20px}}
  .att-pct{{font-weight:700;font-variant-numeric:tabular-nums;font-size:12.5px;min-width:34px;text-align:right}}
  .chip{{font-family:'Sora';font-weight:700;font-size:11px;padding:3px 9px;border-radius:7px;background:var(--blue-soft);color:var(--royal)}}
  .rec{{margin-top:14px;font-size:12.5px;color:#8a5a12;background:var(--gold-soft);border-radius:10px;padding:11px 14px;display:flex;gap:9px;align-items:flex-start}}
  .rec b{{color:#6e4708}}
  .sem{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;box-shadow:var(--shadow);margin-bottom:12px}}
  .sem-h{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
  .sem-h .t{{font-family:'Sora';font-weight:600;font-size:14.5px}}
  .sem-h .t small{{color:var(--muted);font-weight:400;font-family:'Inter'}}
  .sem-gpa{{font-family:'Sora';font-weight:700;font-size:12px;padding:5px 11px;border-radius:8px}}
  .sem-gpa.done{{background:var(--navy);color:#fff}}.sem-gpa.prog{{background:var(--gold-soft);color:#a5761a}}
  .tips{{list-style:none;display:flex;flex-direction:column;gap:11px}}
  .tips li{{display:flex;gap:12px;font-size:13.5px;color:#2c3d52;align-items:flex-start}}
  .tips .n{{width:22px;height:22px;border-radius:7px;background:var(--blue-soft);color:var(--blue);font-family:'Sora';font-weight:700;font-size:11px;display:grid;place-items:center;flex-shrink:0;margin-top:1px}}
  .foot{{text-align:center;margin-top:34px;padding-top:20px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);display:flex;align-items:center;justify-content:center;gap:8px}}
  .rise{{opacity:0;transform:translateY(16px);animation:rise .7s cubic-bezier(.22,1,.36,1) forwards}}
  @keyframes rise{{to{{opacity:1;transform:none}}}}
  .d1{{animation-delay:.05s}}.d2{{animation-delay:.12s}}.d3{{animation-delay:.19s}}.d4{{animation-delay:.26s}}.d5{{animation-delay:.33s}}.d6{{animation-delay:.4s}}.d7{{animation-delay:.47s}}
  @media (max-width:720px){{
    .hero{{padding:24px 20px;border-radius:20px}}
    .hero-inner{{grid-template-columns:1fr;gap:24px;text-align:center}}
    .ring-wrap{{margin:0 auto}}.bd-row{{grid-template-columns:80px 1fr auto}}.g2{{grid-template-columns:1fr}}
  }}
  @media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}
    .chart .line{{stroke-dashoffset:0}}.chart .dot,.chart .dv,.area{{opacity:1}}.rise{{opacity:1;transform:none}}}}
</style></head>
<body><div class="wrap">

  <div class="brand rise">
    <div class="brand-mark"><span>B</span></div>
    <div class="brand-txt"><b>Academic Report</b><small>BUITEMS Student Portal</small></div>
  </div>

  <div class="hero rise d1">
    <div class="hero-inner">
      <div class="ring-wrap">
        <svg width="172" height="172" viewBox="0 0 172 172" style="transform:rotate(-90deg)">
          <circle cx="86" cy="86" r="74" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="13"/>
          <circle id="ring" cx="86" cy="86" r="74" fill="none" stroke="url(#gRing)" stroke-width="13"
            stroke-linecap="round" stroke-dasharray="465" stroke-dashoffset="465"/>
          <defs><linearGradient id="gRing" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#f5c451"/><stop offset="1" stop-color="#c9962e"/></linearGradient></defs>
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

  <div class="lbl rise d2"><span class="dot"></span><b>Priorities</b><span class="rule"></span></div>
  <div class="flags">{_flag_cards(intelligence["flags"])}</div>

  <div class="lbl rise d3"><span class="dot"></span><b>GPA Trend</b><span class="rule"></span></div>
  <div class="trend-card rise d3">
    <div class="trend-head"><h3>Completed semesters</h3><span class="dir" style="color:{dir_color}">{dir_arrow} {_esc(dir_txt)}</span></div>
    <svg class="chart" viewBox="0 0 600 210">
      <defs>
        <linearGradient id="gLine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1e5aa8"/><stop offset="1" stop-color="#123a63"/></linearGradient>
        <linearGradient id="gGold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="rgba(30,90,168,.16)"/><stop offset="1" stop-color="rgba(30,90,168,0)"/></linearGradient>
      </defs>
      <line class="grid-l" x1="44" y1="30" x2="588" y2="30"/><text class="ax" x="34" y="34" text-anchor="end">4.0</text>
      <line class="grid-l" x1="44" y1="90" x2="588" y2="90"/><text class="ax" x="34" y="94" text-anchor="end">3.0</text>
      <line class="grid-l" x1="44" y1="150" x2="588" y2="150"/><text class="ax" x="34" y="154" text-anchor="end">2.0</text>
      <path class="area" id="area"/><polyline class="line" id="line" points=""/>
      <g id="dots"></g><g id="xlabels"></g>
    </svg>
  </div>

  <div class="grid g2" style="margin-top:14px">
    <div class="card rise d4"><h3>Overall CGPA</h3><div class="stat num">{_esc(cg_txt)}</div><span class="pill good">{standing} standing</span></div>
    <div class="card rise d4"><h3>Fees</h3><div class="stat sm num">{_esc(fee_due)}</div><div class="stat-sub">{fee_total}</div><span class="pill {fee_pill[0]}">{fee_pill[1]}</span></div>
  </div>

  <div class="grid g2" style="margin-top:14px">
    <div class="card rise d5"><h3>Strengths</h3><div class="sw">{_sw_items(intelligence["strengths"], "up")}</div></div>
    <div class="card rise d5"><h3>Needs Focus</h3><div class="sw">{_sw_items(intelligence["weaknesses"], "dn")}</div></div>
  </div>

  <div class="lbl rise d5"><span class="dot"></span><b>Attendance</b><span class="rule"></span></div>
  <div class="card rise d5">
    <table class="tbl"><thead><tr><th>Course</th><th class="c">Classes</th><th class="r">Rate</th></tr></thead>
      <tbody>{_attendance_rows(report["attendance"])}</tbody></table>
    {_recovery_note(intelligence["attendance_recovery"])}
  </div>

  <div class="lbl rise d6"><span class="dot"></span><b>Semester Breakdown</b><span class="rule"></span></div>
  <div class="rise d6">{_semester_cards(report["semesters"])}</div>

  <div class="lbl rise d7"><span class="dot"></span><b>What to do next</b><span class="rule"></span></div>
  <div class="card rise d7"><ul class="tips">{_suggestion_items(intelligence["suggestions"])}</ul></div>

  <div class="foot"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>Generated on your device &middot; No data leaves the university network</div>

</div>
<script>
  var score={score};
  var ring=document.getElementById('ring');
  var C=465, off=C-C*(score/100);
  requestAnimationFrame(function(){{ring.style.transition='stroke-dashoffset 1.5s cubic-bezier(.22,1,.36,1) .3s';ring.style.strokeDashoffset=off;}});
  var numEl=document.getElementById('scoreNum'),s=0;
  function step(){{s+=2;if(s>=score){{numEl.textContent=score;}}else{{numEl.textContent=s;requestAnimationFrame(step);}}}}
  setTimeout(function(){{requestAnimationFrame(step);}},400);
  var fills=document.querySelectorAll('.bd-fill');
  for(var i=0;i<fills.length;i++){{(function(f){{requestAnimationFrame(function(){{f.style.width=getComputedStyle(f).getPropertyValue('--w');}});}})(fills[i]);}}

  var pts={trend_json};
  if(pts.length){{
    var X0=70,X1=560;
    var Y=function(g){{return 30+(4.0-g)/(4.0-1.5)*150;}};
    var xs=pts.map(function(p,i){{return X0+(X1-X0)*(pts.length>1?i/(pts.length-1):0.5);}});
    document.getElementById('line').setAttribute('points',xs.map(function(x,i){{return x+','+Y(pts[i].g);}}).join(' '));
    var area='M'+xs[0]+','+Y(pts[0].g)+' '+xs.map(function(x,i){{return 'L'+x+','+Y(pts[i].g);}}).join(' ')+' L'+xs[xs.length-1]+',180 L'+xs[0]+',180 Z';
    var areaEl=document.getElementById('area');areaEl.setAttribute('d',area);
    setTimeout(function(){{areaEl.style.transition='opacity 1s ease';areaEl.style.opacity=1;}},1400);
    var dots=document.getElementById('dots'),xl=document.getElementById('xlabels');
    pts.forEach(function(p,i){{
      var cx=xs[i],cy=Y(p.g);
      var c=document.createElementNS('http://www.w3.org/2000/svg','circle');
      c.setAttribute('class','dot');c.setAttribute('cx',cx);c.setAttribute('cy',cy);c.setAttribute('r',5.5);
      c.style.animationDelay=(1.1+i*.18)+'s';dots.appendChild(c);
      var t=document.createElementNS('http://www.w3.org/2000/svg','text');
      t.setAttribute('class','dv');t.setAttribute('x',cx);t.setAttribute('y',cy-14);t.textContent=Number(p.g).toFixed(2);
      t.style.animationDelay=(1.2+i*.18)+'s';dots.appendChild(t);
      var xt=document.createElementNS('http://www.w3.org/2000/svg','text');
      xt.setAttribute('class','ax');xt.setAttribute('x',cx);xt.setAttribute('y',200);xt.setAttribute('text-anchor','middle');xt.textContent='Sem '+p.s;xl.appendChild(xt);
    }});
  }}
</script>
</body></html>'''
