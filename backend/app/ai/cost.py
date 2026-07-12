PRICING = {
    "groq": {
        "llama-3.1-8b-instant": {
            "input_per_1k": 0.05 / 1000,
            "output_per_1k": 0.08 / 1000,
        },
        "llama-3.3-70b-versatile": {
            "input_per_1k": 0.59 / 1000,
            "output_per_1k": 0.79 / 1000,
        },
    },
}


def estimate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    feature: str = "unknown",
) -> float:
    """Estimate cost in USD from public provider pricing. Returns 0.0 if unknown."""
    provider_pricing = PRICING.get(provider, {})
    model_pricing = provider_pricing.get(model)

    if not model_pricing:
        return 0.0

    input_cost = input_tokens * model_pricing["input_per_1k"]
    output_cost = output_tokens * model_pricing["output_per_1k"]
    return input_cost + output_cost
