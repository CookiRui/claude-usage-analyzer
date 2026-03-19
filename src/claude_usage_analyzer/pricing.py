"""Built-in Claude model pricing table and cost calculation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# Prices per million tokens (USD)
# Source: https://docs.anthropic.com/en/docs/about-claude/pricing

@dataclass(frozen=True)
class ModelPrice:
    input: float         # $ per MTok
    output: float        # $ per MTok
    cache_write: float   # $ per MTok (5-min cache write = 1.25x input)
    cache_read: float    # $ per MTok (cache hit = 0.1x input)


# Model ID patterns → pricing. Order matters: first match wins.
# Keys are substrings matched against model IDs.
DEFAULT_PRICING: dict[str, ModelPrice] = {
    "claude-opus-4-6":   ModelPrice(input=5.0,  output=25.0, cache_write=6.25,  cache_read=0.50),
    "claude-opus-4-5":   ModelPrice(input=5.0,  output=25.0, cache_write=6.25,  cache_read=0.50),
    "claude-opus-4-1":   ModelPrice(input=15.0, output=75.0, cache_write=18.75, cache_read=1.50),
    "claude-opus-4-":    ModelPrice(input=15.0, output=75.0, cache_write=18.75, cache_read=1.50),
    "claude-sonnet-4":   ModelPrice(input=3.0,  output=15.0, cache_write=3.75,  cache_read=0.30),
    "claude-sonnet-3":   ModelPrice(input=3.0,  output=15.0, cache_write=3.75,  cache_read=0.30),
    "claude-haiku-4-5":  ModelPrice(input=1.0,  output=5.0,  cache_write=1.25,  cache_read=0.10),
    "claude-haiku-3-5":  ModelPrice(input=0.80, output=4.0,  cache_write=1.0,   cache_read=0.08),
    "claude-haiku-3":    ModelPrice(input=0.25, output=1.25, cache_write=0.30,  cache_read=0.03),
}

# Fallback for unknown models
FALLBACK_PRICE = ModelPrice(input=3.0, output=15.0, cache_write=3.75, cache_read=0.30)

MTOK = 1_000_000


def get_model_price(model_id: str, pricing: dict[str, ModelPrice] | None = None) -> ModelPrice:
    """Look up pricing for a model ID. Falls back to FALLBACK_PRICE for unknown models."""
    table = pricing or DEFAULT_PRICING
    for pattern, price in table.items():
        if pattern in model_id:
            return price
    return FALLBACK_PRICE


def compute_cost(
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int,
    cache_read_tokens: int,
    price: ModelPrice,
) -> float:
    """Compute cost in USD for a set of token counts."""
    return (
        input_tokens / MTOK * price.input
        + output_tokens / MTOK * price.output
        + cache_creation_tokens / MTOK * price.cache_write
        + cache_read_tokens / MTOK * price.cache_read
    )


def load_custom_pricing(path: Path) -> dict[str, ModelPrice]:
    """Load custom pricing from a JSON file.

    Expected format:
    {
        "claude-opus-4-6": {"input": 5.0, "output": 25.0, "cache_write": 6.25, "cache_read": 0.50},
        ...
    }
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {
        model: ModelPrice(
            input=p["input"],
            output=p["output"],
            cache_write=p["cache_write"],
            cache_read=p["cache_read"],
        )
        for model, p in data.items()
    }
