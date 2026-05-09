"""Run the two-stage prompt workflow across all configured providers.

Usage (from project root):
    python -m scripts.run_collection
or
    python scripts/run_collection.py

Reads keys from src/config.py. Saves incrementally to data/raw_responses.json
so reruns resume rather than re-spend API calls.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import API_KEYS, PROVIDERS, REQUEST_DELAY, RUNS_PER_MODEL
from src.llm_client import get_client, run_prompt_workflow
from src.paths import RAW_RESPONSES

MAX_CONSECUTIVE_FAILS = 3


def load_existing() -> list[dict]:
    if RAW_RESPONSES.exists():
        with RAW_RESPONSES.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save(results: list[dict]) -> None:
    RAW_RESPONSES.parent.mkdir(parents=True, exist_ok=True)
    with RAW_RESPONSES.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main() -> None:
    raw_results = load_existing()
    completed = {(r["provider"], r["model_name"], r["run"]) for r in raw_results}
    print(f"Resuming from {len(raw_results)} existing workflows.")

    for provider_name, provider_cfg in PROVIDERS.items():
        if not API_KEYS.get(provider_name):
            print(f"[{provider_name}] SKIPPED -- no API key")
            continue
        client = get_client(provider_name)
        delay = REQUEST_DELAY.get(provider_name, 2.0)

        for model_cfg in provider_cfg["models"]:
            consecutive_fails = 0
            for run in range(1, RUNS_PER_MODEL + 1):
                key = (provider_name, model_cfg["name"], run)
                if key in completed:
                    continue
                if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                    print(f"  Skipping {provider_name}/{model_cfg['name']} (>=3 consecutive fails)")
                    break
                try:
                    result = run_prompt_workflow(client, model_cfg["id"], delay)
                    raw_results.append({
                        "provider": provider_name,
                        "model_name": model_cfg["name"],
                        "model_id": model_cfg["id"],
                        "run": run,
                        "timestamp": datetime.now().isoformat(),
                        **result,
                    })
                    completed.add(key)
                    consecutive_fails = 0
                    if len(raw_results) % 5 == 0:
                        save(raw_results)
                except Exception as exc:  # noqa: BLE001
                    consecutive_fails += 1
                    print(f"  FAIL {provider_name}/{model_cfg['name']} run {run}: {exc}")

    save(raw_results)
    print(f"Done. {len(raw_results)} workflows saved to {RAW_RESPONSES}")


if __name__ == "__main__":
    main()
