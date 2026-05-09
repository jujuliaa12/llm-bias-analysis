# LLM Phishing-Vulnerability Bias Audit

> **Tagline.** Open-source LLMs that pass toxicity benchmarks can still make systematically discriminatory selections when asked *who is vulnerable to phishing*. This repo is the audit, the data, and the mitigation plan.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Hugging Face Dataset](https://img.shields.io/badge/HF-Dataset-yellow)](https://huggingface.co/datasets/Julia569922/phishing-llm-bias-audit) [![Streamlit demo](https://img.shields.io/badge/Streamlit-Demo-red)](demo/app.py)

A multi-provider empirical study of demographic bias in open-source LLMs when they are asked to assess phishing vulnerability. **855 persona records across 14 model–provider configurations from 5 inference providers**, evaluated with chi-square, Welch's *t*-tests, Fisher's exact tests, Detoxify toxicity scoring, and qualitative coding.

→ **Try the demo:** `streamlit run demo/app.py` (see [`demo/`](demo/))
→ **Use the dataset:** see [`huggingface/`](huggingface/) for the prepared HF dataset card and push instructions.

> **Headline finding.** The bias is *implicit*: toxicity scores are near zero, gender is rarely cited in the model's stated reasoning, yet the chi-square test of gender × vulnerability is highly significant (χ² = 130.34, *p* < 10⁻²⁵). The same models that look safe on toxicity benchmarks make systematically discriminatory selections.

> **What this study does *not* claim.** We do not claim that any demographic group is inherently more (or less) vulnerable to phishing. The study evaluates **how LLMs represent vulnerability under controlled prompts** — i.e. what the *model* internalises and selects. Findings are about LLM behaviour, not about people.

---

## Overview

Open-source LLMs are increasingly proposed as auxiliary tools in cybersecurity workflows — drafting awareness training, scoring users for risk-based authentication, profiling targets in red-team exercises. This study asks whether they are fit for that purpose, or whether they reproduce demographic stereotypes when reasoning about *who is vulnerable to phishing*.

We adapt the [DECODINGTRUST](https://arxiv.org/abs/2306.11698) evaluation paradigm to phishing using a two-stage prompt protocol from the course's Week 5 lecture (slide p. 149):

1. **Prompt 1 – Persona Generation.** The model generates three diverse personas with constrained attributes (name, age, gender, education, traits, work, devices, country).
2. **Prompt 2 – Vulnerability Selection.** Conditioned on those personas, the model picks which one is most vulnerable to phishing and explains why.

Repeated 22 times per model across 14 model–provider configurations. Forced-choice design ⇒ an unbiased model should pick each persona ~33.3 % of the time; deviations from that baseline are observable preferences.

## Research Question

> *Do open-source LLMs exhibit systematic demographic bias when generating personas and assessing their vulnerability to phishing attacks?*

Sub-questions:

- Is bias uniform across providers, or model-specific?
- Does the bias appear in the *language* of the reasoning (toxicity), or only in the *selection* (implicit)?
- Which demographic axes (gender, age, experience, education, occupation, location) carry the strongest signal?
- Can bias-aware prompting reduce it? (See `docs/robustness_plan.md`.)

## Why this matters

LLMs are already being marketed for selection-based cybersecurity tasks: adaptive authentication risk-scoring, simulated-phishing target selection, red-team persona generation, awareness-content tailoring. In every one of these, a biased model produces concrete deployment harms:

- Disproportionate friction (e.g. extra MFA challenges) for groups the model marks "vulnerable".
- Stereotyped groups over-trained on simulated phishing; "safe" groups under-trained and genuinely under-protected.
- Stereotype-coded persona libraries that bias post-incident analysis.

These harms are typically invisible to end users and look objective to the security team running the tool. **Toxicity classifiers do not catch them**, because the model never says anything overtly toxic — it just *picks* in a biased way. See `docs/insights.md` for a longer treatment.

## Methodology

| Stage | Tool / test | What it measures |
|---|---|---|
| Generation | OpenAI-compatible chat completions (T = 0.7, top-*p* = 0.9, max 2048 tokens) | Free-text persona triples + vulnerability pick |
| Parsing | Mistral Small at T = 0.0 | Free-text → structured JSON (3 personas / workflow) |
| Gender | Pearson χ² of independence | Gender × Is_Vulnerable contingency |
| Age & experience | Welch's *t*-test + Cohen's *d* + Mann-Whitney U | Continuous demographic differences |
| Domain & location | Fisher's exact (per category, *n* ≥ 5) | Categorical over-/under-representation |
| Education | Pearson χ² | Ordinal-as-categorical association |
| Toxicity | [Detoxify](https://github.com/unitaryai/detoxify) (`original`) | Surface harmfulness of reasoning text |
| Qualitative | Thematic coding of 25 % random sample | What the model *says* it is doing |

Models (14 configurations across 5 providers): Llama 3.1 / 3.3 8B–70B (Groq, SambaNova, Cerebras), Mistral Small / Nemo / Ministral 8B (Mistral), Gemma 3 4B / 12B / 27B (Google AI), DeepSeek V3, Llama 4 Scout / Maverick, Qwen 3 235B. Full table in `src/config.py` and per-model breakdown in [`docs/model_summary.md`](docs/model_summary.md).

## Dataset

- **`data/raw_responses.json`** – 285 unparsed two-turn workflows (1.2 MB).
- **`data/parsed_personas.json`** – the same workflows after deterministic JSON extraction (4.0 MB).
- **`results/dataset.csv`** – the analysis-ready 855-row table (one row per persona).
- **`results/analysis_summary.csv`** – headline statistics (regenerated by `scripts/run_analysis.py`).
- **`results/per_model_summary.csv`** – per-(provider, model) breakdown (regenerated by the same script).
- **`results/toxicity_scores.csv`** – Detoxify outputs on vulnerability-reason text.

Distribution: Female 391 (45.7 %), Male 277 (32.4 %), Non-binary 163 (19.1 %), Other 24 (2.8 %); mean age 32.5 ± 10.3; mean experience 8.6 ± 7.8 years; 285 personas (33.3 %) selected as vulnerable by construction.

## Models / providers

| Provider | Models in the panel | Free-tier API |
|---|---|---|
| Groq | Llama 3.1 8B Instant, Llama 3.3 70B Versatile, Llama 4 Scout 17B | Yes |
| Mistral | Mistral Small, Mistral Nemo, Ministral 8B | Yes |
| Google AI | Gemma 3 4B IT, Gemma 3 12B IT, Gemma 3 27B IT | Yes |
| SambaNova | Llama 3.3 70B Instruct, DeepSeek V3, Llama 4 Maverick 17B | Yes (rate-limited) |
| Cerebras | Llama 3.1 8B, Qwen 3 235B Instruct | Yes |

Per-(provider, model) counts and bias direction: see [`docs/model_summary.md`](docs/model_summary.md).

## Statistical Tests & Key Findings

| Axis | Test | Statistic | *p* | Effect | Direction |
|---|---|---:|---:|---|---|
| **Gender** | χ² | 130.34 | < 10⁻²⁵ | – | Non-binary 69.3 % vs. expected 33.3 %; Female 28.6 %; Male 18.4 % |
| **Age** | Welch *t* | −7.22 | < 10⁻¹¹ | *d* = −0.55 (medium) | Vulnerable mean 28.7, non-vuln 34.4 |
| **Experience** | Welch *t* | −5.68 | < 10⁻⁷ | *d* = −0.42 | Vulnerable mean 6.4 yr, non-vuln 9.8 yr |
| **Education** | χ² | 402.91 | < 10⁻⁸⁰ | – | High-school / undergraduate over-represented; postgraduate under |
| **Domain** | Fisher (per-cat) | – | – | – | Arts / Creative ↑, IT / Engineering ↓ among vulnerable |
| **Location** | Fisher (per-cat) | – | – | – | India (44), Mexico (34), Brazil (28), Nigeria (19) over-represented |
| **Toxicity** | Detoxify | – | – | – | Mean 0.0016, max 0.0844 — uniformly near zero |

Full numerical tables in [`docs/findings.md`](docs/findings.md); reproduced live by `scripts/run_analysis.py`.

### Model-dependent bias patterns

The aggregate χ² obscures stark model-specific behaviour:

- **Gemma 3 4B** picked **female** in 24/24 runs (100 %).
- **Llama 4 Scout** picked **non-binary** in 25/25 runs (100 %).
- **SambaNova models** picked non-binary in 22/25 selections.
- **Ministral 8B** uniquely picked **male** in 18/25 runs.
- **Mistral Nemo** was the most balanced (12 F / 11 M, χ² *p* = 0.47 — *not* significant per-model).

Bias is therefore not a property of "LLMs in general" — it is a property of the specific training pipeline. See [`docs/model_summary.md`](docs/model_summary.md) for the full breakdown.

## Important Figures

All figures live in `figures/`. The earlier evaluation set (April 7, fairness/stereotype/ethics/factuality rubric) is preserved under `figures/legacy/` for transparency.

| File | What it shows |
|---|---|
| `figures/fig01_gender_bias.png` | Gender × vulnerability counts and rate vs. 33.3 % baseline |
| `figures/fig02_age_bias.png` | Age histogram + box plot by vulnerability |
| `figures/fig02b_experience_bias.png` | Years-of-experience distribution |
| `figures/fig03_domain_bias.png` | Top 15 domains by vulnerability rate |
| `figures/fig04_education_bias.png` | Education-level vulnerability rates |
| `figures/fig05_location_bias.png` | Top 15 locations by vulnerability rate |
| `figures/fig06_cross_model.png` | Gender × Model heatmap; mean age × Model heatmap |
| `figures/fig07_personality_traits.png` | Trait frequency: vulnerable vs. non-vulnerable |
| `figures/fig08_toxicity.png` | Detoxify toxicity by model |
| `figures/fig09_qualitative_reasons.png` | Reasoning categories from the 25 % sample |
| `figures/fig10_summary.png` | Four-panel summary used in the paper |
| `figures/fig11_bias_vs_toxicity.png` | **Per-model bias magnitude vs. toxicity — visualises the implicit-bias headline** |
| `figures/fig12_arm_comparison.png` | Vulnerability rate by gender across prompt arms (populated by `scripts/compare_prompts.py`) |

## Repository Layout

```
phishing_llm_eval/
├── README.md                  ← you are here
├── requirements.txt
├── CITATION.cff
├── .gitignore
├── src/                       ← importable modules
│   ├── config.py              ← providers, models, generation params (API keys redacted)
│   ├── prompts.py             ← exact prompts from the Week 5 lecture
│   ├── mitigation_prompts.py  ← Arm A / B / C variants for the robustness experiment
│   ├── paths.py               ← canonical project paths
│   ├── llm_client.py          ← multi-provider chat-completion wrapper
│   ├── parsing.py             ← deterministic structured extraction
│   ├── stats_tests.py         ← chi-square, Welch's t, Fisher, summary
│   └── plotting.py            ← figure helpers used in the analysis notebook
├── notebooks/
│   ├── 01_data_collection.ipynb   ← end-to-end collection + parsing pipeline
│   └── 02_analysis.ipynb          ← all statistical tests & figure generation
├── scripts/
│   ├── run_collection.py      ← `python -m scripts.run_collection`
│   ├── parse_responses.py     ← raw responses JSON -> structured dataset CSV
│   ├── run_analysis.py        ← reproduces the headline statistics
│   ├── plot_bias_vs_toxicity.py ← regenerates fig11
│   ├── run_robustness.py      ← Arm A / B / C collection (template, gated on API keys)
│   └── compare_prompts.py     ← side-by-side stats + figure for arm comparison
├── demo/
│   ├── app.py                 ← Streamlit dataset explorer (headless, no secrets)
│   └── README.md              ← HF Spaces frontmatter + run instructions
├── huggingface/
│   ├── dataset/
│   │   ├── README.md          ← HF dataset card with YAML frontmatter
│   │   └── data.csv           ← copy of results/dataset.csv for HF preview
│   └── PUSH_INSTRUCTIONS.md   ← how to push to huggingface.co/datasets
├── data/                      ← raw + parsed LLM outputs (large JSON)
├── results/                   ← analysis-ready CSVs
├── figures/                   ← report-grade PNGs (+ legacy/)
└── docs/
    ├── findings.md            ← bias-by-axis synthesis
    ├── methodology.md         ← experimental protocol
    ├── model_summary.md       ← per-(provider, model) breakdown
    ├── insights.md            ← five takeaways for practitioners
    └── robustness_plan.md     ← bias-aware / reduced-demographic experiment design
```

## Reproducibility

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Reproduce the headline statistics from the saved dataset
python scripts/run_analysis.py
# → matches results/analysis_summary.csv exactly

# 3. Regenerate the bias-vs-toxicity figure
python scripts/plot_bias_vs_toxicity.py

# 4. (Optional) Regenerate the rest of the figures from notebooks/02_analysis.ipynb
jupyter notebook notebooks/02_analysis.ipynb

# 5. (Optional) Rerun data collection — needs API keys
#    Edit src/config.py to add keys for groq / mistral / google_ai / sambanova / cerebras
python scripts/run_collection.py

# 6. (Optional) Run the robustness experiment (Arms B and C)
python -m scripts.run_robustness --arms B,C --runs 20
python -m scripts.parse_responses --raw data/robustness/B_raw.json --out results/robustness_B.csv
python -m scripts.parse_responses --raw data/robustness/C_raw.json --out results/robustness_C.csv
python -m scripts.compare_prompts \
    --arm-a results/dataset.csv \
    --arm-b results/robustness_B.csv \
    --arm-c results/robustness_C.csv
```

### Robustness experiment quickstart

The mitigation experiment (Arm A baseline / Arm B bias-aware / Arm C reduced-demographic) is fully scaffolded — only API access is left to you.

1. **Add at least one provider's API key** to `src/config.py`. The Mistral key is required for the JSON-extraction parser (default `PARSE_PROVIDER`).
2. **Collect.** `python -m scripts.run_robustness --arms B,C --runs 20` — resumable, ~6 hours wall-clock on free tiers.
3. **Parse.** `python -m scripts.parse_responses --raw data/robustness/B_raw.json --out results/robustness_B.csv` (and same for C).
4. **Compare.** `python -m scripts.compare_prompts --arm-a results/dataset.csv --arm-b results/robustness_B.csv --arm-c results/robustness_C.csv` — prints χ²/*t*/*d* per arm and writes `figures/fig12_arm_comparison.png`.

Full design: [`docs/robustness_plan.md`](docs/robustness_plan.md). Prompt definitions: [`src/mitigation_prompts.py`](src/mitigation_prompts.py).

### Live demo

```powershell
pip install streamlit altair
streamlit run demo/app.py
```

Headline KPIs, per-model bias profile, gender / age / domain plots, and drill-down to read the model's actual stated reasoning for any persona. See [`demo/README.md`](demo/README.md) for HF Spaces deployment.

### Hugging Face dataset

The 855-row dataset is staged for Hugging Face publication in [`huggingface/dataset/`](huggingface/dataset/) with a populated dataset card, schema documentation, and bias-warning section. To push:

```bash
huggingface-cli login
huggingface-cli upload Julia569922/phishing-llm-bias-audit huggingface/dataset . --repo-type=dataset
```

Full instructions: [`huggingface/PUSH_INSTRUCTIONS.md`](huggingface/PUSH_INSTRUCTIONS.md).

The collection pipeline is **resumable**: it skips workflows already in `data/raw_responses.json`, so partial runs cost nothing extra. Generation parameters are pinned (T = 0.7, top-*p* = 0.9) — outputs are not bit-reproducible across providers because all models are accessed through hosted inference APIs that may version, quantise, or rate-limit independently.

## Limitations

- **SambaNova rate limits** capped 3 of its models to 7–9 runs each on the free tier (8.8 % of total workflows).
- **Cerebras free tier** exposes only 2 models versus 3 on the others.
- **LLM-based parsing** (Mistral Small at T = 0.0) is deterministic but not infallible — extraction errors are possible on unusually formatted outputs.
- **Single prompt pair.** The baseline study uses one specific Prompt 1 / Prompt 2 wording. Sensitivity to phrasing is a known issue in LLM evaluation; alternative formulations are addressed by the [robustness plan](docs/robustness_plan.md).
- **Hosted-inference variability.** Free-tier endpoints may quantise or otherwise modify the underlying model versus the released checkpoints.
- **Forced-choice design.** The 33.3 % baseline assumes the model cannot abstain; this is by construction (Prompt 2 demands a pick).
- **Behavioural ground truth is absent.** This study measures what the *model* selects, not what would actually correlate with phishing susceptibility in real users.

## Ethical Considerations

The biases identified here have direct deployment implications. A model that selects non-binary individuals as "phishing-vulnerable" 69 % of the time, or systematically associates developing-nation personas with vulnerability, would — if used in real risk-scoring — produce **discriminatory profiling** dressed up as objective security analysis. Worse, the bias is implicit: language-level safeguards (toxicity classifiers, refusal training) do not catch it, because the model never says anything overtly toxic. It just *picks* in a biased way.

We publish this study to motivate audits, not to characterise demographic groups. **None of the patterns observed reflect actual phishing susceptibility in those populations**; they reflect what the LLM has internalised. Practitioners deploying LLMs in security workflows should run an equivalent forced-choice audit on their specific model and provider before relying on its judgements.

## Future Work

1. **Run the robustness experiment** (`docs/robustness_plan.md`). Whether bias-aware prompting (Arm B) or reduced-demographic prompting (Arm C) reduces the χ² is the natural next question.
2. **Behavioural-ground-truth correlation.** Pair LLM "vulnerability" picks with actual phishing-simulation click-through rates from a separate user study. The existing literature ([Sheng et al. 2010](https://dl.acm.org/doi/10.1145/1753326.1753383); [Parsons et al. 2013](https://www.sciencedirect.com/science/article/pii/S0167404813001181)) gives a starting list of behavioural predictors.
3. **Larger panel.** Add closed-source models (GPT-4 family, Claude family, Gemini Pro) to the panel for a closed-vs-open comparison.
4. **Trait-level intervention.** Test whether constraining Prompt 1 to *also* avoid loaded personality traits (e.g. forbidding "naive" / "trusting" assignments) reduces downstream bias more than demographic-only interventions.
5. **Persistence across model versions.** Re-run the same audit when each provider updates a model checkpoint; track whether bias direction is stable across versions.

## Citation & Acknowledgements

Citation metadata is in [`CITATION.cff`](CITATION.cff) (GitHub renders a "Cite this repository" widget from it).

The two-stage prompt design (Prompt 1 persona generation → Prompt 2 vulnerability selection) follows the Week 5 lecture in the course this work was originally produced for. The evaluation framework draws on the [DECODINGTRUST](https://arxiv.org/abs/2306.11698) protocol; the toxicity-scoring layer uses [Detoxify](https://github.com/unitaryai/detoxify); the phishing-susceptibility background draws on Sheng et al. (2010), Butavicius et al. (2016), and Parsons et al. (2013).

## License

Code: MIT (see `src/` headers). Generated dataset: provided for research use; please cite this repository when redistributing.
