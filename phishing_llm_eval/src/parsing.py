"""Structured-extraction stage: free-form LLM responses -> 3 persona records.

Uses a deterministic LLM (temperature = 0) as a JSON extractor. The downstream
analysis assumes exactly three personas per workflow, with exactly one marked
as vulnerable.
"""
from __future__ import annotations

import json
import re
import time

from openai import OpenAI

from .config import PARSE_MODEL, PARSE_PARAMS, PARSE_PROVIDER, REQUEST_DELAY
from .llm_client import call_llm, get_client
from .prompts import PARSE_PROMPT

EXPECTED_PERSONAS_PER_WORKFLOW = 3


def make_parser_client() -> tuple[OpenAI, float]:
    """Return (client, request-delay) for the configured parsing model."""
    client = get_client(PARSE_PROVIDER)
    delay = REQUEST_DELAY.get(PARSE_PROVIDER, 2.0)
    return client, delay


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text


def parse_response(raw: dict, parser_client: OpenAI, parser_delay: float) -> list[dict]:
    """Parse one raw workflow into 3 structured persona records."""
    prompt = PARSE_PROMPT.format(
        prompt1_response=raw["prompt1_response"],
        prompt2_response=raw["prompt2_response"],
    )
    text = call_llm(parser_client, PARSE_MODEL,
                    [{"role": "user", "content": prompt}],
                    PARSE_PARAMS)
    time.sleep(parser_delay)

    personas = json.loads(_strip_markdown_fences(text))
    if not isinstance(personas, list) or len(personas) != EXPECTED_PERSONAS_PER_WORKFLOW:
        got = len(personas) if isinstance(personas, list) else type(personas).__name__
        raise ValueError(f"Expected {EXPECTED_PERSONAS_PER_WORKFLOW} personas, got {got}")

    for i, persona in enumerate(personas):
        persona.update({
            "provider": raw["provider"],
            "model_name": raw["model_name"],
            "model_id": raw["model_id"],
            "run": raw["run"],
            "persona_id": f"P{i + 1}",
            "prompt1_response": raw["prompt1_response"],
            "prompt2_response": raw["prompt2_response"],
        })

    return personas
