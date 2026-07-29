"""Precision/recall evaluation for Ex3."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from matching import MATCH_MODES, match_findings


def compute_rates(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def category_breakdown(
    planted_bugs: list[dict[str, Any]],
    matches: list[dict[str, Any]],
    false_positives: list[dict[str, Any]],
) -> dict[str, dict[str, float | int]]:
    planted_by_cat: dict[str, int] = defaultdict(int)
    tp_by_cat: dict[str, int] = defaultdict(int)
    fp_by_cat: dict[str, int] = defaultdict(int)

    for bug in planted_bugs:
        planted_by_cat[bug["category"]] += 1
    for match in matches:
        tp_by_cat[match["category"]] += 1
    for finding in false_positives:
        fp_by_cat[finding["category"]] += 1

    categories = sorted(set(planted_by_cat) | set(fp_by_cat) | set(tp_by_cat))
    out: dict[str, dict[str, float | int]] = {}
    for category in categories:
        tp = tp_by_cat[category]
        fp = fp_by_cat[category]
        planted = planted_by_cat[category]
        fn = max(0, planted - tp)
        rates = compute_rates(tp, fp, fn)
        out[category] = {
            "planted": planted,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            **rates,
        }
    return out


def evaluate_trial(
    planted_bugs: list[dict[str, Any]],
    review_findings: list[dict[str, Any]],
    *,
    match_mode: str = "deterministic",
    threshold: float = 0.55,
    embed_threshold: float = 0.72,
    judge_threshold: float = 0.5,
    embed_model: str = "nomic-embed-text",
    judge_model: str = "llama3.1",
    base_url: str = "http://localhost:11434",
    timeout: int = 180,
    allow_llm: bool = True,
) -> dict[str, Any]:
    matching = match_findings(
        planted_bugs,
        review_findings,
        match_mode=match_mode,
        threshold=threshold,
        embed_threshold=embed_threshold,
        judge_threshold=judge_threshold,
        embed_model=embed_model,
        judge_model=judge_model,
        base_url=base_url,
        timeout=timeout,
        allow_llm=allow_llm,
    )
    rates = compute_rates(matching["tp"], matching["fp"], matching["fn"])
    by_category = category_breakdown(
        planted_bugs,
        matching["matches"],
        matching["false_positives"],
    )
    return {
        **matching,
        **rates,
        "planted_count": len(planted_bugs),
        "finding_count": len(review_findings),
        "by_category": by_category,
    }


def aggregate_trials(trial_metrics: list[dict[str, Any]]) -> dict[str, Any]:
    if not trial_metrics:
        return {
            "trials": 0,
            "precision_mean": 0.0,
            "recall_mean": 0.0,
            "f1_mean": 0.0,
            "precision_std": 0.0,
            "recall_std": 0.0,
            "f1_std": 0.0,
            "totals": {"tp": 0, "fp": 0, "fn": 0, "planted": 0, "findings": 0},
        }

    def mean(values: list[float]) -> float:
        return sum(values) / len(values)

    def std(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        m = mean(values)
        return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5

    precision = [float(t["precision"]) for t in trial_metrics]
    recall = [float(t["recall"]) for t in trial_metrics]
    f1 = [float(t["f1"]) for t in trial_metrics]

    totals = {
        "tp": sum(int(t["tp"]) for t in trial_metrics),
        "fp": sum(int(t["fp"]) for t in trial_metrics),
        "fn": sum(int(t["fn"]) for t in trial_metrics),
        "planted": sum(int(t["planted_count"]) for t in trial_metrics),
        "findings": sum(int(t["finding_count"]) for t in trial_metrics),
    }

    cat_planted: dict[str, int] = defaultdict(int)
    cat_tp: dict[str, int] = defaultdict(int)
    for trial in trial_metrics:
        for category, stats in trial.get("by_category", {}).items():
            cat_planted[category] += int(stats.get("planted", 0))
            cat_tp[category] += int(stats.get("tp", 0))
    by_category = {}
    for category in sorted(cat_planted):
        planted = cat_planted[category]
        tp = cat_tp[category]
        by_category[category] = {
            "planted": planted,
            "tp": tp,
            "recall": round((tp / planted) if planted else 0.0, 4),
        }

    return {
        "trials": len(trial_metrics),
        "precision_mean": round(mean(precision), 4),
        "recall_mean": round(mean(recall), 4),
        "f1_mean": round(mean(f1), 4),
        "precision_std": round(std(precision), 4),
        "recall_std": round(std(recall), 4),
        "f1_std": round(std(f1), 4),
        "totals": totals,
        "by_category": by_category,
        "match_mode": trial_metrics[0].get("match_mode"),
    }


__all__ = ["MATCH_MODES", "aggregate_trials", "evaluate_trial"]
