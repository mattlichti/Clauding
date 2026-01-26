"""Tests for the runner module."""

import pytest
from ..runner import compute_stats


class TestComputeStats:
    """Tests for the compute_stats function."""

    def test_empty_results(self):
        stats = compute_stats([])

        assert stats["total"] == 0
        assert stats["by_shots"] == {}
        assert stats["by_category"] == {}
        assert stats["by_model"] == {}

    def test_single_result_jailbreak(self):
        results = [{
            "num_shots": 10,
            "category": "violence",
            "model": "test",
            "judgment": {"is_jailbreak": True}
        }]

        stats = compute_stats(results)

        assert stats["total"] == 1
        assert stats["by_shots"][10]["total"] == 1
        assert stats["by_shots"][10]["jailbreaks"] == 1
        assert stats["by_shots"][10]["rate"] == 1.0

    def test_single_result_refusal(self):
        results = [{
            "num_shots": 10,
            "category": "violence",
            "model": "test",
            "judgment": {"is_jailbreak": False}
        }]

        stats = compute_stats(results)

        assert stats["by_shots"][10]["jailbreaks"] == 0
        assert stats["by_shots"][10]["rate"] == 0.0

    def test_multiple_shot_counts(self):
        results = [
            {"num_shots": 0, "category": "a", "model": "m", "judgment": {"is_jailbreak": False}},
            {"num_shots": 0, "category": "a", "model": "m", "judgment": {"is_jailbreak": False}},
            {"num_shots": 10, "category": "a", "model": "m", "judgment": {"is_jailbreak": True}},
            {"num_shots": 10, "category": "a", "model": "m", "judgment": {"is_jailbreak": False}},
            {"num_shots": 50, "category": "a", "model": "m", "judgment": {"is_jailbreak": True}},
            {"num_shots": 50, "category": "a", "model": "m", "judgment": {"is_jailbreak": True}},
        ]

        stats = compute_stats(results)

        assert stats["by_shots"][0]["rate"] == 0.0
        assert stats["by_shots"][10]["rate"] == 0.5
        assert stats["by_shots"][50]["rate"] == 1.0

    def test_multiple_categories(self):
        results = [
            {"num_shots": 10, "category": "violence", "model": "m", "judgment": {"is_jailbreak": True}},
            {"num_shots": 10, "category": "violence", "model": "m", "judgment": {"is_jailbreak": True}},
            {"num_shots": 10, "category": "illegal", "model": "m", "judgment": {"is_jailbreak": False}},
            {"num_shots": 10, "category": "illegal", "model": "m", "judgment": {"is_jailbreak": True}},
        ]

        stats = compute_stats(results)

        assert stats["by_category"]["violence"]["total"] == 2
        assert stats["by_category"]["violence"]["jailbreaks"] == 2
        assert stats["by_category"]["violence"]["rate"] == 1.0

        assert stats["by_category"]["illegal"]["total"] == 2
        assert stats["by_category"]["illegal"]["jailbreaks"] == 1
        assert stats["by_category"]["illegal"]["rate"] == 0.5

    def test_missing_category_treated_as_unknown(self):
        results = [
            {"num_shots": 10, "model": "m", "judgment": {"is_jailbreak": True}},
        ]

        stats = compute_stats(results)

        assert "unknown" in stats["by_category"]
        assert stats["by_category"]["unknown"]["total"] == 1

    def test_rate_calculation_precision(self):
        # Test with numbers that produce a repeating decimal
        results = [
            {"num_shots": 5, "category": "a", "model": "m", "judgment": {"is_jailbreak": True}},
            {"num_shots": 5, "category": "a", "model": "m", "judgment": {"is_jailbreak": False}},
            {"num_shots": 5, "category": "a", "model": "m", "judgment": {"is_jailbreak": False}},
        ]

        stats = compute_stats(results)

        # 1/3 = 0.333...
        assert abs(stats["by_shots"][5]["rate"] - (1/3)) < 0.0001

    def test_total_count_accuracy(self):
        results = [{"num_shots": i, "category": "a", "model": "m", "judgment": {"is_jailbreak": False}}
                   for i in range(100)]

        stats = compute_stats(results)

        assert stats["total"] == 100
