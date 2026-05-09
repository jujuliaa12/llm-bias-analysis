"""Run the bias-statistics pipeline against `results/dataset.csv`.

Reproduces the headline numbers in `results/analysis_summary.csv`. Useful as a
sanity check that src/stats_tests.py matches what the notebook recorded.

Usage:
    python -m scripts.run_analysis
or
    python scripts/run_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.paths import DATASET_CSV
from src.stats_tests import (
    fisher_per_category,
    gender_chi_square,
    standardise_columns,
    summarise,
    welch_ttest,
)


def main() -> None:
    df = pd.read_csv(DATASET_CSV, encoding="utf-8-sig")
    df = standardise_columns(df)

    print("=" * 60)
    print(f"Dataset: {len(df)} personas | "
          f"{df['Model'].nunique()} models | {df['Provider'].nunique()} providers")
    print("=" * 60)

    summary = summarise(df)
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\n--- Gender chi-square ---")
    g = gender_chi_square(df)
    print(f"  chi2={g.statistic:.4f}, p={g.p_value:.4g}, dof={g.extras['dof']}")
    print(g.extras["contingency"])

    print("\n--- Age Welch's t-test ---")
    a = welch_ttest(df, "Age")
    print(f"  t={a.statistic:.4f}, p={a.p_value:.4g}, "
          f"d={a.extras['cohens_d']:.4f}")
    print(f"  vuln  : n={a.extras['vuln_n']:>3d} mean={a.extras['vuln_mean']:.1f} "
          f"sd={a.extras['vuln_std']:.1f}")
    print(f"  non   : n={a.extras['non_n']:>3d} mean={a.extras['non_mean']:.1f} "
          f"sd={a.extras['non_std']:.1f}")

    print("\n--- Domain Fisher exact (top 10 by p-value) ---")
    fisher = fisher_per_category(df, "Domain_Clean", min_n=5)
    print(fisher.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
