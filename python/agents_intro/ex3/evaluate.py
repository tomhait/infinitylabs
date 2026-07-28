"""Deterministic matching + precision/recall evaluation for Ex3."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _line_overlap(a_start: int, a_end: int, b_start: int, b_end: int, slack: int = 5) -> bool:
    # Expand ranges slightly to tolerate localization noise.
    a0, a1 = a_start - slack, a_end + slack
    b0, b1 = b_start - slack, b_end + slack
    return not (a1 < b0 or b1 < a0)


def finding_similarity(planted: dict[str, Any], found: dict[str, Any]) -> float:
    """Score how likely a reviewer finding matches a planted bug."""
    score = 0.0
    if planted["category"] == found["category"]:
        score += 0.35
    if _line_overlap(
        planted["line_start"],
        planted["line_end"],
        found["line_start"],
        found["line_end"],
    ):
        score += 0.35

    planted_text = f"{planted['title']} {planted['detail']}"
    found_text = f"{found['title']} {found['detail']}"
    score += 0.30 * _jaccard(_tokenize(planted_text), _tokenize(found_text))
    return score


def match_findings(
    planted_bugs: list[dict[str, Any]],
    review_findings: list[dict[str, Any]],
    *,
    threshold: float = 0.55,
) -> dict[str, Any]:
    """Greedy one-to-one matching by descending similarity."""
    candidates: list[tuple[float, str, str]] = []
    for planted in planted_bugs:
        for found in review_findings:
            sim = finding_similarity(planted, found)
            if sim >= threshold:
                candidates.append((sim, planted["id"], found["id"]))
    candidates.sort(reverse=True, key=lambda x: x[0])

    matched_planted: set[str] = set()
    matched_found: set[str] = set()
    matches: list[dict[str, Any]] = []
    for sim, planted_id, found_id in candidates:
        if planted_id in matched_planted or found_id in matched_found:
            continue
        matched_planted.add(planted_id)
        matched_found.add(found_id)
        planted = next(b for b in planted_bugs if b["id"] == planted_id)
        found = next(f for f in review_findings if f["id"] == found_id)
        matches.append(
            {
                "planted_id": planted_id,
                "finding_id": found_id,
                "similarity": round(sim, 4),
                "planted_title": planted["title"],
                "finding_title": found["title"],
                "category": planted["category"],
            }
        )

    false_negatives = [b for b in planted_bugs if b["id"] not in matched_planted]
    false_positives = [f for f in review_findings if f["id"] not in matched_found]
    return {
        "matches": matches,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "tp": len(matches),
        "fp": len(false_positives),
        "fn": len(false_negatives),
    }


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
    threshold: float = 0.55,
) -> dict[str, Any]:
    matching = match_findings(planted_bugs, review_findings, threshold=threshold)
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
        "match_threshold": threshold,
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

    # Aggregate category recall across trials.
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
    }
