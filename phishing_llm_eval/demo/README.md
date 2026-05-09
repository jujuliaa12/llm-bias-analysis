---
title: LLM Phishing-Bias Audit
colorFrom: red
colorTo: indigo
sdk: streamlit
sdk_version: "1.51.0"
app_file: demo/app.py
pinned: false
license: mit
short_description: Interactive viewer for an 855-persona LLM phishing-bias audit
---

# LLM Phishing-Vulnerability Bias Audit — Demo

Interactive Streamlit app over the audit's 855-persona dataset. Read-only — no
API calls, no secrets, runs entirely off `results/dataset.csv`.

## Run locally

```bash
pip install -r requirements.txt streamlit altair
streamlit run demo/app.py
```

## Deploy on Hugging Face Spaces

1. Create a new Space — SDK: **Streamlit**.
2. Push this repo (or copy `demo/`, `src/`, `results/dataset.csv`,
   `requirements.txt`, and this `demo/README.md`).
3. Spaces reads the YAML frontmatter at the top of this file:
   `app_file = demo/app.py`, `sdk = streamlit`. No further config required.

## What it shows

- **Headline KPIs.** Personas, vulnerable picks, gender χ², age *t*-stat — all
  recomputed live from the filtered dataset.
- **Tabs.**
  1. *Gender* — vulnerability rate per gender vs. the 33.3 % baseline.
  2. *Age* — distribution overlay for vulnerable vs. non-vulnerable.
  3. *Domain / Education* — top-15 domains, education-level table.
  4. *Per-model* — sortable table of every (provider, model) configuration's
     dominant vulnerable gender and per-model χ².
  5. *Drill-down* — pick any persona and read the model's actual stated
     reasoning (the Prompt 2 response).

## What it intentionally does *not* show

- A claim that any demographic group is more or less susceptible to phishing
  in real life. The findings are about **LLM behaviour under controlled
  prompts**, not about people.
- Live model inference. Adding new collection runs is a separate flow — see
  `scripts/run_collection.py` and `scripts/run_robustness.py` in the repo.
