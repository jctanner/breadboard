"""Render the report's testing overview with Matplotlib.

From the repository root:
  .venv/bin/python .ledger/notes/assets/strat-workflow-testing/plot.py

The JSON preserves unknown values as null. They receive labels, not data points.
"""

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/strat-workflow-report-mpl")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter


def render():
    directory = Path(__file__).resolve().parent
    data = json.loads((directory / "data.json").read_text())
    levels = {item["level"]: item for item in data["levels"]}
    recorded = "#233947"
    projected = "#306B9A"
    muted = "#68737C"

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "svg.fonttype": "none",
    })
    fig, axes = plt.subplots(3, 1, figsize=(9, 10.3), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.865, bottom=0.245, hspace=0.39)
    fig.suptitle("Testing levels: cost, time and remaining uncertainty",
                 x=0.12, y=0.98, ha="left", fontsize=16, fontweight="bold")
    fig.text(0.12, 0.945, "Cost/time cover both designs; failure-rate bounds apply to each design.",
             fontsize=11, color=muted)
    fig.legend(handles=[
        Line2D([0], [0], color=recorded, marker="o", label="Recorded Opus reference"),
        Line2D([0], [0], color=projected, linestyle="--", marker="o",
               markerfacecolor="white", label="Projection / zero-failure scenario"),
    ], loc="upper left", bbox_to_anchor=(0.11, 0.923), frameon=False, ncol=2,
       fontsize=10, handlelength=2.5)

    for ax in axes:
        ax.set_xlim(0.65, 5.45)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#E3E7EB", linewidth=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["bottom", "left"]].set_color("#9CA6AD")
        ax.tick_params(axis="both", length=0, pad=7)
        ax.axvspan(4.55, 5.45, color="#F4F2EB", zorder=0)

    def label(ax, x, y, text, offset=10):
        ax.annotate(text, (x, y), textcoords="offset points", xytext=(0, offset),
                    ha="center", va="bottom" if offset >= 0 else "top", fontsize=11)

    cost, time, bound = axes
    cost.set_title("Pipeline budget for each level", loc="left", pad=11)
    cost.set_ylabel("US dollars")
    cost.set_ylim(-500, 11000)
    cost.set_yticks([0, 3000, 6000, 9000])
    cost.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))
    cost.plot([2, 3, 4], [levels[i]["cost_usd"] for i in [2, 3, 4]],
              color=projected, linestyle="--", linewidth=2)
    cost.scatter([3, 4], [levels[i]["cost_usd"] for i in [3, 4]],
                 edgecolors=projected, facecolors="white", s=55, linewidth=1.8, zorder=3)
    cost.plot([1, 2], [levels[i]["cost_usd"] for i in [1, 2]],
              color=recorded, marker="o", linewidth=2, markersize=6, zorder=4)
    for i in [1, 2, 3, 4]:
        label(cost, i, levels[i]["cost_usd"], f"${levels[i]['cost_usd']:,.2f}" if i < 3
              else f"${levels[i]['cost_usd']:,.0f}")
    cost.text(5, 0.47, "Extra cost\nnot measured", ha="center", va="center",
              transform=cost.get_xaxis_transform(), color=muted, fontsize=10)

    time.set_title("Recorded job time", loc="left", pad=11)
    time.set_ylabel("Job hours")
    time.set_ylim(-0.12, 3.05)
    time.set_yticks([0, 1, 2, 3])
    time.plot([1, 2], [levels[i]["job_hours"] for i in [1, 2]],
              color=recorded, marker="o", linewidth=2, markersize=6)
    label(time, 1, levels[1]["job_hours"], "0.98 h*")
    label(time, 2, levels[2]["job_hours"], "2.33 h")
    for i in [3, 4]:
        time.text(i, 0.45, "Ten-RFE time\nnot measured", ha="center", va="center",
                  transform=time.get_xaxis_transform(), color=muted, fontsize=10)
    time.text(5, 0.45, "Depends\non judge", ha="center", va="center",
              transform=time.get_xaxis_transform(), color=muted, fontsize=10)

    bound.set_title("Remaining uncertainty if every qualifying run succeeds", loc="left", pad=11)
    bound.set_ylabel("Upper failure rate (%)")
    bound.set_ylim(-1.5, 37)
    bound.set_yticks([0, 10, 20, 30])
    bound.plot([3, 4], [levels[i]["upper_failure_rate_percent"] for i in [3, 4]],
               color=projected, linestyle="--", marker="o", markerfacecolor="white",
               markeredgewidth=1.8, linewidth=2, markersize=7)
    for i in [3, 4]:
        label(bound, i, levels[i]["upper_failure_rate_percent"],
              f"{levels[i]['upper_failure_rate_percent']}%")
    bound.text(1.5, 0.43, "No reliability claim", ha="center", va="center",
               transform=bound.get_xaxis_transform(), color=muted, fontsize=10)
    bound.text(5, 0.43, "Evaluates\ncontent quality", ha="center", va="center",
               transform=bound.get_xaxis_transform(), color=muted, fontsize=10)
    bound.set_xticks([1, 2, 3, 4, 5], labels=[
        "L1\nSmoke\n1 RFE",
        "L2\nBatch baseline\n3 RFEs",
        "L3\nPilot\n10 runs/design",
        "L4\nReliability\n60 runs/design",
        "L5\nContent judging\nSaved outputs",
    ])
    bound.tick_params(axis="x", labelsize=10.5, pad=10)
    fig.text(0.12, 0.055,
             "L1/L2: one Opus pair each. *L1 averages historical jobs with transport interruptions.\n"
             "L3/L4: ten RFEs per run; costs projected from the three-RFE reference.\n"
             "Failure bounds use the approximate 95% zero-failure method, per design.\n"
             "Budgets are not cumulative. Judge spend and quota waits are additional.\n"
             "L5 can evaluate earlier outputs without waiting for L4.",
             fontsize=9.5, linespacing=1.6, color=muted, va="bottom")

    fig.savefig(directory / "overview.png", dpi=240, facecolor="white")
    fig.savefig(directory / "overview.svg", facecolor="white", metadata={"Date": None})
    plt.close(fig)


if __name__ == "__main__":
    render()
