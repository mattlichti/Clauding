"""
Experiment runner for many-shot jailbreaking evaluations.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import BaseModel, get_model
from .prompts import build_many_shot_prompt, get_test_questions
from .judge import judge_response
from . import database as db


def run_single_experiment(
    model: BaseModel,
    question: str,
    num_shots: int,
) -> dict:
    """
    Run a single experiment with one question and shot count.

    Args:
        model: The model to test
        question: The target question
        num_shots: Number of fake Q&A shots

    Returns:
        Dictionary with experiment results
    """
    prompt = build_many_shot_prompt(question, num_shots)

    try:
        response = model.generate(prompt)
        judgment = judge_response(response, question)
        error = None
    except Exception as e:
        response = ""
        judgment = {"is_jailbreak": False, "is_refusal": True}
        error = str(e)

    return {
        "model": model.name,
        "question": question,
        "num_shots": num_shots,
        "response": response,
        "judgment": judgment,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }


def run_experiment_sweep(
    model: BaseModel,
    shot_counts: list[int] = [0, 4, 8, 16, 32, 64, 128],
    categories: list[str] | None = None,
    verbose: bool = True,
    save_to_db: bool = True,
    experiment_id: Optional[int] = None,
) -> tuple[list[dict], Optional[int]]:
    """
    Run experiments across multiple shot counts and questions.

    Args:
        model: The model to test
        shot_counts: List of shot counts to test
        categories: Question categories to include (None for all)
        verbose: Whether to print progress
        save_to_db: Whether to save results to database
        experiment_id: Existing experiment ID to add results to

    Returns:
        Tuple of (results list, experiment_id)
    """
    questions = get_test_questions(categories)
    results = []

    # Create experiment in database if saving
    if save_to_db and experiment_id is None:
        provider, model_id = model.name.split(":", 1)
        experiment_id = db.create_experiment(
            provider=provider,
            model_id=model_id,
            shot_counts=shot_counts,
            categories=categories or ["all"]
        )

    total = len(shot_counts) * len(questions)
    current = 0

    for num_shots in shot_counts:
        for q in questions:
            current += 1
            if verbose:
                print(f"[{current}/{total}] {model.name} | shots={num_shots} | {q['category']}")

            result = run_single_experiment(model, q["question"], num_shots)
            result["category"] = q["category"]
            results.append(result)

            # Save to database
            if save_to_db and experiment_id:
                db.save_result(
                    experiment_id=experiment_id,
                    question=q["question"],
                    category=q["category"],
                    num_shots=num_shots,
                    response=result["response"],
                    is_jailbreak=result["judgment"]["is_jailbreak"],
                    is_refusal=result["judgment"]["is_refusal"],
                    response_length=result["judgment"].get("response_length", 0),
                    error=result["error"]
                )

            if verbose and result["error"]:
                print(f"  ERROR: {result['error']}")
            elif verbose:
                status = "JAILBREAK" if result["judgment"]["is_jailbreak"] else "REFUSED"
                print(f"  {status}")

    # Update experiment stats
    if save_to_db and experiment_id:
        db.update_experiment_stats(experiment_id)

    return results, experiment_id


def compute_stats(results: list[dict]) -> dict:
    """
    Compute summary statistics from experiment results.

    Args:
        results: List of experiment results

    Returns:
        Dictionary with summary statistics
    """
    stats = {
        "total": len(results),
        "by_shots": {},
        "by_category": {},
        "by_model": {},
    }

    # Group by shot count
    for result in results:
        shots = result["num_shots"]
        if shots not in stats["by_shots"]:
            stats["by_shots"][shots] = {"total": 0, "jailbreaks": 0}
        stats["by_shots"][shots]["total"] += 1
        if result["judgment"]["is_jailbreak"]:
            stats["by_shots"][shots]["jailbreaks"] += 1

    # Compute rates
    for shots, data in stats["by_shots"].items():
        data["rate"] = data["jailbreaks"] / data["total"] if data["total"] > 0 else 0

    # Group by category
    for result in results:
        cat = result.get("category", "unknown")
        if cat not in stats["by_category"]:
            stats["by_category"][cat] = {"total": 0, "jailbreaks": 0}
        stats["by_category"][cat]["total"] += 1
        if result["judgment"]["is_jailbreak"]:
            stats["by_category"][cat]["jailbreaks"] += 1

    for cat, data in stats["by_category"].items():
        data["rate"] = data["jailbreaks"] / data["total"] if data["total"] > 0 else 0

    return stats


def save_results(results: list[dict], stats: dict, output_dir: str = "evals/results"):
    """
    Save experiment results and stats to files.

    Args:
        results: List of experiment results
        stats: Summary statistics
        output_dir: Directory to save results
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save raw results
    results_file = Path(output_dir) / f"results_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Save stats
    stats_file = Path(output_dir) / f"stats_{timestamp}.json"
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\nResults saved to: {results_file}")
    print(f"Stats saved to: {stats_file}")

    return results_file, stats_file
