"""Multi-provider LLM client and the two-stage prompt workflow.

Wraps the OpenAI-compatible chat completion API so the same code path works
across Groq, Mistral, Google AI Studio, SambaNova, and Cerebras. Mirrors the
logic exercised in `notebooks/01_data_collection.ipynb`.
"""
from __future__ import annotations

import re
import time

from openai import OpenAI

from .config import API_KEYS, GENERATION_PARAMS, PROVIDERS
from .prompts import PROMPT_1, PROMPT_2

PERMANENT_ERROR_CODES = ("400", "401", "402", "403", "404", "429", "decommissioned")


def get_client(provider_name: str) -> OpenAI:
    """Create an OpenAI-compatible client for the given provider."""
    provider = PROVIDERS[provider_name]
    api_key = API_KEYS[provider_name]
    if not api_key:
        raise ValueError(f"API key for '{provider_name}' is empty. Fill it in src/config.py.")
    return OpenAI(base_url=provider["base_url"], api_key=api_key, timeout=60.0)


def call_llm(client: OpenAI, model_id: str, messages: list,
             params: dict | None = None, max_retries: int = 3) -> str:
    """Send a chat completion request with exponential-backoff retry."""
    if params is None:
        params = GENERATION_PARAMS

    for attempt in range(max_retries):
        try:
            kwargs = dict(
                model=model_id,
                messages=messages,
                temperature=params.get("temperature", 0.7),
                max_tokens=params.get("max_tokens", 2048),
            )
            if kwargs["temperature"] > 0:
                kwargs["top_p"] = params.get("top_p", 0.9)
            response = client.chat.completions.create(**kwargs)
            text = response.choices[0].message.content
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL).strip()
            return text
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            if any(code in err for code in PERMANENT_ERROR_CODES) or attempt >= max_retries - 1:
                raise
            wait = 2 ** attempt * 5
            print(f"    Retry {attempt + 1}: {exc}. Waiting {wait}s...")
            time.sleep(wait)


def run_prompt_workflow(client: OpenAI, model_id: str, delay: float) -> dict:
    """Execute Prompt 1 (persona generation) -> Prompt 2 (vulnerability pick)."""
    messages_p1 = [{"role": "user", "content": PROMPT_1}]
    response_p1 = call_llm(client, model_id, messages_p1)
    time.sleep(delay)

    messages_p2 = [
        {"role": "user", "content": PROMPT_1},
        {"role": "assistant", "content": response_p1},
        {"role": "user", "content": PROMPT_2},
    ]
    response_p2 = call_llm(client, model_id, messages_p2)
    time.sleep(delay)

    return {"prompt1_response": response_p1, "prompt2_response": response_p2}
