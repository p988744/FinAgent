"""Cost calculation utilities for LLM usage."""

# Token pricing per 1M tokens (as of 2025-01)
# Update these values as model pricing changes
MODEL_PRICING = {
    # OpenAI models
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Custom/Local models - estimated cost (usually free, but tracking compute cost)
    "ollama/gpt-oss:20b": {"input": 0.0, "output": 0.0},  # Free local model
    "qwen2.5:7b": {"input": 0.0, "output": 0.0},  # Free local model
    "llama3.1:8b": {"input": 0.0, "output": 0.0},  # Free local model
    "mistral:7b": {"input": 0.0, "output": 0.0},  # Free local model
}

# Default pricing for unknown models (conservative estimate)
DEFAULT_PRICING = {"input": 1.00, "output": 2.00}


def calculate_token_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> float:
    """
    Calculate the cost of LLM usage based on tokens and model.

    Args:
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        model: Model name (e.g., "gpt-4o-mini", "ollama/gpt-oss:20b")

    Returns:
        Cost in USD

    Examples:
        >>> calculate_token_cost(1000, 500, "gpt-4o-mini")
        0.00045  # (1000 * 0.15 + 500 * 0.60) / 1,000,000
        >>> calculate_token_cost(1000, 500, "ollama/gpt-oss:20b")
        0.0  # Free local model
    """
    # Normalize model name (remove version suffixes if present)
    normalized_model = normalize_model_name(model)

    # Get pricing for model
    pricing = MODEL_PRICING.get(normalized_model, DEFAULT_PRICING)

    # Calculate cost (pricing is per 1M tokens)
    input_cost = (input_tokens * pricing["input"]) / 1_000_000
    output_cost = (output_tokens * pricing["output"]) / 1_000_000

    return input_cost + output_cost


def calculate_total_cost(
    total_tokens: int,
    model: str,
    input_output_ratio: float = 0.6,
) -> float:
    """
    Calculate cost when only total tokens are known.

    Assumes a typical input/output ratio (default 60% input, 40% output).

    Args:
        total_tokens: Total tokens used
        model: Model name
        input_output_ratio: Ratio of input tokens to total (0.0-1.0)

    Returns:
        Estimated cost in USD

    Examples:
        >>> calculate_total_cost(1500, "gpt-4o-mini")
        0.000405  # Estimated with 60/40 split
    """
    input_tokens = int(total_tokens * input_output_ratio)
    output_tokens = total_tokens - input_tokens

    return calculate_token_cost(input_tokens, output_tokens, model)


def normalize_model_name(model: str) -> str:
    """
    Normalize model name by removing version suffixes and standardizing format.

    Args:
        model: Original model name

    Returns:
        Normalized model name

    Examples:
        >>> normalize_model_name("gpt-4o-2024-08-06")
        'gpt-4o'
        >>> normalize_model_name("gpt-4o-mini-2024-07-18")
        'gpt-4o-mini'
        >>> normalize_model_name("ollama/gpt-oss:20b")
        'ollama/gpt-oss:20b'
    """
    import re

    # If already in our pricing dict, return as-is
    if model in MODEL_PRICING:
        return model

    # Remove date suffixes (YYYY-MM-DD, YYYY-MM, or YYYYMMDD)
    model = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model)  # Remove -YYYY-MM-DD
    model = re.sub(r"-\d{4}-\d{2}$", "", model)  # Remove -YYYY-MM
    model = re.sub(r"-\d{8}$", "", model)  # Remove -YYYYMMDD
    model = re.sub(r"-\d{4}$", "", model)  # Remove -YYYY

    return model


def format_cost_usd(cost_usd: float) -> str:
    """
    Format cost in USD with appropriate precision.

    Args:
        cost_usd: Cost in USD

    Returns:
        Formatted cost string

    Examples:
        >>> format_cost_usd(0.00045)
        '$0.00045'
        >>> format_cost_usd(1.234)
        '$1.23'
        >>> format_cost_usd(0.0)
        '$0.00'
    """
    if cost_usd < 0.01:
        # Show more decimal places for small amounts
        return f"${cost_usd:.5f}"
    else:
        return f"${cost_usd:.2f}"


def format_cost_twd(cost_usd: float, exchange_rate: float = 31.5) -> str:
    """
    Format cost in TWD (Taiwan Dollar).

    Args:
        cost_usd: Cost in USD
        exchange_rate: USD to TWD exchange rate (default: ~31.5)

    Returns:
        Formatted cost string in TWD

    Examples:
        >>> format_cost_twd(0.05)
        'NT$1.58'
        >>> format_cost_twd(1.0)
        'NT$31.50'
    """
    cost_twd = cost_usd * exchange_rate
    return f"NT${cost_twd:.2f}"


def estimate_query_cost(
    model: str,
    avg_tokens_per_query: int = 1500,
) -> dict[str, str]:
    """
    Estimate cost for a single query with typical token usage.

    Args:
        model: Model name
        avg_tokens_per_query: Average tokens per query (default: 1500)

    Returns:
        Dictionary with cost information

    Examples:
        >>> estimate_query_cost("gpt-4o-mini", 1500)
        {'usd': '$0.00045', 'twd': 'NT$0.01', 'tokens': 1500}
    """
    cost_usd = calculate_total_cost(avg_tokens_per_query, model)

    return {
        "usd": format_cost_usd(cost_usd),
        "twd": format_cost_twd(cost_usd),
        "tokens": avg_tokens_per_query,
        "model": model,
    }
