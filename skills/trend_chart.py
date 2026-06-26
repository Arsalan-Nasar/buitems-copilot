# skills/trend_chart.py — GPA trend chart with growth % (Georgia, compact).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

# use Georgia (installed on Windows); fall back to a serif if missing
rcParams["font.family"] = "serif"
rcParams["font.serif"] = ["Georgia", "Times New Roman", "DejaVu Serif"]

from core.grading import semester_gpa


def trend_chart(data, message=""):
    sems = data["semesters"]
    labels, gpas = [], []
    for num in sorted(sems.keys(), key=int):
        gpa = semester_gpa(sems[num]["courses"])
        if gpa is not None:
            labels.append(f"Sem {num}")
            gpas.append(gpa)

    if len(gpas) < 2:
        return None

    NAVY="#13344e"; BLUE="#2b6ca3"; INK="#1f2d3a"; GREEN="#2e8b57"; RED="#c0533b"

    # smaller, balanced size
    fig, ax = plt.subplots(figsize=(6.0, 3.4), dpi=140)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.fill_between(range(len(gpas)), gpas, 0, color=BLUE, alpha=0.08, zorder=1)
    ax.plot(range(len(gpas)), gpas, color=BLUE, linewidth=2.5, zorder=3,
            marker="o", markersize=9, markerfacecolor=NAVY,
            markeredgecolor="white", markeredgewidth=2)

    for i, g in enumerate(gpas):
        ax.annotate(f"{g:.2f}", (i, g), textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=10.5, fontweight="bold", color=NAVY)

    for i in range(1, len(gpas)):
        prev, curr = gpas[i-1], gpas[i]
        if prev > 0:
            pct = (curr - prev) / prev * 100
            color = GREEN if pct >= 0 else RED
            arrow = "\u25B2" if pct >= 0 else "\u25BC"
            ax.annotate(f"{arrow} {abs(pct):.1f}%", (i-0.5, (prev+curr)/2),
                        textcoords="offset points", xytext=(0, -18), ha="center",
                        fontsize=8.5, fontweight="bold", color=color,
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=color, lw=1, alpha=0.9))

    ax.set_ylim(0, 4.3)
    ax.set_xlim(-0.3, len(gpas)-0.7)
    ax.set_xticks(range(len(gpas)))
    ax.set_xticklabels(labels, fontsize=10, color=INK)
    ax.set_yticks([0,1,2,3,4])
    ax.set_yticklabels(["0","1","2","3","4"], fontsize=9, color="#8a9aa8")
    ax.set_title("GPA Trend Across Semesters", fontsize=13, fontweight="bold", color=NAVY, pad=12)
    ax.grid(True, axis="y", alpha=0.12, color=NAVY)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#dbe5ee")
    ax.spines["bottom"].set_color("#dbe5ee")
    ax.tick_params(length=0)

    os.makedirs("data/charts", exist_ok=True)
    path = os.path.abspath("data/charts/gpa_trend.png")
    plt.savefig(path, facecolor="white", bbox_inches="tight", pad_inches=0.2)
    plt.close()
    return path


if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    p = trend_chart(data)
    print("Chart saved at:", p if p else "(not enough data)")