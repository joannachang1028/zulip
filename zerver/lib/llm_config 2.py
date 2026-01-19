"""
LLM configuration for Message Recap feature (Groq-only).
Loads .env locally and returns provider + model.
"""

import os
from typing import Dict

from dotenv import load_dotenv

DEFAULT_MODEL = "groq/llama-3.3-70b-versatile"


def load_llm_config() -> Dict[str, str]:
    # Load .env from project root (idempotent; safe to call multiple times)
    load_dotenv()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Add it to your .env file.")

    model = os.environ.get("LITELLM_MODEL", DEFAULT_MODEL)

    return {
        "provider": "groq",
        "model": model,
    }