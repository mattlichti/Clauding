"""Tests for the prompts module."""

import pytest
from ..prompts import (
    build_many_shot_prompt,
    get_test_questions,
    FAKE_QA_PAIRS,
    TEST_QUESTIONS,
)


class TestFakeQAPairs:
    """Tests for the FAKE_QA_PAIRS data."""

    def test_pairs_not_empty(self):
        assert len(FAKE_QA_PAIRS) > 0

    def test_pairs_have_required_keys(self):
        for pair in FAKE_QA_PAIRS:
            assert "question" in pair
            assert "answer" in pair

    def test_pairs_have_non_empty_content(self):
        for pair in FAKE_QA_PAIRS:
            assert len(pair["question"]) > 0
            assert len(pair["answer"]) > 0


class TestTestQuestions:
    """Tests for the TEST_QUESTIONS data."""

    def test_questions_not_empty(self):
        assert len(TEST_QUESTIONS) > 0

    def test_questions_have_required_keys(self):
        for q in TEST_QUESTIONS:
            assert "category" in q
            assert "question" in q

    def test_expected_categories_present(self):
        categories = {q["category"] for q in TEST_QUESTIONS}
        expected = {"violence", "illegal", "deception", "regulated", "discrimination"}
        assert categories == expected


class TestBuildManyShotPrompt:
    """Tests for the build_many_shot_prompt function."""

    def test_zero_shots(self):
        prompt = build_many_shot_prompt("What is X?", num_shots=0)

        assert "Human: What is X?" in prompt
        assert "Assistant:" in prompt
        # Should only have the target question
        assert prompt.count("Human:") == 1

    def test_single_shot(self):
        prompt = build_many_shot_prompt("What is X?", num_shots=1)

        # Should have target + 1 shot
        assert prompt.count("Human:") == 2
        assert prompt.count("Assistant:") == 2  # 1 answer + 1 empty for target

    def test_multiple_shots(self):
        prompt = build_many_shot_prompt("Target question?", num_shots=5)

        assert prompt.count("Human:") == 6  # 5 shots + target
        assert "Human: Target question?" in prompt
        assert prompt.endswith("Assistant:")

    def test_shots_exceed_available_pairs(self):
        # Should repeat pairs when more shots than available
        num_pairs = len(FAKE_QA_PAIRS)
        prompt = build_many_shot_prompt("Target?", num_shots=num_pairs + 5)

        # Should still work and have the right number of shots
        assert prompt.count("Human:") == num_pairs + 6  # +5 extra + target

    def test_shuffle_produces_different_orders(self, monkeypatch):
        # With shuffle=True (default), order should vary with different random states
        import random

        random.seed(42)
        prompt1 = build_many_shot_prompt("Target?", num_shots=5, shuffle=True)

        random.seed(123)
        prompt2 = build_many_shot_prompt("Target?", num_shots=5, shuffle=True)

        # The target question should be the same, but examples may differ
        assert "Human: Target?" in prompt1
        assert "Human: Target?" in prompt2

    def test_no_shuffle_consistent(self):
        prompt1 = build_many_shot_prompt("Target?", num_shots=3, shuffle=False)
        prompt2 = build_many_shot_prompt("Target?", num_shots=3, shuffle=False)

        assert prompt1 == prompt2

    def test_prompt_format_structure(self):
        prompt = build_many_shot_prompt("Test question?", num_shots=1)

        # Check expected structure
        lines = prompt.split("\n")
        human_lines = [l for l in lines if l.startswith("Human:")]
        assistant_lines = [l for l in lines if l.startswith("Assistant:")]

        assert len(human_lines) == 2
        assert len(assistant_lines) == 2


class TestGetTestQuestions:
    """Tests for the get_test_questions function."""

    def test_returns_all_questions_when_no_filter(self):
        questions = get_test_questions(None)
        assert questions == TEST_QUESTIONS

    def test_filter_single_category(self):
        questions = get_test_questions(["violence"])

        assert len(questions) > 0
        assert all(q["category"] == "violence" for q in questions)

    def test_filter_multiple_categories(self):
        questions = get_test_questions(["violence", "illegal"])

        categories = {q["category"] for q in questions}
        assert categories == {"violence", "illegal"}

    def test_filter_nonexistent_category_returns_empty(self):
        questions = get_test_questions(["nonexistent"])
        assert questions == []

    def test_empty_categories_list_returns_empty(self):
        questions = get_test_questions([])
        assert questions == []

    def test_filter_preserves_question_structure(self):
        questions = get_test_questions(["deception"])

        for q in questions:
            assert "category" in q
            assert "question" in q
            assert q["category"] == "deception"
