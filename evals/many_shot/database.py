"""
SQLite database for storing experiment results.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = "evals/results.db"


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Get a database connection, creating the database if needed."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Initialize the database schema."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Experiments table - one row per experiment run
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            provider TEXT NOT NULL,
            model_id TEXT NOT NULL,
            shot_counts TEXT NOT NULL,
            categories TEXT NOT NULL,
            total_runs INTEGER,
            total_jailbreaks INTEGER,
            notes TEXT
        )
    """)

    # Results table - one row per question tested
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            question TEXT NOT NULL,
            category TEXT NOT NULL,
            num_shots INTEGER NOT NULL,
            response TEXT,
            is_jailbreak BOOLEAN NOT NULL,
            is_refusal BOOLEAN NOT NULL,
            response_length INTEGER,
            error TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    """)

    # Index for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_experiment
        ON results(experiment_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_shots
        ON results(num_shots)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_category
        ON results(category)
    """)

    conn.commit()
    conn.close()


def create_experiment(
    provider: str,
    model_id: str,
    shot_counts: list[int],
    categories: list[str],
    notes: str = "",
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Create a new experiment and return its ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO experiments (provider, model_id, shot_counts, categories, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (
        provider,
        model_id,
        json.dumps(shot_counts),
        json.dumps(categories),
        notes
    ))

    experiment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return experiment_id


def save_result(
    experiment_id: int,
    question: str,
    category: str,
    num_shots: int,
    response: str,
    is_jailbreak: bool,
    is_refusal: bool,
    response_length: int,
    error: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
):
    """Save a single result to the database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO results (
            experiment_id, question, category, num_shots,
            response, is_jailbreak, is_refusal, response_length, error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        experiment_id, question, category, num_shots,
        response, is_jailbreak, is_refusal, response_length, error
    ))

    conn.commit()
    conn.close()


def update_experiment_stats(experiment_id: int, db_path: str = DEFAULT_DB_PATH):
    """Update experiment totals after all results are saved."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE experiments
        SET total_runs = (SELECT COUNT(*) FROM results WHERE experiment_id = ?),
            total_jailbreaks = (SELECT COUNT(*) FROM results WHERE experiment_id = ? AND is_jailbreak = 1)
        WHERE id = ?
    """, (experiment_id, experiment_id, experiment_id))

    conn.commit()
    conn.close()


def get_experiments(db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Get all experiments."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM experiments ORDER BY created_at DESC
    """)

    experiments = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Parse JSON fields
    for exp in experiments:
        exp["shot_counts"] = json.loads(exp["shot_counts"])
        exp["categories"] = json.loads(exp["categories"])

    return experiments


def get_experiment_results(experiment_id: int, db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Get all results for an experiment."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM results WHERE experiment_id = ? ORDER BY num_shots, category
    """, (experiment_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


def get_stats_by_shots(experiment_id: int, db_path: str = DEFAULT_DB_PATH) -> dict:
    """Get jailbreak stats grouped by shot count."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            num_shots,
            COUNT(*) as total,
            SUM(CASE WHEN is_jailbreak THEN 1 ELSE 0 END) as jailbreaks
        FROM results
        WHERE experiment_id = ?
        GROUP BY num_shots
        ORDER BY num_shots
    """, (experiment_id,))

    stats = {}
    for row in cursor.fetchall():
        stats[row["num_shots"]] = {
            "total": row["total"],
            "jailbreaks": row["jailbreaks"],
            "rate": row["jailbreaks"] / row["total"] if row["total"] > 0 else 0
        }

    conn.close()
    return stats


def get_stats_by_category(experiment_id: int, db_path: str = DEFAULT_DB_PATH) -> dict:
    """Get jailbreak stats grouped by category."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category,
            COUNT(*) as total,
            SUM(CASE WHEN is_jailbreak THEN 1 ELSE 0 END) as jailbreaks
        FROM results
        WHERE experiment_id = ?
        GROUP BY category
        ORDER BY category
    """, (experiment_id,))

    stats = {}
    for row in cursor.fetchall():
        stats[row["category"]] = {
            "total": row["total"],
            "jailbreaks": row["jailbreaks"],
            "rate": row["jailbreaks"] / row["total"] if row["total"] > 0 else 0
        }

    conn.close()
    return stats


def get_comparison_data(experiment_ids: list[int], db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Get data for comparing multiple experiments."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(experiment_ids))
    cursor.execute(f"""
        SELECT
            e.id as experiment_id,
            e.provider,
            e.model_id,
            r.num_shots,
            COUNT(*) as total,
            SUM(CASE WHEN r.is_jailbreak THEN 1 ELSE 0 END) as jailbreaks
        FROM experiments e
        JOIN results r ON e.id = r.experiment_id
        WHERE e.id IN ({placeholders})
        GROUP BY e.id, r.num_shots
        ORDER BY e.id, r.num_shots
    """, experiment_ids)

    data = [dict(row) for row in cursor.fetchall()]
    conn.close()

    for row in data:
        row["rate"] = row["jailbreaks"] / row["total"] if row["total"] > 0 else 0

    return data


def delete_experiment(experiment_id: int, db_path: str = DEFAULT_DB_PATH):
    """Delete an experiment and its results."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM results WHERE experiment_id = ?", (experiment_id,))
    cursor.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))

    conn.commit()
    conn.close()


# Initialize database on import
init_db()
