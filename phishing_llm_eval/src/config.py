"""
Configuration for LLM Phishing Bias Evaluation.

Multi-provider setup for evaluating bias in LLM persona generation
and phishing susceptibility assessment, following the DECODINGTRUST
framework methodology adapted for phishing contexts.

Workflow:
  Prompt 1 → LLM generates 3 diverse personas
  Prompt 2 → LLM chooses which persona is most vulnerable to phishing
  Repeat across 14 models × 22 runs = 924 persona samples
"""

# ============================================================
# API Keys
# ============================================================
API_KEYS = {
    "groq": "",        # Get from https://console.groq.com
    "mistral": "",     # Get from https://console.mistral.ai
    "google_ai": "",   # Get from https://aistudio.google.com
    "sambanova": "",   # Get from https://cloud.sambanova.ai
    "cerebras": "",    # Get from https://cloud.cerebras.ai
}

# ============================================================
# Provider & Model Configuration
# 5 providers × 2-3 models each = 14 models total
# All use OpenAI-compatible API
# ============================================================
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            {"name": "llama-3.1-8b",  "id": "llama-3.1-8b-instant"},
            {"name": "llama-3.3-70b", "id": "llama-3.3-70b-versatile"},
            {"name": "llama-4-scout", "id": "meta-llama/llama-4-scout-17b-16e-instruct"},
        ],
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "models": [
            {"name": "mistral-small", "id": "mistral-small-latest"},
            {"name": "mistral-nemo",  "id": "open-mistral-nemo"},
            {"name": "ministral-8b",  "id": "ministral-8b-latest"},
        ],
    },
    "google_ai": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
            {"name": "gemma-3-4b",  "id": "gemma-3-4b-it"},
            {"name": "gemma-3-12b", "id": "gemma-3-12b-it"},
            {"name": "gemma-3-27b", "id": "gemma-3-27b-it"},
        ],
    },
    "sambanova": {
        "base_url": "https://api.sambanova.ai/v1",
        "models": [
            {"name": "llama-3.3-70b",    "id": "Meta-Llama-3.3-70B-Instruct"},
            {"name": "deepseek-v3",       "id": "DeepSeek-V3-0324"},
            {"name": "llama-4-maverick",  "id": "Llama-4-Maverick-17B-128E-Instruct"},
        ],
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "models": [
            {"name": "llama3.1-8b",  "id": "llama3.1-8b"},
            {"name": "qwen3-235b",   "id": "qwen-3-235b-a22b-instruct-2507"},
        ],
    },
}

# ============================================================
# Generation Parameters
# ============================================================
GENERATION_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2048,
}

# ============================================================
# Experiment Configuration
# ============================================================
RUNS_PER_MODEL = 22         # Prompt 1→2 workflow runs per model
# Total: 14 models × 22 runs × 3 personas/run = 924 persona rows

# ============================================================
# Parsing Model — used to extract structured data from raw responses
# ============================================================
PARSE_PROVIDER = "mistral"
PARSE_MODEL = "mistral-small-latest"
PARSE_PARAMS = {
    "temperature": 0.0,
    "max_tokens": 2048,
}

# ============================================================
# Rate Limiting (seconds between requests)
# ============================================================
REQUEST_DELAY = {
    "groq": 4.0,            # Higher delay for parsing (uses Groq too)
    "mistral": 1.0,
    "google_ai": 4.5,
    "sambanova": 1.5,
    "cerebras": 1.0,
}
