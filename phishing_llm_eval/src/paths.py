"""Canonical project paths.

Resolved relative to this file so notebooks, scripts, and modules always read
from / write to the same locations regardless of the caller's CWD.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"

RAW_RESPONSES = DATA_DIR / "raw_responses.json"
PARSED_PERSONAS = DATA_DIR / "parsed_personas.json"

DATASET_CSV = RESULTS_DIR / "dataset.csv"
ANALYSIS_SUMMARY_CSV = RESULTS_DIR / "analysis_summary.csv"
TOXICITY_CSV = RESULTS_DIR / "toxicity_scores.csv"
