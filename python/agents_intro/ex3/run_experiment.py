#!/usr/bin/env python3
"""Ex3 experiment runner: generate -> review -> evaluate -> report."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluate import aggregate_trials, evaluate_trial
from generator import DEFAULT_X, generate_buggy_module
from report import render_cli_banner, render_summary_markdown, render_trial_markdown, write_text
from reviewer import review_python_code


def _dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_one_trial(
    *,
    trial_id: str,
    out_dir: Path,
    generator_model: str,
    reviewer_model: str,
    base_url: str,
    timeout: int,
    topic_hint: str | None,
    match_threshold: float,
) -> dict[str, Any]:
    trial_dir = out_dir / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    generated = generate_buggy_module(
        model=generator_model,
        base_url=base_url,
        timeout=timeout,
        expected_x=DEFAULT_X,
        topic_hint=topic_hint,
    )
    code_path = trial_dir / "generated_code.py"
    code_path.write_text(generated["code"], encoding="utf-8")
    ground_truth = {
        "topic": generated["topic"],
        "x": generated["x"],
        "bug_budget": generated["bug_budget"],
        "actual_bug_budget": generated.get("actual_bug_budget"),
        "budget_warning": generated.get("budget_warning"),
        "bugs": generated["bugs"],
    }
    _dump_json(trial_dir / "ground_truth.json", ground_truth)
    if generated.get("budget_warning"):
        print(f"  Warning: {generated['budget_warning']}")

    review = review_python_code(
        generated["code"],
        model=reviewer_model,
        base_url=base_url,
        timeout=timeout,
    )
    _dump_json(trial_dir / "review_findings.json", review)

    metrics = evaluate_trial(
        generated["bugs"],
        review["findings"],
        threshold=match_threshold,
    )
    _dump_json(
        trial_dir / "matches.json",
        {
            "matches": metrics["matches"],
            "false_negatives": metrics["false_negatives"],
            "false_positives": metrics["false_positives"],
            "tp": metrics["tp"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "match_threshold": match_threshold,
        },
    )

    latency = time.perf_counter() - started
    trial = {
        "trial_id": trial_id,
        "topic": generated["topic"],
        "generator_model": generator_model,
        "reviewer_model": reviewer_model,
        "latency_seconds": round(latency, 3),
        "metrics": metrics,
        "artifact_dir": str(trial_dir),
    }
    write_text(trial_dir / "trial_report.md", render_trial_markdown(trial))
    _dump_json(trial_dir / "trial_metrics.json", trial)
    return trial


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="two-agent Python code-review evaluation with reporting."
    )
    parser.add_argument("--trials", type=int, default=5, help="Number of independent trials.")
    parser.add_argument(
        "--generator-model",
        type=str,
        default="llama3",
        help="Ollama model for generator agent.",
    )
    parser.add_argument(
        "--reviewer-model",
        type=str,
        default="llama3.1",
        help="Ollama model for reviewer agent.",
    )
    parser.add_argument("--base-url", type=str, default="http://localhost:11434")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.55,
        help="Similarity threshold for TP matching.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="Output directory (default: runs/<timestamp>).",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="",
        help="Optional topic hint for generation.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run offline demo with synthetic planted/review data (no LLM calls).",
    )
    return parser


def run_demo(out_dir: Path, match_threshold: float) -> list[dict[str, Any]]:
    """Offline path to validate evaluation + reporting without Ollama."""
    trials: list[dict[str, Any]] = []
    planted = [
        {
            "id": f"B{i}",
            "category": cat,
            "line_start": i * 3,
            "line_end": i * 3 + 1,
            "title": title,
            "detail": detail,
        }
        for i, (cat, title, detail) in enumerate(
            [
                ("logic", "Off-by-one in loop", "Loop uses <= and overruns list"),
                ("logic", "Wrong comparison", "Uses is instead of =="),
                ("logic", "Mutable default", "Uses list default argument"),
                ("logic", "Shadowed variable", "Inner var overwrites outer total"),
                ("edge_case", "None not handled", "Assumes dict always present"),
                ("edge_case", "Empty input crash", "No guard for empty list"),
                ("security", "Command injection", "os.system with user input"),
                ("security", "Hardcoded secret", "API key embedded in source"),
                ("performance", "Nested loop", "O(n^2) membership checks"),
                ("performance", "Repeated work", "Recomputes sum every iteration"),
                ("api_design", "Leaky abstraction", "Returns internal mutable list"),
                ("maintainability", "Cryptic names", "Uses a1/b2 for domain concepts"),
            ],
            start=1,
        )
    ]
    # Reviewer finds 9 correctly, misses 3, adds 2 false alarms.
    findings = []
    for bug in planted[:9]:
        findings.append(
            {
                "id": f"F-{bug['id']}",
                "category": bug["category"],
                "line_start": bug["line_start"],
                "line_end": bug["line_end"],
                "title": bug["title"],
                "detail": bug["detail"],
                "severity": "high",
                "confidence": 0.9,
            }
        )
    findings.extend(
        [
            {
                "id": "F-FP1",
                "category": "maintainability",
                "line_start": 2,
                "line_end": 2,
                "title": "Missing docstring",
                "detail": "Function has no docstring",
                "severity": "nit",
                "confidence": 0.4,
            },
            {
                "id": "F-FP2",
                "category": "logic",
                "line_start": 80,
                "line_end": 82,
                "title": "Imagined race condition",
                "detail": "Claims thread hazard in single-threaded code",
                "severity": "medium",
                "confidence": 0.3,
            },
        ]
    )

    code = "\n".join(f"x = {i}" for i in range(1, 90)) + "\n"
    for idx in range(1, 3):
        trial_id = f"trial_{idx:02d}"
        trial_dir = out_dir / trial_id
        trial_dir.mkdir(parents=True, exist_ok=True)
        (trial_dir / "generated_code.py").write_text(code, encoding="utf-8")
        _dump_json(
            trial_dir / "ground_truth.json",
            {"topic": f"demo topic {idx}", "x": len(planted), "bugs": planted},
        )
        review = {"summary": "demo review", "findings": findings, "finding_count": len(findings)}
        _dump_json(trial_dir / "review_findings.json", review)
        metrics = evaluate_trial(planted, findings, threshold=match_threshold)
        _dump_json(
            trial_dir / "matches.json",
            {
                "matches": metrics["matches"],
                "false_negatives": metrics["false_negatives"],
                "false_positives": metrics["false_positives"],
                "tp": metrics["tp"],
                "fp": metrics["fp"],
                "fn": metrics["fn"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
            },
        )
        trial = {
            "trial_id": trial_id,
            "topic": f"demo topic {idx}",
            "generator_model": "demo-generator",
            "reviewer_model": "demo-reviewer",
            "latency_seconds": 0.01 * idx,
            "metrics": metrics,
            "artifact_dir": str(trial_dir),
        }
        write_text(trial_dir / "trial_report.md", render_trial_markdown(trial))
        _dump_json(trial_dir / "trial_metrics.json", trial)
        trials.append(trial)
    return trials


def main() -> None:
    args = build_parser().parse_args()
    if args.trials < 1:
        print("Agent error: --trials must be >= 1")
        raise SystemExit(2)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir) if args.output_dir else Path("runs") / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    topic_hint = args.topic.strip() or None
    trials: list[dict[str, Any]] = []

    if args.demo:
        trials = run_demo(out_dir, match_threshold=args.match_threshold)
        generator_model = "demo-generator"
        reviewer_model = "demo-reviewer"
    else:
        generator_model = args.generator_model
        reviewer_model = args.reviewer_model
        for i in range(1, args.trials + 1):
            trial_id = f"trial_{i:02d}"
            print(f"Running {trial_id} ...")
            try:
                trial = run_one_trial(
                    trial_id=trial_id,
                    out_dir=out_dir,
                    generator_model=generator_model,
                    reviewer_model=reviewer_model,
                    base_url=args.base_url,
                    timeout=args.timeout,
                    topic_hint=topic_hint,
                    match_threshold=args.match_threshold,
                )
            except Exception as error:
                print(f"Agent error in {trial_id}: {error}")
                raise SystemExit(1) from error
            trials.append(trial)
            print(
                f"  P={trial['metrics']['precision']:.2f} "
                f"R={trial['metrics']['recall']:.2f} "
                f"F1={trial['metrics']['f1']:.2f}"
            )

    summary = aggregate_trials([t["metrics"] for t in trials])
    summary_payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generator_model": generator_model,
        "reviewer_model": reviewer_model,
        "x": DEFAULT_X,
        "match_threshold": args.match_threshold,
        "output_dir": str(out_dir),
        "summary": summary,
        "trials": [
            {
                "trial_id": t["trial_id"],
                "topic": t["topic"],
                "precision": t["metrics"]["precision"],
                "recall": t["metrics"]["recall"],
                "f1": t["metrics"]["f1"],
                "tp": t["metrics"]["tp"],
                "fp": t["metrics"]["fp"],
                "fn": t["metrics"]["fn"],
                "latency_seconds": t["latency_seconds"],
            }
            for t in trials
        ],
    }
    _dump_json(out_dir / "summary.json", summary_payload)
    write_text(
        out_dir / "summary.md",
        render_summary_markdown(
            summary=summary,
            trials=trials,
            generator_model=generator_model,
            reviewer_model=reviewer_model,
            x=DEFAULT_X,
        ),
    )

    print()
    print(render_cli_banner(summary, generator_model=generator_model, reviewer_model=reviewer_model))
    print()
    print(f"Wrote reports to: {out_dir}")
    print(f"- {out_dir / 'summary.md'}")
    print(f"- {out_dir / 'summary.json'}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
