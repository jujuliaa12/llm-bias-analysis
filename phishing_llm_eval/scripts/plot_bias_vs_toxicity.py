"""Render figures/fig11_bias_vs_toxicity.png.

Per-model gender-bias magnitude (chi-square of gender x vulnerability) on x,
mean Detoxify toxicity of vulnerability reasoning on y. Each dot is one model.
Visualises the headline finding: high bias coexists with near-zero toxicity.

Inputs:  results/dataset.csv, results/toxicity_scores.csv
Output:  figures/fig11_bias_vs_toxicity.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import chi2_contingency

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.paths import DATASET_CSV, FIGURES_DIR, RESULTS_DIR
from src.stats_tests import standardise_columns

OUT = FIGURES_DIR / "fig11_bias_vs_toxicity.png"


def collect() -> pd.DataFrame:
    df = standardise_columns(pd.read_csv(DATASET_CSV, encoding="utf-8-sig"))
    tox = pd.read_csv(RESULTS_DIR / "toxicity_scores.csv")
    rows = []
    for model in df["Model"].unique():
        grp = df[df["Model"] == model]
        ct = pd.crosstab(grp["Gender_Clean"], grp["Is_Vulnerable"])
        if ct.shape[0] < 2 or ct.shape[1] < 2:
            continue
        chi2, p, _, _ = chi2_contingency(ct)
        tox_grp = tox[tox["model"] == model]
        if tox_grp.empty:
            continue
        rows.append({
            "model": model,
            "provider": grp["Provider"].iloc[0],
            "chi2": float(chi2),
            "p": float(p),
            "mean_toxicity": float(tox_grp["toxicity"].mean()),
            "max_toxicity": float(tox_grp["toxicity"].max()),
            "n_personas": int(len(grp)),
        })
    return pd.DataFrame(rows).sort_values("chi2", ascending=False).reset_index(drop=True)


def render(m: pd.DataFrame, out: Path = OUT) -> None:
    sns.set_theme(style="whitegrid", palette="Set2")
    fig, ax = plt.subplots(figsize=(11, 7))

    palette = sns.color_palette("Set2", n_colors=m["provider"].nunique())
    provider_color = dict(zip(sorted(m["provider"].unique()), palette))

    for _, row in m.iterrows():
        ax.scatter(row["chi2"], row["mean_toxicity"],
                   s=120, color=provider_color[row["provider"]],
                   edgecolor="black", linewidth=0.8, zorder=3,
                   label=row["provider"])
        ax.annotate(row["model"], (row["chi2"], row["mean_toxicity"]),
                    xytext=(5, 5), textcoords="offset points", fontsize=8)

    ax.axhline(0.005, color="gray", linestyle=":", alpha=0.4)
    ax.axvline(20, color="gray", linestyle=":", alpha=0.4)
    ax.text(0.02, 0.97,
            "high bias + low toxicity:\nbias is implicit,\ntoxicity screens miss it",
            transform=ax.transAxes, va="top", ha="left",
            fontsize=10, color="#444",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

    ax.set_xlabel("Per-model gender-bias magnitude (chi-square, gender x vulnerability)")
    ax.set_ylabel("Mean Detoxify toxicity of vulnerability reasoning")
    ax.set_title("The bias is implicit: high selection bias coexists with near-zero toxicity")

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), title="Provider", loc="upper right")

    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Saved {out}")


if __name__ == "__main__":
    render(collect())
