"""Plot helpers used in `notebooks/02_analysis.ipynb`.

Functions here are deliberately thin: they reproduce the figures shipped in
`figures/` without changing palette, axes, or layout.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

EXPECTED_BASE_RATE = 33.3  # 1 of 3 personas selected as vulnerable per workflow


def configure_style() -> None:
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["figure.dpi"] = 150
    sns.set_theme(style="whitegrid", palette="Set2")


def gender_bias_figure(contingency: pd.DataFrame, vuln_rate: pd.Series,
                       chi2: float, p_value: float, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    contingency.plot(kind="bar", ax=axes[0], rot=0)
    axes[0].set(title="Persona Count by Gender and Vulnerability",
                xlabel="Gender", ylabel="Count")

    vuln_rate.plot(kind="bar", ax=axes[1], color=sns.color_palette("Set2"), rot=0)
    axes[1].set(title=f"Vulnerability Rate by Gender (chi2={chi2:.2f}, p={p_value:.4f})",
                xlabel="Gender", ylabel="Vulnerability Rate (%)")
    axes[1].axhline(y=EXPECTED_BASE_RATE, color="red", linestyle="--",
                    alpha=0.5, label=f"Expected ({EXPECTED_BASE_RATE}%)")
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight")
    plt.close(fig)


def vulnerability_rate_barh(stats: pd.DataFrame, label_col: str, title: str,
                            out: Path, top_n: int = 15) -> None:
    """Horizontal bar chart of vuln rate with the 33.3% baseline."""
    top = stats.head(top_n)
    colors = ["salmon" if rate > 40 else "skyblue" for rate in top["vuln_rate"]]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(top[label_col], top["vuln_rate"], color=colors)
    ax.axvline(x=EXPECTED_BASE_RATE, color="red", linestyle="--", alpha=0.5,
               label=f"Expected ({EXPECTED_BASE_RATE}%)")
    ax.set(xlabel="Vulnerability Rate (%)", title=title)
    ax.legend()
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight")
    plt.close(fig)


def age_bias_figure(vuln_age: pd.Series, non_vuln_age: pd.Series,
                    df: pd.DataFrame, t_stat: float, p_value: float,
                    out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].hist(vuln_age, bins=15, alpha=0.6,
                 label=f"Vulnerable (mean={vuln_age.mean():.1f})", color="salmon")
    axes[0].hist(non_vuln_age, bins=15, alpha=0.6,
                 label=f"Non-vulnerable (mean={non_vuln_age.mean():.1f})", color="skyblue")
    axes[0].set(title="Age Distribution by Vulnerability Status",
                xlabel="Age", ylabel="Count")
    axes[0].legend()

    df.boxplot(column="Age", by="Is_Vulnerable", ax=axes[1])
    axes[1].set(title=f"Age by Vulnerability (t={t_stat:.2f}, p={p_value:.4f})",
                xlabel="Is Vulnerable", ylabel="Age")
    plt.suptitle("")
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight")
    plt.close(fig)
