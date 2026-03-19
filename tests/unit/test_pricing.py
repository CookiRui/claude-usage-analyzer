"""Tests for pricing module."""

from claude_usage_analyzer.pricing import (
    DEFAULT_PRICING,
    FALLBACK_PRICE,
    ModelPrice,
    compute_cost,
    get_model_price,
)


class TestGetModelPrice:
    def test_opus_46(self):
        p = get_model_price("claude-opus-4-6-20260101")
        assert p.input == 5.0
        assert p.output == 25.0

    def test_opus_45(self):
        p = get_model_price("claude-opus-4-5-20251101")
        assert p.input == 5.0

    def test_sonnet(self):
        p = get_model_price("claude-sonnet-4-5-20250929")
        assert p.input == 3.0
        assert p.output == 15.0

    def test_haiku(self):
        p = get_model_price("claude-haiku-4-5-20251001")
        assert p.input == 1.0
        assert p.output == 5.0

    def test_unknown_model_returns_fallback(self):
        p = get_model_price("some-unknown-model")
        assert p == FALLBACK_PRICE

    def test_custom_pricing(self):
        custom = {"my-model": ModelPrice(input=10.0, output=50.0, cache_write=12.5, cache_read=1.0)}
        p = get_model_price("my-model", custom)
        assert p.input == 10.0


class TestComputeCost:
    def test_basic(self):
        price = ModelPrice(input=5.0, output=25.0, cache_write=6.25, cache_read=0.50)
        cost = compute_cost(
            input_tokens=1_000_000,
            output_tokens=100_000,
            cache_creation_tokens=500_000,
            cache_read_tokens=10_000_000,
            price=price,
        )
        # 1M * $5/M + 0.1M * $25/M + 0.5M * $6.25/M + 10M * $0.5/M
        # = 5 + 2.5 + 3.125 + 5 = 15.625
        assert abs(cost - 15.625) < 0.001

    def test_zero_tokens(self):
        price = ModelPrice(input=5.0, output=25.0, cache_write=6.25, cache_read=0.50)
        cost = compute_cost(0, 0, 0, 0, price)
        assert cost == 0.0

    def test_haiku_cheaper(self):
        opus = get_model_price("claude-opus-4-6")
        haiku = get_model_price("claude-haiku-4-5-20251001")
        opus_cost = compute_cost(1_000_000, 100_000, 0, 0, opus)
        haiku_cost = compute_cost(1_000_000, 100_000, 0, 0, haiku)
        assert haiku_cost < opus_cost
