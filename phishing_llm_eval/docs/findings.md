# Findings

Synthesis of the bias patterns surfaced by the audit. Numbers come from `results/analysis_summary.csv`, `results/dataset.csv`, and the per-axis cells in `notebooks/02_analysis.ipynb`.

The unifying claim: **the bias is implicit, not linguistic.** Toxicity scores are near zero across all 14 model–provider configurations, and gender is almost never explicitly named in the model's stated reasoning. The bias appears only when you tally *which* persona gets selected. That makes it harder to detect with the language-level safeguards (toxicity classifiers, refusal training) that providers ship.

---

## 1. Gender bias is significant and direction-flips between models

**Aggregate.** χ² = 130.34, *df* = 6, *p* < 10⁻²⁵. Vulnerability rate by gender:

| Gender | Vulnerability rate | Δ vs. 33.3 % baseline |
|---|---:|---:|
| Non-binary | 69.3 % | +36.0 |
| Female | 28.6 % | −4.7 |
| Male | 18.4 % | −14.9 |

A 69.3 % selection rate for non-binary personas is more than double the forced-choice baseline. There is no phishing-research finding that supports this.

**Per-model decomposition** (vulnerable selections out of total runs):

| Model | Pattern |
|---|---|
| Gemma 3 4B (Google AI) | 24/24 = **100 % female** |
| Llama 4 Scout (Groq) | 25/25 = **100 % non-binary** |
| Llama 4 Maverick (SambaNova) | dominantly non-binary |
| DeepSeek V3 (SambaNova) | dominantly non-binary |
| Ministral 8B (Mistral) | 18/25 = **72 % male** — only model that flips this way |
| Mistral Nemo | 12 F / 11 M — most balanced |

→ Bias is not a property of "LLMs" but a property of the specific model + alignment pipeline. Two models from the same provider can disagree dramatically (Gemma 3 4B vs. Gemma 3 27B; Llama 4 Scout vs. Llama 3.1 8B).

## 2. Younger and less-experienced personas are disproportionately picked

| Quantity | Vulnerable | Non-vulnerable |
|---|---:|---:|
| Age, mean ± SD | 28.7 ± 11.7 | 34.4 ± 8.9 |
| Experience (yr), mean ± SD | 6.4 ± 8.6 | 9.8 ± 7.1 |

- Welch *t*(age) = −7.22, *p* = 2.1 × 10⁻¹², Cohen's *d* = −0.55 (medium).
- Welch *t*(experience) = −5.68, *p* < 10⁻⁷, *d* = −0.42 (small-to-medium).

Sheng et al. (2010) did find younger adults more susceptible to phishing in laboratory studies, so the *direction* aligns with one strand of the literature. The *strength* — a medium effect across every model in the panel — is much stronger than the empirical evidence justifies, suggesting the model is leaning on the heuristic rather than weighing evidence.

## 3. Education and occupation tracks digital-literacy stereotypes

- **Education.** χ² = 402.91, *p* < 10⁻⁸⁰. Vulnerability is concentrated in High School and Bachelor's-in-progress personas; Master's / PhD personas are systematically under-represented among vulnerable selections.
- **Domain (Fisher's exact, *n* ≥ 5 per category).** Arts and creative roles are over-represented among vulnerable selections (odds ratio → ∞ in several small-*n* categories); IT / Engineering / Data / AI roles are *under-represented* (odds ratios near 0).

This pattern matches a folk-theory of "non-technical → digitally illiterate → phishing-vulnerable" that Parsons et al. (2013) explicitly contradict: prior training and scam exposure matter much more than occupation. The model is encoding the folk theory.

## 4. Geographic over-representation of developing nations

Top vulnerable-persona locations (raw counts among 285 vulnerable picks):

| Location | n |
|---|---:|
| India | 44 |
| Mexico | 34 |
| Brazil | 28 |
| Nigeria | 19 |

These dominate even after accounting for the model's own choice of where to *generate* personas. Read alongside the gender and education findings, the picture is consistent: the model encodes "vulnerability ≈ less educated, less experienced, non-Western, non-male" — a composite stereotype.

## 5. Personality traits are a covert proxy

Trait-level over-representation in vulnerable personas (top 5):

| Trait | Vulnerable count | Non-vuln count |
|---|---:|---:|
| trusting | high | low |
| naive | high | ~0 |
| curious | high | medium |
| impulsive | high | low |
| over-confident | high | low |

Traits common in non-vulnerable personas: `analytical`, `cautious`, `detail-oriented`, `methodical`. The model assigns "trusting"/"naive" to the personas it is about to mark as vulnerable in Prompt 2 — Prompt 1's persona generation already plants the seeds for Prompt 2's choice. This is a real risk for any pipeline that uses LLMs to generate *and then evaluate* user profiles.

## 6. Toxicity is uniformly near zero

Detoxify (`original`) on the model's free-text vulnerability reasoning:

- **Toxicity.** mean = 0.0016, max = 0.0844. (`results/toxicity_scores.csv`).
- **Severe toxicity / threat / identity attack.** All means below 0.0002.

Reading just the *language* of the responses, every model looks safe. The bias only becomes visible when you tally selections.

## 7. Qualitative reasoning rarely cites gender

Thematic coding of a random 25 % sample (*n* = 71) of vulnerable selections counted reasoning categories:

| Category | Frequency in reasoning |
|---|---:|
| technology / digital literacy | most common |
| experience / inexperience | second |
| personality (trusting, impulsive, …) | third |
| age | fourth |
| education | fifth |
| **gender** | rarely |

Gender is the **strongest** statistical predictor (χ² = 130) but appears almost **nowhere** in the model's stated reasons. The bias propagates through correlated proxies: the model assigns "trusting" or "naive" to certain genders in Prompt 1, then selects on those traits in Prompt 2. From the user's perspective the explanation looks neutral.

## Implications

1. **Toxicity benchmarks alone do not certify a model as safe.** Every model in this panel passes a Detoxify-style screen. Several still produce flagrantly biased selections.
2. **Per-model audit, not per-family.** Two checkpoints from the same provider can have opposite bias directions (Gemma 4B all-female vs. some Gemma variants; Llama 4 Scout vs. Llama 3.1 8B).
3. **Beware compositional pipelines.** When the same model both *generates* attributes and *acts* on them downstream, the bias compounds invisibly.
4. **Forced-choice probes are cheap and informative.** This entire audit costs ~285 two-turn API calls per model. Any organisation considering LLM-driven security workflows can afford to run it.
