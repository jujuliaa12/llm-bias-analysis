"""Compare Arm A / B / C bias statistics side by side.

Loads parsed persona datasets for each arm (one CSV per arm in the same schema
as results/dataset.csv) and reports:

  - per-arm headline statistics (chi-square gender x vulnerability, age t-test,
    Cohen's d)
  - per-arm, per-model gender split among vulnerable picks
  - a side-by-side bar chart of vulnerability rate by gender for each arm,
    saved to figures/fig12_arm_comparison.png

For Arm A you can pass results/dataset.csv directly (the existing audit IS the
Arm-A baseline). Arm B and Arm C CSVs must be produced by running the
collection + parsing pipeline on the data/robustness/<arm>_raw.json outputs of
run_robustness.py.

Usage:
    python -m scripts.compare_prompts \
        --arm-a results/dataset.csv \
        --arm-b results/robustness_B.csv \
        --arm-c results/robustness_C.csv

Any arm CSV may be omitted; the script reports on whichever arms are provided.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.paths import FIGURES_DIR
from src.stats_tests import gender_chi_square, standardise_columns, welch_ttest

OUT = FIGURES_DIR / "fig12_arm_comparison.png"
EXPECTED_BASE_RATE = 33.3


def _load(path: str | None) -> pd.DataFrame | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        print(f"[skip] {path} does not exist")
        return None
    df = standardise_columns(pd.read_csv(p, encoding="utf-8-sig"))
    return df


def _summarise(df: pd.DataFrame, arm: str) -> dict:
    g = gender_chi_square(df)
    a = welch_ttest(df, "Age")
    return {
        "arm": arm,
        "n_personas": len(df),
        "n_vulnerable": int((df["Is_Vulnerable"] == "Yes").sum()),
        "gender_chi2": round(g.statistic, 3),
        "gender_p": g.p_value,
        "age_t": round(a.statistic, 3),
        "age_p": a.p_value,
        "age_cohens_d": round(a.extras["cohens_d"], 3),
        "age_vuln_mean": round(a.extras["vuln_mean"], 1),
        "age_non_mean": round(a.extras["non_mean"], 1),
    }


def _vuln_rate_by_gender(df: pd.DataFrame) -> pd.Series:
    ct = pd.crosstab(df["Gender_Clean"], df["Is_Vulnerable"])
    if "Yes" not in ct.columns:
        ct["Yes"] = 0
    return (ct["Yes"] / ct.sum(axis=1) * 100).round(1)


def render_comparison_figure(arm_dfs: dict[str, pd.DataFrame], out: Path = OUT) -> None:
    sns.set_theme(style="whitegrid", palette="Set2")
    arms = list(arm_dfs.keys())
    fig, axes = plt.subplots(1, len(arms), figsize=(5 * len(arms), 5), sharey=True)
    if len(arms) == 1:
        axes = [axes]

    for ax, arm in zip(axes, arms):
        rates = _vuln_rate_by_gender(arm_dfs[arm])
        rates = rates[rates.index.isin(["Female", "Male", "Non-Binary"])]
        rates.plot(kind="bar", ax=ax, color=sns.color_palette("Set2"), rot=0)
        ax.axhline(EXPECTED_BASE_RATE, color="red", linestyle="--", alpha=0.5,
                   label=f"Expected ({EXPECTED_BASE_RATE}%)")
        ax.set(title=f"Arm {arm}", xlabel="Gender", ylabel="Vulnerability rate (%)")
        ax.set_ylim(0, max(100, rates.max() * 1.1))
        ax.legend(loc="upper right")

    plt.suptitle("Vulnerability rate by gender across prompt arms", y=1.02, fontsize=13)
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Saved {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-a", help="Path to Arm A CSV (default: results/dataset.csv)",
                    default=None)
    ap.add_argument("--arm-b", help="Path to Arm B CSV", default=None)
    ap.add_argument("--arm-c", help="Path to Arm C CSV", default=None)
    args = ap.parse_args()

    a = _load(args.arm_a or "results/dataset.csv")
    b = _load(args.arm_b)
    c = _load(args.arm_c)
    arm_dfs = {k: v for k, v in [("A", a), ("B", b), ("C", c)] if v is not None}
    if not arm_dfs:
        print("No arm CSVs to compare.")
        return

    summary = pd.DataFrame([_summarise(df, arm) for arm, df in arm_dfs.items()])
    print("\n=== Arm-level summary ===")
    print(summary.to_string(index=False))

    render_comparison_figure(arm_dfs)

    if len(arm_dfs) >= 2:
        print("\n=== Direct comparison (Arm A baseline) ===")
        ref = next(iter(arm_dfs))
        for arm in arm_dfs:
            if arm == ref:
                continue
            ref_chi2 = summary.set_index("arm").loc[ref, "gender_chi2"]
            arm_chi2 = summary.set_index("arm").loc[arm, "gender_chi2"]
            print(f"  Arm {arm} vs Arm {ref}: chi2 {ref_chi2} -> {arm_chi2} "
                  f"(reduction: {ref_chi2 - arm_chi2:+.1f})")


if __name__ == "__main__":
    main()
