# Insights

Five observations from the audit that travel beyond the specific dataset. None of them depend on a particular model family — they are properties of how LLMs are evaluated and deployed today.

---

## 1. Demographic bias can appear even when the language is non-toxic

The Detoxify scores in this study are uniformly near zero (mean 0.0016, max 0.0844) — yet the gender × vulnerability χ² is 130.34 (*p* < 10⁻²⁵). That is not a contradiction: **toxicity classifiers measure surface harm in the model's *words*. Bias here lives in the model's *picks*.**

When the experimental signal is "which of three options does the model select?", a perfectly polite response can still be discriminatory. Practical consequences:

- **Toxicity benchmarks do not certify a model as safe for selection-based tasks.** Many providers ship toxicity scores as part of "responsible AI" documentation; this study shows that those scores are necessary but nowhere near sufficient.
- **Refusal training is the wrong tool for selection bias.** The model never says anything refuseable; it just chooses unevenly. Mitigation has to act at the *decision* layer, not the *language* layer.
- **`figures/fig11_bias_vs_toxicity.png` makes this concrete:** Llama 4 Scout sits at the extreme right of the bias axis (χ² = 75) and at the *bottom* of the toxicity axis. The two metrics are essentially independent.

## 2. Cross-model variation matters more than aggregate statistics

Aggregate "LLMs are biased" headlines obscure the actionable signal. In this panel:

| Model | Direction |
|---|---|
| Gemma 3 4B | 100 % female picks |
| Llama 4 Scout | 100 % non-binary picks |
| Ministral 8B | 72 % male picks |
| Mistral Nemo | balanced (12 F / 11 M, χ² *p* = 0.47) |

Same prompts, same temperature, same forced-choice structure — different alignment. **Two checkpoints from the same provider can have opposite bias directions.** The implication for practitioners is operational: every deployed model needs its own audit. Generalising bias profiles across model families is unsafe.

## 3. Prompt robustness is a load-bearing assumption

Every result here is conditioned on **one** specific prompt pair (lifted verbatim from the Week 5 lecture, slide p. 149). LLMs are well known to be prompt-sensitive — small phrasing changes can produce different outputs.

Two robustness questions follow naturally:

1. *Stability*: do we see the same bias direction if the prompt is paraphrased?
2. *Mitigability*: does explicitly forbidding demographic reasoning shrink the bias?

`docs/robustness_plan.md` and `scripts/run_robustness.py` provide an experimental template for both. Until that experiment is run, the right disclaimer is: "the bias observed under this prompt formulation is X." It is not "model M is biased in direction X *period*."

## 4. Bias-aware prompting deserves to be tested as a mitigation

A cheap intervention worth measuring: adding to the vulnerability-selection prompt an explicit instruction to **not** infer phishing vulnerability from gender / ethnicity / nationality / age, and to base decisions on behavioural and cybersecurity evidence instead.

`src/mitigation_prompts.py::PROMPT_B_VULN` implements one such variant. Three plausible outcomes:

- **Bias persists.** Instruction-following is decoupled from internalised priors. This would be the strongest argument for structural fixes (training-data curation, RLHF with explicit fairness objectives) over prompting.
- **Bias shrinks but does not vanish.** Most likely. Implies bias-aware prompting is a useful first line, not a complete fix.
- **Bias inverts.** Over-correction. Some alignment training has shown this pattern (refusing to engage with demographic groups it now treats as "sensitive").

A separate Arm C in the plan tests an even stronger variant: removing protected-demographic fields from the persona representation entirely, so the model has no surface to associate vulnerability with. If bias survives Arm C, it has migrated to behavioural-trait proxies (e.g. assigning "trusting" disproportionately to certain personas at generation time) — which is itself a finding.

## 5. Practical risks if LLMs are used in security assessment

The deployment scenarios that motivated this study are not hypothetical — vendors routinely propose LLMs for:

- automated risk-scoring of users for adaptive authentication
- targeted-phishing-training selection ("which employees should we send the simulated phish to?")
- red-team persona generation
- writing security awareness training tailored to a "vulnerable demographic"

Deploying a biased model in any of these workflows would produce concrete harms:

| Workflow | Failure mode |
|---|---|
| Risk-scoring for adaptive auth | Disproportionate friction (extra MFA challenges, soft-locks) for groups the model marks "vulnerable" — irrespective of actual posture |
| Targeted training selection | Over-training stereotypically "vulnerable" groups, under-training stereotypically "safe" ones — leaving the second group genuinely under-protected |
| Red-team persona generation | Reinforcing the operator's mental model that some demographics are easy targets, biasing both training scenarios and post-incident analyses |
| Awareness-content tailoring | Patronising or stereotype-coded materials sent to specific groups |

Two of these — adaptive auth and training selection — are decisions the user typically does not see, which is the worst case. The bias is invisible to them and looks objective to the security team.

**Recommendation.** If you are evaluating an LLM for any selection-based security task, run a forced-choice audit on your specific model + provider before deployment. The audit in this repo costs ≈ 285 two-turn API calls per model and is reproducible from `scripts/run_collection.py` + `scripts/run_analysis.py`.
