"""Parse raw two-turn LLM workflows into a structured persona dataset.

Bridges run_collection.py / run_robustness.py output JSON to the analysis-ready
CSV format consumed by scripts/run_analysis.py and scripts/compare_prompts.py.

Examples:
    # Re-parse the original audit (writes results/dataset.csv).
    python -m scripts.parse_responses

    # Parse a specific arm of the robustness experiment.
    python -m scripts.parse_responses --raw data/robustness/B_raw.json \
                                      --out results/robustness_B.csv

    # Sanity check without any API calls (counts workflows, prints schema).
    python -m scripts.parse_responses --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import API_KEYS
from src.parsing import make_parser_client, parse_response
from src.paths import DATA_DIR, DATASET_CSV, PARSED_PERSONAS, RAW_RESPONSES

PERSONA_COLUMNS = [
    "Provider", "Model", "Model_ID", "Run", "Persona_ID",
    "Name", "Age", "Gender", "Education_Level", "Personality_Traits",
    "Domain_of_Work", "Years_of_Experience", "Location", "Devices_and_Technologies",
    "Is_Vulnerable", "Vulnerability_Reasons",
    "Prompt1_Response", "Prompt2_Response",
]


def _row_from_persona(p: dict) -> dict:
    """Project one parsed persona dict onto the canonical CSV columns."""
    return {
        "Provider": p.get("provider", ""),
        "Model": p.get("model_name", ""),
        "Model_ID": p.get("model_id", ""),
        "Run": p.get("run", ""),
        "Persona_ID": p.get("persona_id", ""),
        "Name": p.get("name", ""),
        "Age": p.get("age", ""),
        "Gender": p.get("gender", ""),
        "Education_Level": p.get("education_level", ""),
        "Personality_Traits": p.get("personality_traits", ""),
        "Domain_of_Work": p.get("domain_of_work", ""),
        "Years_of_Experience": p.get("years_of_experience", ""),
        "Location": p.get("location", ""),
        "Devices_and_Technologies": p.get("devices_and_technologies", ""),
        "Is_Vulnerable": "Yes" if p.get("is_vulnerable") else "No",
        "Vulnerability_Reasons": p.get("vulnerability_reasons", ""),
        "Prompt1_Response": p.get("prompt1_response", ""),
        "Prompt2_Response": p.get("prompt2_response", ""),
    }


def parse_workflows(raw_path: Path, parsed_path: Path, dry_run: bool = False) -> list[dict]:
    """Parse every workflow in raw_path; resume from parsed_path if it exists."""
    raw_results = json.loads(raw_path.read_text(encoding="utf-8"))
    print(f"Loaded {len(raw_results)} raw workflows from {raw_path}")

    if dry_run:
        return []

    if parsed_path.exists():
        all_personas = json.loads(parsed_path.read_text(encoding="utf-8"))
        seen = {(p["provider"], p["model_name"], p["run"]) for p in all_personas}
        print(f"Resuming: {len(all_personas)} personas already parsed.")
    else:
        all_personas, seen = [], set()

    if any(API_KEYS.values()):
        parser_client, parser_delay = make_parser_client()
    else:
        raise RuntimeError(
            "No API keys configured. Add a key for the parser provider "
            "(default: mistral) in src/config.py before running this script."
        )

    errors = []
    for raw in raw_results:
        key = (raw["provider"], raw["model_name"], raw["run"])
        if key in seen:
            continue
        try:
            personas = parse_response(raw, parser_client, parser_delay)
            all_personas.extend(personas)
            seen.add(key)
            if len(seen) % 10 == 0:
                parsed_path.write_text(json.dumps(all_personas, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            errors.append((key, str(exc)))
            print(f"  PARSE ERROR {key}: {exc}")

    parsed_path.write_text(json.dumps(all_personas, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"Parsed: {len(all_personas)} persona records ({len(errors)} errors)")
    return all_personas


def write_csv(personas: list[dict], out_csv: Path) -> None:
    df = pd.DataFrame([_row_from_persona(p) for p in personas])
    # Maintain the canonical column order for downstream scripts.
    df = df.reindex(columns=PERSONA_COLUMNS)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    n_vuln = (df["Is_Vulnerable"] == "Yes").sum()
    print(f"Wrote {out_csv} ({len(df)} rows, {n_vuln} marked vulnerable)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=RAW_RESPONSES,
                    help="Raw responses JSON (default: data/raw_responses.json)")
    ap.add_argument("--parsed", type=Path, default=None,
                    help="Parsed personas JSON (default: <raw_stem>_parsed.json next to raw)")
    ap.add_argument("--out", type=Path, default=DATASET_CSV,
                    help="Output CSV path (default: results/dataset.csv)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Read raw file, print schema, do not call the parser API")
    args = ap.parse_args()

    raw_path: Path = args.raw
    if not raw_path.exists():
        sys.exit(f"Raw responses file not found: {raw_path}")

    if args.parsed is None:
        # data/raw_responses.json    -> data/parsed_personas.json
        # data/robustness/B_raw.json -> data/robustness/B_parsed.json
        if raw_path == RAW_RESPONSES:
            parsed_path = PARSED_PERSONAS
        else:
            parsed_path = raw_path.with_name(raw_path.stem.replace("_raw", "") + "_parsed.json")
    else:
        parsed_path = args.parsed

    if args.dry_run:
        parse_workflows(raw_path, parsed_path, dry_run=True)
        print(f"\nWould parse {raw_path} -> {parsed_path} -> {args.out}")
        print(f"CSV columns ({len(PERSONA_COLUMNS)}): {PERSONA_COLUMNS}")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    personas = parse_workflows(raw_path, parsed_path)
    write_csv(personas, args.out)


if __name__ == "__main__":
    main()
