# Methodology

Compact reference for how the dataset was produced and how the statistics were computed.

## Experimental design

Each **workflow** is a two-turn dialogue with a single model:

1. **Prompt 1 — Persona Generation.** Asks the model for three personas with constrained attributes (name, age, gender, education, traits, devices, work, country). The exact text is in `src/prompts.py::PROMPT_1` and is taken verbatim from the Week 5 lecture (slide p. 149).
2. **Prompt 2 — Vulnerability Selection.** With Prompt 1's response in the conversation history, asks the model which of the three personas is most vulnerable to phishing and why.

Each model is run **22 times** (`RUNS_PER_MODEL` in `src/config.py`). Every run yields three persona rows; one is marked `Is_Vulnerable = Yes`. Forced-choice ⇒ uniform-random selection would give a 33.3 % vulnerability rate per group; deviations are observable preferences.

## Models

14 model–provider configurations across 5 inference providers, all OpenAI-compatible:

| Provider | Models | Effective runs |
|---|---|---|
| Groq | Llama 3.1 8B, Llama 3.3 70B, Llama 4 Scout 17B | 25 each |
| Mistral | Mistral Small, Mistral Nemo, Ministral 8B | 25 each |
| Google AI | Gemma 3 4B, Gemma 3 12B, Gemma 3 27B | 20–24 |
| SambaNova | Llama 3.3 70B, DeepSeek V3, Llama 4 Maverick 17B | 7–9 (rate-limited) |
| Cerebras | Llama 3.1 8B, Qwen 3 235B | 22 each |

Generation parameters held constant: `temperature = 0.7`, `top_p = 0.9`, `max_tokens = 2048`. Retry with exponential backoff on transient errors; permanent errors (4xx, decommissioned models) raise immediately.

## Parsing

Free-text responses are parsed into structured JSON by **Mistral Small at temperature = 0.0** (see `src/parsing.py`). The parser prompt (in `src/prompts.py::PARSE_PROMPT`) instructs the LLM to extract exactly three personas, mark exactly one as `is_vulnerable = true`, and copy the vulnerability reasons from Prompt 2's text. Failed extractions are logged and skipped, not invented.

## Sample

| Quantity | Value |
|---|---:|
| Workflows | 285 |
| Persona rows | 855 |
| Vulnerable selections | 285 (33.3 % by construction) |
| Distinct models | 13 names / 14 (provider, model) configurations |
| Distinct providers | 5 |

## Statistical tests

| Axis | Test | Why |
|---|---|---|
| Gender × Is_Vulnerable | Pearson χ² | Categorical × binary, all expected ≥ 5 |
| Age, Years_of_Experience | Welch's *t* + Cohen's *d* + Mann-Whitney U | Continuous; unequal variance not assumed; non-parametric cross-check |
| Domain_of_Work | Fisher's exact, per category, *n* ≥ 5 | Many small-cell categories; per-cat unadjusted *p* reported |
| Education | Pearson χ² | Treated as categorical |
| Location | Fisher's exact, per category | Same rationale as Domain |
| Per-model gender | Per-(provider, model) χ² | Heterogeneity check |
| Reasoning text | Detoxify (`original`) | Surface toxicity floor |
| Reasoning content | Thematic coding of 25 % random sample | What the model claims to base its choice on |

Multiple-comparison correction is **not** applied — Fisher's per-category *p*-values are reported unadjusted and interpreted conservatively (we focus on the gradient, not on individual cells). Effect sizes are reported alongside *p*-values throughout.

## What the headline numbers refer to

`results/analysis_summary.csv` records:

| Field | Meaning |
|---|---|
| `total_personas` | 855 — total rows |
| `total_vulnerable` | 285 — `Is_Vulnerable == "Yes"` |
| `n_models` / `n_providers` | 13 distinct model names / 5 providers |
| `gender_chi2`, `gender_p` | Gender_Clean × Is_Vulnerable, *df* = 6 |
| `age_t`, `age_p`, `age_cohens_d` | Welch's *t* of Age between vulnerable and non-vulnerable rows |

`scripts/run_analysis.py` recomputes all of these from `results/dataset.csv` and prints the same numbers. If this script ever diverges from the saved summary, the dataset and code have drifted out of sync.

## Threats to validity

- **Single prompt pair.** Sensitivity to wording is a known LLM-evaluation issue; alternative phrasings are future work.
- **Compositional pipeline.** Prompt 1 generates the attributes Prompt 2 then selects on. Trait-level bias in Prompt 1 manifests as gender/age bias in Prompt 2's pick — the audit captures the joint effect, not the marginal.
- **Hosted inference.** Free-tier endpoints may quantise or version-pin differently than the released model checkpoints. Re-running on the same provider months later may give different results.
- **Multiple Fisher tests.** Per-category Fisher across many domains/locations inflates Type I error if interpreted naively. We report the gradient, not individual cells.
- **Parsing fidelity.** A deterministic LLM is still an LLM; rare extraction errors are possible.
