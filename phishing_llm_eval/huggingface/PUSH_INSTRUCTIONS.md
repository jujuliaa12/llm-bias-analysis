# Pushing to Hugging Face

The `huggingface/dataset/` folder is ready to upload as a Hugging Face dataset.
Two ways to push it. Pick one.

## Option A — `huggingface_hub` (recommended)

```bash
pip install huggingface_hub

# 1. One-time login (browser flow). Stores a token under ~/.cache/huggingface/.
huggingface-cli login

# 2. Push the prepared folder as a dataset.
#    Replace Julia569922 below.
huggingface-cli upload \
    Julia569922/phishing-llm-bias-audit \
    huggingface/dataset \
    . \
    --repo-type=dataset \
    --commit-message "Initial release of LLM phishing-bias audit dataset"
```

The first `huggingface-cli upload` call also creates the dataset repo if it
doesn't exist. After it finishes, your dataset is at:

```
https://huggingface.co/datasets/Julia569922/phishing-llm-bias-audit
```

## Option B — Python script (more control)

```python
# scripts/push_to_hf.py — equivalent of Option A in code form.
from huggingface_hub import HfApi

api = HfApi()
api.create_repo(
    repo_id="Julia569922/phishing-llm-bias-audit",
    repo_type="dataset",
    exist_ok=True,
)
api.upload_folder(
    folder_path="huggingface/dataset",
    repo_id="Julia569922/phishing-llm-bias-audit",
    repo_type="dataset",
    commit_message="Initial release of LLM phishing-bias audit dataset",
)
```

Run with `python scripts/push_to_hf.py` after `huggingface-cli login`.

## What's in the folder

```
huggingface/dataset/
├── README.md      ← dataset card with YAML frontmatter (HF reads this)
└── data.csv       ← copy of results/dataset.csv (855 rows × 18 cols)
```

The YAML frontmatter at the top of `README.md` configures the HF preview:

- `task_categories: text-classification`
- `tags: bias-evaluation, fairness, phishing, cybersecurity, llm-evaluation, …`
- `configs.default.data_files.split: full -> data.csv`
- `license: mit`

So users can do:

```python
from datasets import load_dataset
ds = load_dataset("Julia569922/phishing-llm-bias-audit", split="full")
```

## Verifying the YAML before push

```bash
python -c "
import yaml, re, pathlib
text = pathlib.Path('huggingface/dataset/README.md').read_text(encoding='utf-8')
m = re.match(r'^---\n(.*?)\n---', text, flags=re.DOTALL)
print(yaml.safe_load(m.group(1)))
"
```

If that prints a Python dict without errors, the YAML is well-formed.

## After the first push

To update the dataset later:

```bash
# Edit huggingface/dataset/README.md or replace data.csv, then:
huggingface-cli upload \
    Julia569922/phishing-llm-bias-audit \
    huggingface/dataset \
    . \
    --repo-type=dataset \
    --commit-message "Describe what changed"
```

## What I left for you

I prepared everything except the actual push (which needs your HF account
+ token). When you've pushed, replace `Julia569922` in the project's main
`README.md` and in the `huggingface/dataset/README.md` citation block with
your real handle.
