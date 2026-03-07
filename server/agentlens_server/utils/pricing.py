"""Model pricing table and cost calculation utilities. Prices in USD per 1M tokens."""

MODEL_PRICING: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "o3-mini": {"input": 1.10, "output": 4.40},

    # Anthropic
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},

    # Google
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},

    # Meta (via API providers)
    "llama-3.1-70b": {"input": 0.35, "output": 0.40},
    "llama-3.1-8b": {"input": 0.05, "output": 0.08},

    # Mistral
    "mistral-large": {"input": 2.00, "output": 6.00},
    "mistral-small": {"input": 0.20, "output": 0.60},
}

# Cheaper alternatives map for cost optimization suggestions
CHEAPER_ALTERNATIVES: dict[str, str] = {
    "gpt-4o": "gpt-4o-mini",
    "gpt-4": "gpt-4o",
    "gpt-4-turbo": "gpt-4o",
    "claude-opus-4-6": "claude-sonnet-4-6",
    "claude-sonnet-4-6": "claude-haiku-4-5-20251001",
    "o1": "o3-mini",
    "gemini-1.5-pro": "gemini-1.5-flash",
    "mistral-large": "mistral-small",
}


def calculate_cost(model: str, tokens_input: int, tokens_output: int) -> float:
    """Calculate cost in USD for a given model and token counts. Returns 0.0 for unknown models."""
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        # Try fuzzy match — e.g., "gpt-4o-2024-08-06" should match "gpt-4o"
        for key in MODEL_PRICING:
            if key in model or model.startswith(key):
                pricing = MODEL_PRICING[key]
                break
    if not pricing:
        return 0.0
    return (tokens_input * pricing["input"] / 1_000_000) + (tokens_output * pricing["output"] / 1_000_000)


def get_cheaper_alternative(model: str) -> str:
    """Return the name of a cheaper alternative model, or the same model if none known."""
    return CHEAPER_ALTERNATIVES.get(model, model)


def estimate_savings(model: str, tokens_input: int, tokens_output: int) -> float:
    """Estimate USD savings if the cheaper alternative model were used instead."""
    current = calculate_cost(model, tokens_input, tokens_output)
    alt = get_cheaper_alternative(model)
    if alt == model:
        return 0.0
    alternative_cost = calculate_cost(alt, tokens_input, tokens_output)
    return max(0.0, current - alternative_cost)


def estimate_savings_pct(model: str, tokens_input: int, tokens_output: int) -> int:
    """Return approximate savings percentage as integer (0-99)."""
    current = calculate_cost(model, tokens_input, tokens_output)
    if current == 0:
        return 0
    savings = estimate_savings(model, tokens_input, tokens_output)
    return int((savings / current) * 100)
