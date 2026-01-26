"""Tests for the database module."""

import pytest
import tempfile
import os
from .. import database as db


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.init_db(path)
    yield path
    os.unlink(path)


class TestInitDb:
    """Tests for database initialization."""

    def test_creates_experiments_table(self, temp_db):
        conn = db.get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiments'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_creates_results_table(self, temp_db):
        conn = db.get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_creates_indexes(self, temp_db):
        conn = db.get_connection(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

        assert "idx_results_experiment" in indexes
        assert "idx_results_shots" in indexes
        assert "idx_results_category" in indexes
        conn.close()

    def test_idempotent_init(self, temp_db):
        # Should not raise error when called multiple times
        db.init_db(temp_db)
        db.init_db(temp_db)


class TestCreateExperiment:
    """Tests for experiment creation."""

    def test_returns_experiment_id(self, temp_db):
        exp_id = db.create_experiment(
            provider="anthropic",
            model_id="claude-3",
            shot_counts=[0, 10, 20],
            categories=["violence"],
            db_path=temp_db
        )

        assert isinstance(exp_id, int)
        assert exp_id > 0

    def test_sequential_ids(self, temp_db):
        id1 = db.create_experiment("p", "m", [0], ["c"], db_path=temp_db)
        id2 = db.create_experiment("p", "m", [0], ["c"], db_path=temp_db)

        assert id2 == id1 + 1

    def test_stores_json_fields(self, temp_db):
        shot_counts = [0, 5, 10, 20]
        categories = ["violence", "illegal"]

        exp_id = db.create_experiment(
            provider="anthropic",
            model_id="claude-3",
            shot_counts=shot_counts,
            categories=categories,
            db_path=temp_db
        )

        experiments = db.get_experiments(temp_db)
        exp = experiments[0]

        assert exp["shot_counts"] == shot_counts
        assert exp["categories"] == categories


class TestSaveResult:
    """Tests for saving results."""

    def test_saves_result(self, temp_db):
        exp_id = db.create_experiment("p", "m", [10], ["c"], db_path=temp_db)

        db.save_result(
            experiment_id=exp_id,
            question="Test question?",
            category="violence",
            num_shots=10,
            response="Test response",
            is_jailbreak=True,
            is_refusal=False,
            response_length=100,
            db_path=temp_db
        )

        results = db.get_experiment_results(exp_id, temp_db)
        assert len(results) == 1
        assert results[0]["question"] == "Test question?"
        assert results[0]["is_jailbreak"] == 1  # SQLite stores bool as int

    def test_saves_error_field(self, temp_db):
        exp_id = db.create_experiment("p", "m", [10], ["c"], db_path=temp_db)

        db.save_result(
            experiment_id=exp_id,
            question="Test?",
            category="c",
            num_shots=10,
            response="",
            is_jailbreak=False,
            is_refusal=True,
            response_length=0,
            error="API timeout",
            db_path=temp_db
        )

        results = db.get_experiment_results(exp_id, temp_db)
        assert results[0]["error"] == "API timeout"


class TestUpdateExperimentStats:
    """Tests for updating experiment statistics."""

    def test_updates_totals(self, temp_db):
        exp_id = db.create_experiment("p", "m", [10], ["c"], db_path=temp_db)

        # Add some results
        for i in range(5):
            db.save_result(
                experiment_id=exp_id,
                question=f"Q{i}",
                category="c",
                num_shots=10,
                response="resp",
                is_jailbreak=(i < 2),  # 2 jailbreaks
                is_refusal=(i >= 2),
                response_length=4,
                db_path=temp_db
            )

        db.update_experiment_stats(exp_id, temp_db)

        experiments = db.get_experiments(temp_db)
        exp = experiments[0]

        assert exp["total_runs"] == 5
        assert exp["total_jailbreaks"] == 2


class TestGetStatsByShots:
    """Tests for shot count statistics."""

    def test_groups_by_shots(self, temp_db):
        exp_id = db.create_experiment("p", "m", [0, 10], ["c"], db_path=temp_db)

        # 0 shots: 0/2 jailbreaks
        db.save_result(exp_id, "Q1", "c", 0, "r", False, True, 1, db_path=temp_db)
        db.save_result(exp_id, "Q2", "c", 0, "r", False, True, 1, db_path=temp_db)

        # 10 shots: 2/2 jailbreaks
        db.save_result(exp_id, "Q1", "c", 10, "r", True, False, 1, db_path=temp_db)
        db.save_result(exp_id, "Q2", "c", 10, "r", True, False, 1, db_path=temp_db)

        stats = db.get_stats_by_shots(exp_id, temp_db)

        assert stats[0]["total"] == 2
        assert stats[0]["jailbreaks"] == 0
        assert stats[0]["rate"] == 0.0

        assert stats[10]["total"] == 2
        assert stats[10]["jailbreaks"] == 2
        assert stats[10]["rate"] == 1.0


class TestGetStatsByCategory:
    """Tests for category statistics."""

    def test_groups_by_category(self, temp_db):
        exp_id = db.create_experiment("p", "m", [10], ["a", "b"], db_path=temp_db)

        db.save_result(exp_id, "Q1", "violence", 10, "r", True, False, 1, db_path=temp_db)
        db.save_result(exp_id, "Q2", "violence", 10, "r", False, True, 1, db_path=temp_db)
        db.save_result(exp_id, "Q3", "illegal", 10, "r", True, False, 1, db_path=temp_db)

        stats = db.get_stats_by_category(exp_id, temp_db)

        assert stats["violence"]["total"] == 2
        assert stats["violence"]["jailbreaks"] == 1
        assert stats["violence"]["rate"] == 0.5

        assert stats["illegal"]["total"] == 1
        assert stats["illegal"]["jailbreaks"] == 1
        assert stats["illegal"]["rate"] == 1.0


class TestDeleteExperiment:
    """Tests for experiment deletion."""

    def test_deletes_experiment_and_results(self, temp_db):
        exp_id = db.create_experiment("p", "m", [10], ["c"], db_path=temp_db)
        db.save_result(exp_id, "Q", "c", 10, "r", True, False, 1, db_path=temp_db)

        db.delete_experiment(exp_id, temp_db)

        experiments = db.get_experiments(temp_db)
        results = db.get_experiment_results(exp_id, temp_db)

        assert len(experiments) == 0
        assert len(results) == 0

    def test_only_deletes_specified_experiment(self, temp_db):
        exp_id1 = db.create_experiment("p", "m1", [10], ["c"], db_path=temp_db)
        exp_id2 = db.create_experiment("p", "m2", [10], ["c"], db_path=temp_db)

        db.save_result(exp_id1, "Q", "c", 10, "r", True, False, 1, db_path=temp_db)
        db.save_result(exp_id2, "Q", "c", 10, "r", True, False, 1, db_path=temp_db)

        db.delete_experiment(exp_id1, temp_db)

        experiments = db.get_experiments(temp_db)
        assert len(experiments) == 1
        assert experiments[0]["model_id"] == "m2"


class TestGetComparisonData:
    """Tests for comparison data retrieval."""

    def test_compares_multiple_experiments(self, temp_db):
        exp_id1 = db.create_experiment("anthropic", "claude", [10], ["c"], db_path=temp_db)
        exp_id2 = db.create_experiment("openai", "gpt4", [10], ["c"], db_path=temp_db)

        db.save_result(exp_id1, "Q", "c", 10, "r", True, False, 1, db_path=temp_db)
        db.save_result(exp_id2, "Q", "c", 10, "r", False, True, 1, db_path=temp_db)

        data = db.get_comparison_data([exp_id1, exp_id2], temp_db)

        assert len(data) == 2

        claude_data = next(d for d in data if d["model_id"] == "claude")
        gpt_data = next(d for d in data if d["model_id"] == "gpt4")

        assert claude_data["jailbreaks"] == 1
        assert gpt_data["jailbreaks"] == 0
