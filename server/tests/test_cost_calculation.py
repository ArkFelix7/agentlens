"""Tests for the cost calculation engine."""

import pytest
from agentlens_server.utils.pricing import calculate_cost, MODEL_PRICING


def test_gpt4o_cost():
    cost = calculate_cost("gpt-4o", 1_000_000, 1_000_000)
    assert abs(cost - 12.50) < 0.000001


def test_gpt4o_mini_cost():
    cost = calculate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert abs(cost - 0.75) < 0.000001


def test_claude_sonnet_cost():
    cost = calculate_cost("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert abs(cost - 18.00) < 0.000001


def test_unknown_model_returns_zero():
    cost = calculate_cost("totally-unknown-model-xyz", 1000, 1000)
    assert cost == 0.0


def test_fuzzy_match():
    """'gpt-4o-2024-08-06' should match 'gpt-4o' pricing."""
    cost = calculate_cost("gpt-4o-2024-08-06", 1_000_000, 0)
    assert cost > 0.0  # Should find a match


def test_all_models_have_valid_pricing():
    for model, pricing in MODEL_PRICING.items():
        assert pricing["input"] > 0
        assert pricing["output"] > 0
        cost = calculate_cost(model, 1000, 1000)
        assert cost >= 0
