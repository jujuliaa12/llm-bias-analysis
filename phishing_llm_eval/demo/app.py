"""Streamlit demo for the LLM Phishing-Vulnerability Bias Audit.

Run locally:
    streamlit run demo/app.py

Deploy on Hugging Face Spaces:
    1. Create a new Space (SDK: Streamlit).
    2. Push this repo (or just demo/app.py + results/dataset.csv + requirements.txt).
    3. The Space's app_file should be demo/app.py.

The app reads results/dataset.csv only — no API calls, no secrets needed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from scipy.stats import chi2_contingency, ttest_ind

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.stats_tests import standardise_columns

DATASET_PATH = REPO_ROOT / "results" / "dataset.csv"
EXPECTED_BASE_RATE = 33.3

st.set_page_config(
    page_title="LLM Phishing-Bias Audit",
    layout="wide",
)


@st.cache_data
def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(DATASET_PATH, encoding="utf-8-sig")
    return standardise_columns(df)


def _chi2(df: pd.DataFrame) -> tuple[float, float]:
    ct = pd.crosstab(df["Gender_Clean"], df["Is_Vulnerable"])
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return float("nan"), float("nan")
    chi2, p, _, _ = chi2_contingency(ct)
    return float(chi2), float(p)


def _age_t(df: pd.DataFrame) -> tuple[float, float]:
    v = df.loc[df["Is_Vulnerable"] == "Yes", "Age"].dropna()
    n = df.loc[df["Is_Vulnerable"] == "No", "Age"].dropna()
    if len(v) < 2 or len(n) < 2:
        return float("nan"), float("nan")
    t, p = ttest_ind(v, n, equal_var=False)
    return float(t), float(p)


df = load_dataset()

# ============================================================
# Header
# ============================================================
st.title("LLM Phishing-Vulnerability Bias Audit")
st.caption(
    "Interactive view of the 855-persona dataset from a multi-provider audit "
    "of open-source LLMs. **The bias is implicit: toxicity is near zero, "
    "but selection behaviour is highly significant.**"
)

with st.expander("What does this app show?"):
    st.markdown(
        """
        The audit asks each LLM to (1) generate three diverse personas and (2) pick
        which one is most vulnerable to phishing. With three personas per workflow,
        an unbiased model would pick each gender / age group / occupation at the
        forced-choice baseline rate of **33.3 %**. Deviations from that baseline
        are the bias signal.

        **What this is not.** A claim that any demographic group is more or less
        susceptible to phishing in real life. The findings are about *LLM
        behaviour under controlled prompts*, not about people.

        **Data source.** `results/dataset.csv` — derived from 285 two-turn
        workflows across 14 (provider, model) configurations.
        """
    )

# ============================================================
# Sidebar filters
# ============================================================
st.sidebar.header("Filters")
providers = sorted(df["Provider"].dropna().unique())
provider_pick = st.sidebar.multiselect("Provider", providers, default=providers)
filtered_models = sorted(df.loc[df["Provider"].isin(provider_pick), "Model"].unique())
model_pick = st.sidebar.multiselect("Model", filtered_models, default=filtered_models)

mask = df["Provider"].isin(provider_pick) & df["Model"].isin(model_pick)
sub = df[mask].copy()

if sub.empty:
    st.warning("No rows match the current filters.")
    st.stop()

# ============================================================
# Headline KPIs
# ============================================================
chi2, p_chi2 = _chi2(sub)
t_age, p_age = _age_t(sub)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Personas", f"{len(sub):,}")
c2.metric("Vulnerable picks", f"{(sub['Is_Vulnerable'] == 'Yes').sum():,}",
          help="One persona per workflow is forced to be marked vulnerable.")
c3.metric("Gender χ²", f"{chi2:.1f}",
          delta=f"p = {p_chi2:.1e}" if pd.notna(p_chi2) else None,
          help="Pearson chi-square of Gender × Is_Vulnerable. Higher = stronger bias.")
c4.metric("Age t-stat", f"{t_age:.2f}",
          delta=f"p = {p_age:.1e}" if pd.notna(p_age) else None,
          help="Welch's t-test of age between vulnerable and non-vulnerable picks.")

st.divider()

# ============================================================
# Tab layout
# ============================================================
tab_gender, tab_age, tab_domain, tab_models, tab_drilldown = st.tabs([
    "Gender", "Age", "Domain / Education", "Per-model", "Drill-down"
])

# ----- Gender ---------------------------------------------------
with tab_gender:
    st.subheader("Vulnerability rate by gender")
    rates = (
        sub.groupby("Gender_Clean")
           .agg(total=("Is_Vulnerable", "size"),
                vulnerable=("Is_Vulnerable", lambda s: (s == "Yes").sum()))
           .reset_index()
    )
    rates["vuln_rate"] = (rates["vulnerable"] / rates["total"] * 100).round(1)
    rates = rates[rates["total"] >= 5].sort_values("vuln_rate", ascending=False)

    chart = (
        alt.Chart(rates)
        .mark_bar()
        .encode(
            x=alt.X("Gender_Clean:N", sort="-y", title="Gender"),
            y=alt.Y("vuln_rate:Q", title="Vulnerability rate (%)",
                    scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Gender_Clean:N", legend=None),
            tooltip=["Gender_Clean", "total", "vulnerable", "vuln_rate"],
        )
    )
    baseline = alt.Chart(pd.DataFrame({"y": [EXPECTED_BASE_RATE]})).mark_rule(
        color="red", strokeDash=[6, 4]
    ).encode(y="y:Q")
    st.altair_chart(chart + baseline, width='stretch')
    st.caption("Red dashed line = 33.3 % forced-choice baseline. "
               "Above = over-selected as vulnerable; below = under-selected.")
    st.dataframe(rates, hide_index=True, width='stretch')

# ----- Age ------------------------------------------------------
with tab_age:
    st.subheader("Age distribution by vulnerability status")
    age_df = sub.dropna(subset=["Age"]).copy()
    age_df["Vuln_label"] = age_df["Is_Vulnerable"].map(
        {"Yes": "Vulnerable", "No": "Non-vulnerable"}
    )
    chart = (
        alt.Chart(age_df)
        .mark_bar(opacity=0.7)
        .encode(
            x=alt.X("Age:Q", bin=alt.Bin(maxbins=30), title="Age"),
            y=alt.Y("count()", stack=None, title="Personas"),
            color=alt.Color("Vuln_label:N", scale=alt.Scale(
                domain=["Vulnerable", "Non-vulnerable"],
                range=["#e57373", "#64b5f6"],
            )),
            tooltip=["Vuln_label", "count()"],
        )
    )
    st.altair_chart(chart, width='stretch')
    age_summary = (
        age_df.groupby("Vuln_label")["Age"]
              .agg(["count", "mean", "std", "median"])
              .round(2)
    )
    st.dataframe(age_summary, width='stretch')

# ----- Domain / Education --------------------------------------
with tab_domain:
    st.subheader("Domain of work — top vulnerability rates")
    dom = (
        sub.groupby("Domain_Clean")
           .agg(total=("Is_Vulnerable", "size"),
                vulnerable=("Is_Vulnerable", lambda s: (s == "Yes").sum()))
           .reset_index()
    )
    dom["vuln_rate"] = (dom["vulnerable"] / dom["total"] * 100).round(1)
    dom = dom[dom["total"] >= 5].sort_values("vuln_rate", ascending=False).head(15)
    chart = (
        alt.Chart(dom)
        .mark_bar()
        .encode(
            x=alt.X("vuln_rate:Q", title="Vulnerability rate (%)"),
            y=alt.Y("Domain_Clean:N", sort="-x", title=None),
            color=alt.condition(
                alt.datum.vuln_rate > 40,
                alt.value("#e57373"), alt.value("#64b5f6"),
            ),
            tooltip=["Domain_Clean", "total", "vulnerable", "vuln_rate"],
        )
    )
    baseline = alt.Chart(pd.DataFrame({"x": [EXPECTED_BASE_RATE]})).mark_rule(
        color="red", strokeDash=[6, 4]
    ).encode(x="x:Q")
    st.altair_chart(chart + baseline, width='stretch')

    st.subheader("Education level")
    edu = (
        sub.groupby("Education_Clean")
           .agg(total=("Is_Vulnerable", "size"),
                vulnerable=("Is_Vulnerable", lambda s: (s == "Yes").sum()))
           .reset_index()
    )
    edu["vuln_rate"] = (edu["vulnerable"] / edu["total"] * 100).round(1)
    edu = edu[edu["total"] >= 5].sort_values("vuln_rate", ascending=False)
    st.dataframe(edu, hide_index=True, width='stretch')

# ----- Per-model -----------------------------------------------
with tab_models:
    st.subheader("Per-model dominant vulnerable gender")
    rows = []
    for (prov, model), grp in sub.groupby(["Provider", "Model"]):
        v = grp[grp["Is_Vulnerable"] == "Yes"]
        gc = v["Gender_Clean"].value_counts()
        f = int(gc.get("Female", 0))
        m = int(gc.get("Male", 0))
        nb = int(gc.get("Non-Binary", 0))
        winner_count = max(f, m, nb)
        winner_label = (
            "Female" if f == winner_count and f > 0
            else "Male" if m == winner_count and m > 0
            else "Non-Binary" if nb > 0
            else "—"
        )
        share = (winner_count / max(len(v), 1)) * 100
        per_chi2, per_p = _chi2(grp)
        rows.append({
            "Provider": prov, "Model": model, "Runs": grp["Run"].nunique(),
            "Personas": len(grp), "Vuln": len(v),
            "F": f, "M": m, "NB": nb,
            "Dominant": f"{winner_label} ({share:.0f}%)",
            "χ²": round(per_chi2, 1) if pd.notna(per_chi2) else None,
            "p": f"{per_p:.1e}" if pd.notna(per_p) else "",
        })
    table = pd.DataFrame(rows).sort_values("χ²", ascending=False)
    st.dataframe(table, hide_index=True, width='stretch')
    st.caption("Sorted by per-model gender χ² (higher = stronger gender bias). "
               "Dominant = which gender label the model picks most often as vulnerable.")

# ----- Drill-down ----------------------------------------------
with tab_drilldown:
    st.subheader("Read the model's stated reasoning")
    only_vuln = st.toggle("Show only vulnerable picks", value=True)
    target = sub[sub["Is_Vulnerable"] == "Yes"] if only_vuln else sub

    if target.empty:
        st.info("No rows under the current filter.")
    else:
        labels = (
            target.assign(_label=lambda d: d["Provider"] + " / " + d["Model"]
                          + " — " + d["Name"].fillna("(unnamed)")
                          + " — " + d["Gender"].fillna("?")
                          + ", " + d["Age"].astype(str)
                          + ", " + d["Domain_of_Work"].fillna(""))
        )
        choice = st.selectbox("Persona", labels["_label"].tolist())
        row = labels[labels["_label"] == choice].iloc[0]
        a, b = st.columns(2)
        with a:
            st.markdown("**Persona attributes**")
            st.json({
                "Provider": row["Provider"],
                "Model": row["Model"],
                "Run": int(row["Run"]) if pd.notna(row["Run"]) else None,
                "Name": row["Name"],
                "Age": row["Age"],
                "Gender": row["Gender"],
                "Education": row["Education_Level"],
                "Domain": row["Domain_of_Work"],
                "Years_of_Experience": row["Years_of_Experience"],
                "Location": row["Location"],
                "Personality_Traits": row["Personality_Traits"],
                "Devices_and_Technologies": row["Devices_and_Technologies"],
                "Is_Vulnerable": row["Is_Vulnerable"],
            })
        with b:
            st.markdown("**Vulnerability reasoning (Prompt 2 response)**")
            reason = str(row.get("Vulnerability_Reasons") or "(none)")
            st.write(reason if reason.strip() else "(empty — non-vulnerable persona)")
            with st.expander("Full Prompt 2 response"):
                st.text(str(row.get("Prompt2_Response", "")))
            with st.expander("Full Prompt 1 response (persona generation)"):
                st.text(str(row.get("Prompt1_Response", "")))

st.divider()
st.caption(
    "Source code: github.com/Julia569922/phishing-llm-bias-audit · "
    "Dataset: results/dataset.csv · "
    "Findings: docs/findings.md"
)
