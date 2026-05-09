"""Statistical tests used in the bias evaluation.

Each function takes the cleaned dataset and returns a small result dict so the
notebooks, scripts, and any future analyses share one canonical implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact, mannwhitneyu, ttest_ind


@dataclass
class TestResult:
    name: str
    statistic: float
    p_value: float
    extras: dict


def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add `*_Clean` columns used throughout the analysis."""
    out = df.copy()
    out["Age"] = pd.to_numeric(out["Age"], errors="coerce")
    out["Years_of_Experience"] = pd.to_numeric(out["Years_of_Experience"], errors="coerce")
    out["Gender_Clean"] = out["Gender"].str.strip().str.title()
    out.loc[out["Gender_Clean"].str.contains("Non", case=False, na=False), "Gender_Clean"] = "Non-Binary"
    out["Domain_Clean"] = out["Domain_of_Work"].str.strip().str.title()
    out["Education_Clean"] = out["Education_Level"].str.strip().str.title()
    out["Location_Clean"] = out["Location"].str.strip().str.title()
    return out


def gender_chi_square(df: pd.DataFrame) -> TestResult:
    ct = pd.crosstab(df["Gender_Clean"], df["Is_Vulnerable"])
    chi2, p, dof, expected = chi2_contingency(ct)
    return TestResult(
        name="gender_chi_square",
        statistic=float(chi2),
        p_value=float(p),
        extras={"dof": int(dof), "contingency": ct, "expected": expected},
    )


def _cohens_d(a: pd.Series, b: pd.Series) -> float:
    pooled = np.sqrt((a.std() ** 2 + b.std() ** 2) / 2)
    return float((a.mean() - b.mean()) / pooled) if pooled else float("nan")


def welch_ttest(df: pd.DataFrame, column: str) -> TestResult:
    """Welch's t-test of `column` between vulnerable and non-vulnerable rows."""
    vuln = df.loc[df["Is_Vulnerable"] == "Yes", column].dropna()
    non_vuln = df.loc[df["Is_Vulnerable"] == "No", column].dropna()
    t_stat, p = ttest_ind(vuln, non_vuln, equal_var=False)
    u_stat, p_u = mannwhitneyu(vuln, non_vuln, alternative="two-sided")
    return TestResult(
        name=f"welch_ttest[{column}]",
        statistic=float(t_stat),
        p_value=float(p),
        extras={
            "vuln_mean": float(vuln.mean()),
            "vuln_std": float(vuln.std()),
            "vuln_n": int(len(vuln)),
            "non_mean": float(non_vuln.mean()),
            "non_std": float(non_vuln.std()),
            "non_n": int(len(non_vuln)),
            "cohens_d": _cohens_d(vuln, non_vuln),
            "mannwhitney_u": float(u_stat),
            "mannwhitney_p": float(p_u),
        },
    )


def fisher_per_category(df: pd.DataFrame, column: str, min_n: int = 5) -> pd.DataFrame:
    """Fisher's exact test of `column == value` vs the rest, for each value with n>=min_n."""
    rows = []
    counts = df[column].value_counts()
    for value in counts[counts >= min_n].index:
        in_grp = df[df[column] == value]
        out_grp = df[df[column] != value]
        table = [
            [(in_grp["Is_Vulnerable"] == "Yes").sum(), (in_grp["Is_Vulnerable"] == "No").sum()],
            [(out_grp["Is_Vulnerable"] == "Yes").sum(), (out_grp["Is_Vulnerable"] == "No").sum()],
        ]
        odds_ratio, p_val = fisher_exact(table)
        rows.append({
            "value": value,
            "n": int(counts[value]),
            "odds_ratio": float(odds_ratio),
            "p_value": float(p_val),
        })
    return pd.DataFrame(rows).sort_values("p_value").reset_index(drop=True)


def vulnerability_rate_by(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Per-group counts and vulnerability rate (%) for `column`."""
    grouped = df.groupby(column).agg(
        total=("Is_Vulnerable", "count"),
        vulnerable=("Is_Vulnerable", lambda s: (s == "Yes").sum()),
    )
    grouped["vuln_rate"] = (grouped["vulnerable"] / grouped["total"] * 100).round(1)
    return grouped.reset_index().sort_values("vuln_rate", ascending=False)


def per_model_chi_square(df: pd.DataFrame) -> pd.DataFrame:
    """Per-(provider, model) chi-square on Gender x Is_Vulnerable."""
    rows = []
    for (prov, model), grp in df.groupby(["Provider", "Model"]):
        ct = pd.crosstab(grp["Gender_Clean"], grp["Is_Vulnerable"])
        if ct.shape[0] < 2 or ct.shape[1] < 2:
            continue
        c2, p, _, _ = chi2_contingency(ct)
        rows.append({"provider": prov, "model": model,
                     "chi2": float(c2), "p_value": float(p),
                     "n": int(grp.shape[0])})
    return pd.DataFrame(rows).sort_values("p_value").reset_index(drop=True)


def summarise(df: pd.DataFrame) -> dict:
    """Collect the headline statistics referenced in README/findings."""
    df = standardise_columns(df)
    n_total = len(df)
    n_vuln = int((df["Is_Vulnerable"] == "Yes").sum())
    gender = gender_chi_square(df)
    age = welch_ttest(df, "Age")
    return {
        "total_personas": n_total,
        "total_vulnerable": n_vuln,
        "n_models": int(df["Model"].nunique()),
        "n_providers": int(df["Provider"].nunique()),
        "gender_chi2": gender.statistic,
        "gender_p": gender.p_value,
        "age_t": age.statistic,
        "age_p": age.p_value,
        "age_cohens_d": age.extras["cohens_d"],
    }


def extract_traits(series: Iterable) -> pd.Series:
    """Split free-form `Personality_Traits` strings into a frequency Series."""
    all_traits = []
    for value in pd.Series(series).dropna():
        traits = [t.strip().lower() for t in str(value).replace(";", ",").split(",")]
        all_traits.extend(t for t in traits if t)
    return pd.Series(all_traits).value_counts()
