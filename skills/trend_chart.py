# skills/trend_chart.py — GPA trend line chart across semesters (returns an image path).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")   # no display needed, just save the image
import matplotlib.pyplot as plt

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
        return None   # need at least 2 points for a trend

    # ZIRA theme colors
    ESP = "#1a0f08"; GOLD = "#D4A23A"; CREAM = "#F5EDE1"

    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)

    ax.plot(labels, gpas, color=GOLD, linewidth=3, marker="o",
            markersize=10, markerfacecolor=ESP, markeredgecolor=GOLD, zorder=3)

    # value labels above each point
    for x, y in zip(labels, gpas):
        ax.annotate(f"{y}", (x, y), textcoords="offset points",
                    xytext=(0, 12), ha="center", color=ESP, fontweight="bold")

    ax.set_ylim(0, 4.2)
    ax.set_ylabel("GPA", color=ESP, fontweight="bold")
    ax.set_title("GPA Trend Across Semesters", color=ESP, fontsize=14, fontweight="bold", pad=14)
    ax.grid(True, alpha=0.2, color=ESP)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=ESP)

    os.makedirs("data/charts", exist_ok=True)
    path = os.path.abspath("data/charts/gpa_trend.png")
    plt.tight_layout()
    plt.savefig(path, facecolor=CREAM)
    plt.close()
    return path


# quick test
if __name__ == "__main__":
    import json
    data = json.load(open("data/student.json", encoding="utf-8"))
    p = trend_chart(data)
    print("Chart saved at:", p if p else "(not enough data)")