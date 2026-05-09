"""Robustness experiment runner: collect Arm A / B / C in parallel.

This is a TEMPLATE. It is fully runnable when API keys are present in
src/config.py, and is a no-op (with a clear message) when they are not. It
re-uses src.llm_client.run_prompt_workflow so the original two-stage protocol
is preserved exactly; only the prompt strings change between arms.

Output:
  data/robustness/<arm>_raw.json   - one file per arm, same schema as
                                     data/raw_responses.json

Each row carries an `arm` field ("A" / "B" / "C") so downstream analysis can
join all three for comparison.

Usage:
    python -m scripts.run_robustness --arm A --runs 22
    python -m scripts.run_robustness --arms A,B,C --runs 10
    python -m scripts.run_robustness --arms B,C --providers groq,mistral --runs 10

Recommended N for a 3-arm comparison on each model: 20+ runs per arm so the
within-arm chi-square has decent power. The free-tier audit was 22.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import API_KEYS, PROVIDERS, REQUEST_DELAY
from src.llm_client import call_llm, get_client
from src.mitigation_prompts import ARMS
from src.paths import DATA_DIR

OUT_DIR = DATA_DIR / "robustness"
MAX_CONSECUTIVE_FAILS = 3


def _workflow(client, model_id: str, persona_prompt: str, vuln_prompt: str,
              delay: float) -> dict:
    """One A/B/C-style two-turn dialogue with an arm-specific prompt pair."""
    messages_p1 = [{"role": "user", "content": persona_prompt}]
    response_p1 = call_llm(client, model_id, messages_p1)
    time.sleep(delay)

    messages_p2 = [
        {"role": "user", "content": persona_prompt},
        {"role": "assistant", "content": response_p1},
        {"role": "user", "content": vuln_prompt},
    ]
    response_p2 = call_llm(client, model_id, messages_p2)
    time.sleep(delay)

    return {"prompt1_response": response_p1, "prompt2_response": response_p2}


def collect_arm(arm: str, providers: list[str], runs_per_model: int) -> Path:
    if arm not in ARMS:
        raise ValueError(f"Unknown arm '{arm}', expected one of {list(ARMS)}")
    arm_cfg = ARMS[arm]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{arm}_raw.json"

    if out_file.exists():
        with out_file.open("r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = []
    completed = {(r["provider"], r["model_name"], r["run"]) for r in results}
    print(f"[arm {arm} / {arm_cfg['name']}] resuming from {len(results)} workflows")

    for provider_name in providers:
        if not API_KEYS.get(provider_name):
            print(f"  [{provider_name}] SKIPPED -- no API key")
            continue
        client = get_client(provider_name)
        delay = REQUEST_DELAY.get(provider_name, 2.0)

        for model_cfg in PROVIDERS[provider_name]["models"]:
            consecutive_fails = 0
            for run in range(1, runs_per_model + 1):
                key = (provider_name, model_cfg["name"], run)
                if key in completed:
                    continue
                if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                    print(f"    skipping {provider_name}/{model_cfg['name']} (>=3 fails)")
                    break
                try:
                    out = _workflow(client, model_cfg["id"],
                                    arm_cfg["persona"], arm_cfg["vuln"], delay)
                    results.append({
                        "arm": arm,
                        "provider": provider_name,
                        "model_name": model_cfg["name"],
                        "model_id": model_cfg["id"],
                        "run": run,
                        "timestamp": datetime.now().isoformat(),
                        **out,
                    })
                    completed.add(key)
                    consecutive_fails = 0
                    if len(results) % 5 == 0:
                        out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
                except Exception as exc:  # noqa: BLE001
                    consecutive_fails += 1
                    print(f"    FAIL {provider_name}/{model_cfg['name']} run {run}: {exc}")

    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[arm {arm}] saved {len(results)} workflows -> {out_file}")
    return out_file


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", help="Single arm to run (A, B, or C)")
    ap.add_argument("--arms", help="Comma-separated arms, e.g. A,B,C",
                    default="A,B,C")
    ap.add_argument("--providers", help="Comma-separated provider names",
                    default=",".join(PROVIDERS.keys()))
    ap.add_argument("--runs", type=int, default=20,
                    help="Runs per (arm, model). Default 20.")
    args = ap.parse_args()

    arms = [args.arm] if args.arm else [a.strip() for a in args.arms.split(",") if a.strip()]
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]

    if not any(API_KEYS.get(p) for p in providers):
        print("No API keys configured for the selected providers. "
              "Edit src/config.py to add keys, or pass --providers with a configured one.")
        return

    for arm in arms:
        collect_arm(arm, providers, args.runs)


if __name__ == "__main__":
    main()
