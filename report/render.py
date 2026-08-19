# report/render.py — THE REPORT UI (turns report data into a premium HTML page).
#
# PLAIN ENGLISH:
# Takes the structured report (Phase R1) + intelligence (Phase R2) and produces
# one self-contained, beautiful HTML report. No external calls, no LLM. All data
# is HTML-escaped before rendering (XSS-safe, carried over from the chat version).
#
# Design: deep academic navy + warm gold, serif display numbers, and a circular
# Academic Health Score gauge as the signature element. Green/amber/red for
# health states. Fully self-contained (inline CSS + one inline SVG gauge).

import html as _html


def _esc(v):
    return _html.escape(str(v), quote=True)


def _gauge_svg(score):
    """A circular progress gauge for the health score (the signature element)."""
    # ring geometry
    r = 84
    circ = 2 * 3.14159 * r
    frac = max(0, min(score / 100.0, 1.0))
    filled = circ * frac
    gap = circ - filled
    # color by band
    if score >= 85:
        color = "#2f9e6b"      # green
    elif score >= 70:
        color = "#c9a227"      # gold
    elif score >= 55:
        color = "#d98a2b"      # amber
    else:
        color = "#c2543f"      # red
    return f'''
    <svg viewBox="0 0 200 200" class="gauge" role="img" aria-label="Academic Health Score {score} out of 100">
      <circle cx="100" cy="100" r="{r}" fill="none" stroke="#e7e3d8" stroke-width="16"/>
      <circle cx="100" cy="100" r="{r}" fill="none" stroke="{color}" stroke-width="16"
              stroke-linecap="round" stroke-dasharray="{filled:.1f} {gap:.1f}"
              transform="rotate(-90 100 100)"/>
      <text x="100" y="96" text-anchor="middle" class="gauge-num">{score}</text>
      <text x="100" y="122" text-anchor="middle" class="gauge-den">/ 100</text>
    </svg>'''


def _trend_chart_svg(points):
    """Inline SVG line chart of GPA per semester — the beloved trend chart."""
    if not points:
        return '<p class="muted">Not enough completed semesters yet to chart a trend.</p>'
    W, H = 620, 240
    pad_l, pad_b, pad_t, pad_r = 46, 40, 24, 20
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_b - pad_t
    n = len(points)
    max_gpa, min_gpa = 4.0, 0.0
    def x(i):
        return pad_l + (plot_w * (i / (n - 1)) if n > 1 else plot_w / 2)
    def y(g):
        return pad_t + plot_h * (1 - (g - min_gpa) / (max_gpa - min_gpa))
    # gridlines at 1,2,3,4
    grid = ""
    for g in (1, 2, 3, 4):
        gy = y(g)
        grid += f'<line x1="{pad_l}" y1="{gy:.0f}" x2="{W-pad_r}" y2="{gy:.0f}" stroke="#eee7d6" stroke-width="1"/>'
        grid += f'<text x="{pad_l-10}" y="{gy+4:.0f}" text-anchor="end" class="ax">{g}.0</text>'
    # line + points
    pts_attr = " ".join(f"{x(i):.0f},{y(p['gpa']):.0f}" for i, p in enumerate(points))
    dots = ""
    labels = ""
    for i, p in enumerate(points):
        px, py = x(i), y(p["gpa"])
        dots += f'<circle cx="{px:.0f}" cy="{py:.0f}" r="5" fill="#1c2b4a" stroke="#c9a227" stroke-width="2"/>'
        dots += f'<text x="{px:.0f}" y="{py-12:.0f}" text-anchor="middle" class="pt">{p["gpa"]}</text>'
        labels += f'<text x="{px:.0f}" y="{H-14:.0f}" text-anchor="middle" class="ax">Sem {_esc(p["semester"])}</text>'
    return f'''
    <svg viewBox="0 0 {W} {H}" class="trend" role="img" aria-label="GPA trend chart">
      {grid}
      <polyline points="{pts_attr}" fill="none" stroke="#1c2b4a" stroke-width="3"
                stroke-linejoin="round" stroke-linecap="round"/>
      {dots}
      {labels}
    </svg>'''


def _flag_cards(flags):
    color = {"red": "flag-red", "amber": "flag-amber", "green": "flag-green"}
    icon = {"red": "!", "amber": "!", "green": "\u2713"}
    out = []
    for f in flags:
        cls = color.get(f["level"], "flag-green")
        out.append(f'''
        <div class="flag {cls}">
          <span class="flag-dot">{icon.get(f["level"], "")}</span>
          <span class="flag-msg">{_esc(f["message"])}</span>
        </div>''')
    return "".join(out)


def _sw_list(items, kind):
    if not items:
        return '<li class="muted">None identified yet.</li>'
    out = []
    for c in items:
        out.append(f'<li><span class="sw-grade sw-{kind}">{_esc(c["grade"])}</span>'
                   f'<span class="sw-title">{_esc(c["title"])}</span></li>')
    return "".join(out)


def _semester_tables(semesters):
    out = []
    for s in semesters:
        rows = ""
        for c in s["courses"]:
            total = c["total"] if c["total"] is not None else "\u2014"
            grade = c["grade"] if c["grade"] is not None else "\u2014"
            rows += (f'<tr><td class="l">{_esc(c["title"])}</td>'
                     f'<td>{_esc(c["mid"]) if c["mid"] is not None else "\u2014"}</td>'
                     f'<td>{_esc(c["final"]) if c["final"] is not None else "\u2014"}</td>'
                     f'<td>{_esc(c["sessional"]) if c["sessional"] is not None else "\u2014"}</td>'
                     f'<td>{_esc(total)}</td>'
                     f'<td><span class="grade-chip">{_esc(grade)}</span></td></tr>')
        gpa_txt = s["gpa"] if s["gpa"] is not None else "In progress"
        status_cls = "sem-done" if s["status"] == "complete" else "sem-prog"
        out.append(f'''
        <div class="sem-card">
          <div class="sem-head">
            <span class="sem-name">Semester {_esc(s["semester"])} <span class="muted">· {_esc(s["term"])}</span></span>
            <span class="sem-gpa {status_cls}">GPA {_esc(gpa_txt)}</span>
          </div>
          <table class="tbl">
            <thead><tr><th class="l">Course</th><th>Mid</th><th>Final</th><th>Sess</th><th>Total</th><th>Grade</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>''')
    return "".join(out)


def render_report(report, intelligence):
    """Return a complete, self-contained HTML string for the report."""
    st = report["student"]
    hs = intelligence["health_score"]
    cg = report["cgpa"]

    # health breakdown bars
    bd = ""
    for b in hs["breakdown"]:
        pct = round(b["points"] / b["max"] * 100) if b["max"] else 0
        bd += (f'<div class="bd-row"><span class="bd-label">{_esc(b["factor"])}</span>'
               f'<span class="bd-track"><span class="bd-fill" style="width:{pct}%"></span></span>'
               f'<span class="bd-val">{_esc(b["points"])}/{_esc(b["max"])}</span></div>')

    # fees
    fe = report["fees"]
    fee_pct = round(fe["paid"] / fe["total"] * 100) if fe["total"] else 100

    # attendance rows
    att_rows = ""
    for c in report["attendance"]["courses"]:
        pct = c["percent"]
        cls = "att-ok" if (pct is not None and pct >= report["attendance"]["threshold"]) else "att-low"
        att_rows += (f'<tr><td class="l">{_esc(c["title"])}</td>'
                     f'<td>{_esc(c["present"])}/{_esc(c["total"])}</td>'
                     f'<td class="{cls}">{_esc(pct) if pct is not None else "\u2014"}%</td></tr>')

    # recovery notes
    rec = ""
    for a in intelligence["attendance_recovery"]:
        if a["classes_to_attend"]:
            rec += (f'<p class="rec">To reach 75% in <b>{_esc(a["title"])}</b>, attend the '
                    f'next <b>{_esc(a["classes_to_attend"])}</b> classes.</p>')

    # suggestions
    sug = "".join(f'<li>{_esc(s)}</li>' for s in intelligence["suggestions"])

    trend = report["trend"]
    trend_dir = {"up": "trending upward", "down": "trending downward", "flat": "steady"}.get(
        trend["direction"], "")

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Academic Report — {_esc(st["name"])}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background:#f3f1ea; color:#1c2b4a; font-family:'Inter',system-ui,sans-serif;
         line-height:1.5; padding:24px; }}
  .wrap {{ max-width:920px; margin:0 auto; }}
  .muted {{ color:#8a8778; font-weight:400; }}

  /* header */
  .rep-head {{ display:flex; justify-content:space-between; align-items:flex-end;
              border-bottom:2px solid #1c2b4a; padding-bottom:16px; margin-bottom:24px; }}
  .rep-head h1 {{ font-family:'Fraunces',serif; font-size:26px; font-weight:600; }}
  .rep-head .prog {{ color:#5a5848; font-size:14px; margin-top:2px; }}
  .rep-head .meta {{ text-align:right; font-size:12px; color:#8a8778; }}

  /* hero: score + breakdown */
  .hero {{ display:grid; grid-template-columns:220px 1fr; gap:28px; align-items:center;
          background:#fff; border:1px solid #e7e3d8; border-radius:16px; padding:28px;
          margin-bottom:20px; }}
  .gauge {{ width:200px; height:200px; }}
  .gauge-num {{ font-family:'Fraunces',serif; font-size:52px; font-weight:700; fill:#1c2b4a; }}
  .gauge-den {{ font-size:15px; fill:#8a8778; font-family:'Inter'; }}
  .hero-right h2 {{ font-family:'Fraunces',serif; font-size:15px; text-transform:uppercase;
                   letter-spacing:.08em; color:#8a8778; font-weight:600; margin-bottom:4px; }}
  .band {{ font-family:'Fraunces',serif; font-size:30px; font-weight:600; margin-bottom:16px; }}
  .bd-row {{ display:flex; align-items:center; gap:12px; margin:8px 0; font-size:13px; }}
  .bd-label {{ width:130px; color:#5a5848; }}
  .bd-track {{ flex:1; height:8px; background:#eee7d6; border-radius:4px; overflow:hidden; }}
  .bd-fill {{ display:block; height:100%; background:#c9a227; border-radius:4px; }}
  .bd-val {{ width:52px; text-align:right; font-variant-numeric:tabular-nums; color:#5a5848; }}

  /* section titles */
  .sec {{ margin:26px 0 12px; font-family:'Fraunces',serif; font-size:13px;
         text-transform:uppercase; letter-spacing:.1em; color:#8a8778; font-weight:600; }}

  /* flag cards */
  .flags {{ display:grid; gap:10px; }}
  .flag {{ display:flex; align-items:center; gap:12px; padding:14px 16px; border-radius:12px;
          font-size:14px; border:1px solid; }}
  .flag-dot {{ width:22px; height:22px; border-radius:50%; display:grid; place-items:center;
              color:#fff; font-weight:700; font-size:13px; flex-shrink:0; }}
  .flag-red {{ background:#fbecea; border-color:#e6c3bc; }}
  .flag-red .flag-dot {{ background:#c2543f; }}
  .flag-amber {{ background:#fdf4e3; border-color:#ecd9ae; }}
  .flag-amber .flag-dot {{ background:#d98a2b; }}
  .flag-green {{ background:#e9f4ee; border-color:#bfe0cd; }}
  .flag-green .flag-dot {{ background:#2f9e6b; }}

  /* two-column grid */
  .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  .card {{ background:#fff; border:1px solid #e7e3d8; border-radius:14px; padding:20px; }}
  .card h3 {{ font-family:'Fraunces',serif; font-size:16px; font-weight:600; margin-bottom:4px; }}
  .big-stat {{ font-family:'Fraunces',serif; font-size:40px; font-weight:700; }}

  /* trend chart */
  .trend {{ width:100%; height:auto; }}
  .ax {{ font-size:11px; fill:#8a8778; font-family:'Inter'; }}
  .pt {{ font-size:12px; fill:#1c2b4a; font-weight:600; font-family:'Inter'; }}

  /* strengths/weaknesses */
  ul.sw {{ list-style:none; }}
  ul.sw li {{ display:flex; align-items:center; gap:10px; padding:6px 0; font-size:14px; }}
  .sw-grade {{ font-weight:700; font-size:12px; padding:2px 8px; border-radius:6px; min-width:34px; text-align:center; }}
  .sw-strong {{ background:#e9f4ee; color:#2f9e6b; }}
  .sw-weak {{ background:#fdf4e3; color:#b5761d; }}

  /* tables */
  .sem-card {{ background:#fff; border:1px solid #e7e3d8; border-radius:14px; padding:18px; margin-bottom:14px; }}
  .sem-head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }}
  .sem-name {{ font-family:'Fraunces',serif; font-size:16px; font-weight:600; }}
  .sem-gpa {{ font-size:13px; font-weight:600; padding:4px 10px; border-radius:8px; }}
  .sem-done {{ background:#eef2f8; color:#1c2b4a; }}
  .sem-prog {{ background:#fdf4e3; color:#b5761d; }}
  table.tbl {{ width:100%; border-collapse:collapse; font-size:13px; }}
  table.tbl th {{ text-align:center; font-weight:600; color:#8a8778; font-size:11px;
                 text-transform:uppercase; letter-spacing:.04em; padding:6px 4px; border-bottom:1px solid #eee7d6; }}
  table.tbl td {{ text-align:center; padding:8px 4px; border-bottom:1px solid #f2eee2; }}
  table.tbl td.l, table.tbl th.l {{ text-align:left; }}
  .grade-chip {{ background:#eef2f8; color:#1c2b4a; font-weight:600; padding:2px 8px; border-radius:6px; font-size:12px; }}
  .att-ok {{ color:#2f9e6b; font-weight:600; }}
  .att-low {{ color:#c2543f; font-weight:700; }}
  .rec {{ font-size:13px; color:#5a5848; margin-top:8px; padding:8px 12px; background:#fbecea; border-radius:8px; }}
  ul.tips {{ padding-left:18px; font-size:14px; }}
  ul.tips li {{ margin:6px 0; }}
  .foot {{ text-align:center; color:#a8a596; font-size:12px; margin-top:28px;
          border-top:1px solid #e7e3d8; padding-top:16px; }}

  @media (max-width:680px) {{
    .hero {{ grid-template-columns:1fr; text-align:center; }}
    .gauge {{ margin:0 auto; }}
    .bd-label {{ width:100px; }}
    .grid2 {{ grid-template-columns:1fr; }}
  }}
</style></head>
<body><div class="wrap">

  <div class="rep-head">
    <div>
      <h1>{_esc(st["name"])}</h1>
      <div class="prog">{_esc(st["program"])} · Semester {_esc(st["current_semester"])}</div>
    </div>
    <div class="meta">Academic Report<br>Generated automatically</div>
  </div>

  <div class="hero">
    <div>{_gauge_svg(hs["score"])}</div>
    <div class="hero-right">
      <h2>Academic Health Score</h2>
      <div class="band">{_esc(hs["band"])}</div>
      {bd}
    </div>
  </div>

  <div class="sec">Priorities</div>
  <div class="flags">{_flag_cards(intelligence["flags"])}</div>

  <div class="sec">GPA Trend</div>
  <div class="card">
    {_trend_chart_svg(trend["points"])}
    <p class="muted" style="text-align:center;margin-top:8px;font-size:13px">Your GPA is {_esc(trend_dir)}.</p>
  </div>

  <div class="grid2" style="margin-top:20px">
    <div class="card">
      <h3>Overall CGPA</h3>
      <div class="big-stat">{_esc(cg["cgpa"] if cg["cgpa"] is not None else "—")}</div>
      <p class="muted" style="text-transform:capitalize">{_esc(cg["standing"].replace("_"," "))}</p>
    </div>
    <div class="card">
      <h3>Fees</h3>
      <div class="big-stat">Rs {_esc(f"{fe['due']:,}")}</div>
      <p class="muted">{"All clear" if fe["status"]=="clear" else "still due of Rs " + f"{fe['total']:,}"}</p>
    </div>
  </div>

  <div class="grid2" style="margin-top:20px">
    <div class="card">
      <h3>Strengths</h3>
      <ul class="sw">{_sw_list(intelligence["strengths"], "strong")}</ul>
    </div>
    <div class="card">
      <h3>Needs Focus</h3>
      <ul class="sw">{_sw_list(intelligence["weaknesses"], "weak")}</ul>
    </div>
  </div>

  <div class="sec">Attendance</div>
  <div class="card">
    <table class="tbl">
      <thead><tr><th class="l">Course</th><th>Classes</th><th>%</th></tr></thead>
      <tbody>{att_rows}</tbody>
    </table>
    {rec}
  </div>

  <div class="sec">Semester Breakdown</div>
  {_semester_tables(report["semesters"])}

  <div class="sec">Suggestions</div>
  <div class="card"><ul class="tips">{sug}</ul></div>

  <div class="foot">BUITEMS Copilot · Academic audit generated on your device · No data leaves the university network</div>

</div></body></html>'''
