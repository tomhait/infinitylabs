"""Markdown + CLI reporting for Ex3 evaluation runs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_cli_banner(summary: dict[str, Any], *, generator_model: str, reviewer_model: str) -> str:
    totals = summary.get("totals", {})
    lines = [
        "Code-Review Eval",
        "====================",
        f"Trials: {summary.get('trials', 0)} | Generator: {generator_model} | Reviewer: {reviewer_model}",
        (
            f"Precision: {summary.get('precision_mean', 0):.2f} ± {summary.get('precision_std', 0):.2f}  |  "
            f"Recall: {summary.get('recall_mean', 0):.2f} ± {summary.get('recall_std', 0):.2f}  |  "
            f"F1: {summary.get('f1_mean', 0):.2f} ± {summary.get('f1_std', 0):.2f}"
        ),
        (
            f"Totals: TP={totals.get('tp', 0)}  FP={totals.get('fp', 0)}  FN={totals.get('fn', 0)}  "
            f"planted={totals.get('planted', 0)}  findings={totals.get('findings', 0)}"
        ),
    ]
    by_category = summary.get("by_category") or {}
    if by_category:
        ranked = sorted(by_category.items(), key=lambda kv: float(kv[1].get("recall", 0.0)))
        worst = ranked[0]
        best = ranked[-1]
        lines.append(
            f"Best category:  {best[0]} (recall {float(best[1].get('recall', 0)):.2f})"
        )
        lines.append(
            f"Worst category: {worst[0]} (recall {float(worst[1].get('recall', 0)):.2f})"
        )
    return "\n".join(lines)


def render_trial_markdown(trial: dict[str, Any]) -> str:
    metrics = trial["metrics"]
    lines = [
        f"# Trial {trial['trial_id']} Report",
        "",
        f"- Topic: `{trial.get('topic', '')}`",
        f"- Generator model: `{trial.get('generator_model', '')}`",
        f"- Reviewer model: `{trial.get('reviewer_model', '')}`",
        f"- Planted bugs (x): **{metrics['planted_count']}**",
        f"- Reviewer findings: **{metrics['finding_count']}**",
        "",
        "## Metrics",
        "",
        f"| Metric | Value |",
        f"|---|---:|",
        f"| Precision | {metrics['precision']:.4f} ({_fmt_pct(metrics['precision'])}) |",
        f"| Recall | {metrics['recall']:.4f} ({_fmt_pct(metrics['recall'])}) |",
        f"| F1 | {metrics['f1']:.4f} ({_fmt_pct(metrics['f1'])}) |",
        f"| TP | {metrics['tp']} |",
        f"| FP | {metrics['fp']} |",
        f"| FN | {metrics['fn']} |",
        "",
        "## Category breakdown",
        "",
        "| Category | Planted | TP | FP | FN | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for category, stats in sorted(metrics.get("by_category", {}).items()):
        lines.append(
            "| {cat} | {planted} | {tp} | {fp} | {fn} | {p:.2f} | {r:.2f} | {f:.2f} |".format(
                cat=category,
                planted=stats["planted"],
                tp=stats["tp"],
                fp=stats["fp"],
                fn=stats["fn"],
                p=stats["precision"],
                r=stats["recall"],
                f=stats["f1"],
            )
        )

    lines.extend(["", "## True positives (matched)", ""])
    matches = metrics.get("matches") or []
    if not matches:
        lines.append("_None_")
    else:
        for match in matches:
            lines.append(
                f"- `{match['planted_id']}` ↔ `{match['finding_id']}` "
                f"(sim={match['similarity']:.2f}): {match['planted_title']} / {match['finding_title']}"
            )

    lines.extend(["", "## False negatives (missed planted bugs)", ""])
    fns = metrics.get("false_negatives") or []
    if not fns:
        lines.append("_None_")
    else:
        for bug in fns:
            lines.append(
                f"- `{bug['id']}` [{bug['category']}] L{bug['line_start']}-{bug['line_end']}: {bug['title']}"
            )

    lines.extend(["", "## False positives (unmatched reviewer findings)", ""])
    fps = metrics.get("false_positives") or []
    if not fps:
        lines.append("_None_")
    else:
        for finding in fps:
            lines.append(
                f"- `{finding['id']}` [{finding['category']}] "
                f"L{finding['line_start']}-{finding['line_end']}: {finding['title']}"
            )

    if matches:
        sample = matches[0]
        lines.extend(
            [
                "",
                "## Sample matched finding",
                "",
                f"- Planted: **{sample['planted_title']}** (`{sample['planted_id']}`)",
                f"- Reviewer: **{sample['finding_title']}** (`{sample['finding_id']}`)",
                f"- Similarity: `{sample['similarity']:.4f}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `generated_code.py`",
            "- `ground_truth.json`",
            "- `review_findings.json`",
            "- `matches.json`",
            "",
        ]
    )
    return "\n".join(lines)


def render_summary_markdown(
    *,
    summary: dict[str, Any],
    trials: list[dict[str, Any]],
    generator_model: str,
    reviewer_model: str,
    x: int,
    prompt_version: str = "v1",
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    totals = summary.get("totals", {})
    lines = [
        "# Aggregate Review Report",
        "",
        f"Generated: `{now}`",
        "",
        "## Headline metrics",
        "",
        f"- Trials: **{summary.get('trials', 0)}**",
        f"- Bugs per trial (x): **{x}**",
        f"- Generator model: `{generator_model}`",
        f"- Reviewer model: `{reviewer_model}`",
        (
            f"- Precision: **{summary.get('precision_mean', 0):.4f} ± {summary.get('precision_std', 0):.4f}**"
        ),
        (
            f"- Recall: **{summary.get('recall_mean', 0):.4f} ± {summary.get('recall_std', 0):.4f}**"
        ),
        f"- F1: **{summary.get('f1_mean', 0):.4f} ± {summary.get('f1_std', 0):.4f}**",
        (
            f"- Totals: TP={totals.get('tp', 0)}, FP={totals.get('fp', 0)}, FN={totals.get('fn', 0)}, "
            f"planted={totals.get('planted', 0)}, findings={totals.get('findings', 0)}"
        ),
        "",
        "## Per-trial table",
        "",
        "| Trial | Topic | TP | FP | FN | Precision | Recall | F1 | Latency (s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for trial in trials:
        m = trial["metrics"]
        lines.append(
            "| {tid} | {topic} | {tp} | {fp} | {fn} | {p:.2f} | {r:.2f} | {f:.2f} | {lat:.1f} |".format(
                tid=trial["trial_id"],
                topic=(trial.get("topic") or "")[:40],
                tp=m["tp"],
                fp=m["fp"],
                fn=m["fn"],
                p=m["precision"],
                r=m["recall"],
                f=m["f1"],
                lat=float(trial.get("latency_seconds", 0.0)),
            )
        )

    lines.extend(["", "## Category recall (aggregate)", "", "| Category | Planted | TP | Recall |", "|---|---:|---:|---:|"])
    for category, stats in sorted((summary.get("by_category") or {}).items()):
        lines.append(
            f"| {category} | {stats['planted']} | {stats['tp']} | {float(stats['recall']):.2f} |"
        )

    # Collect top misses / false alarms across trials.
    all_fn: list[tuple[str, dict[str, Any]]] = []
    all_fp: list[tuple[str, dict[str, Any]]] = []
    for trial in trials:
        for bug in trial["metrics"].get("false_negatives") or []:
            all_fn.append((trial["trial_id"], bug))
        for finding in trial["metrics"].get("false_positives") or []:
            all_fp.append((trial["trial_id"], finding))

    lines.extend(["", "## Top misses (FN)", ""])
    if not all_fn:
        lines.append("_None_")
    else:
        for trial_id, bug in all_fn[:12]:
            lines.append(
                f"- `{trial_id}` / `{bug['id']}` [{bug['category']}]: {bug['title']}"
            )

    lines.extend(["", "## Top false alarms (FP)", ""])
    if not all_fp:
        lines.append("_None_")
    else:
        for trial_id, finding in all_fp[:12]:
            lines.append(
                f"- `{trial_id}` / `{finding['id']}` [{finding['category']}]: {finding['title']}"
            )

    lines.extend(
        [
            "",
            "## Config",
            "",
            f"- prompt_version: `{prompt_version}`",
            f"- match_threshold: `{trials[0]['metrics'].get('match_threshold', 0.55) if trials else 0.55}`",
            f"- output_dir: `runs/`",
            "",
        ]
    )
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "nit": 4}


def render_file_review_markdown(
    *,
    file_path: str,
    review: dict[str, Any],
    model: str,
    static_checks: list[str] | None = None,
    focus: str | None = None,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    findings = sorted(
        review.get("findings") or [],
        key=lambda f: (
            _SEVERITY_ORDER.get(str(f.get("severity", "medium")).lower(), 99),
            int(f.get("line_start", 0)),
        ),
    )
    lines = [
        "# Python Code Review",
        "",
        f"Generated: `{now}`",
        "",
        "## File",
        "",
        f"- Path: `{file_path}`",
        f"- Model: `{model}`",
    ]
    if focus:
        lines.append(f"- Focus: `{focus}`")
    lines.extend(["", "## Summary", "", review.get("summary") or "_No summary provided._", ""])

    if static_checks:
        lines.extend(["", "## Static checks", ""])
        for note in static_checks:
            lines.append(f"- {note}")

    lines.extend(
        [
            "",
            f"## Findings ({len(findings)})",
            "",
            "| ID | Severity | Category | Lines | Title | Confidence |",
            "|---|---|---|---:|---|---:|",
        ]
    )
    for finding in findings:
        lines.append(
            "| {id} | {sev} | {cat} | {lines} | {title} | {conf:.2f} |".format(
                id=finding["id"],
                sev=finding["severity"],
                cat=finding["category"],
                lines=f"L{finding['line_start']}-{finding['line_end']}",
                title=finding["title"].replace("|", "\\|"),
                conf=float(finding.get("confidence", 0.0)),
            )
        )

    if not findings:
        lines.extend(["", "_No findings reported._", ""])
    else:
        lines.extend(["", "## Finding details", ""])
        for finding in findings:
            lines.extend(
                [
                    f"### {finding['id']} — {finding['title']}",
                    "",
                    f"- **Severity:** {finding['severity']}",
                    f"- **Category:** {finding['category']}",
                    f"- **Lines:** {finding['line_start']}-{finding['line_end']}",
                    f"- **Confidence:** {float(finding.get('confidence', 0.0)):.2f}",
                    "",
                    finding["detail"],
                    "",
                ]
            )

    lines.extend(["", "## Artifacts", "", "- `review_findings.json`", "- `review_report.md`", ""])
    return "\n".join(lines)


def render_file_review_cli_summary(file_path: str, review: dict[str, Any]) -> str:
    findings = review.get("findings") or []
    by_severity: dict[str, int] = {}
    for f in findings:
        sev = str(f.get("severity", "medium"))
        by_severity[sev] = by_severity.get(sev, 0) + 1
    sev_parts = ", ".join(f"{k}={v}" for k, v in sorted(by_severity.items()))
    summary = (review.get("summary") or "").strip()
    if len(summary) > 160:
        summary = summary[:157] + "..."
    return (
        f"Reviewed: {file_path}\n"
        f"Findings: {len(findings)} ({sev_parts or 'none'})\n"
        f"Summary: {summary or '(empty)'}"
    )
