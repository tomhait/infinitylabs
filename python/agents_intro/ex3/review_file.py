#!/usr/bin/env python3
"""Review a Python file by path using the Ex3 reviewer agent."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from report import render_file_review_cli_summary, render_file_review_markdown, write_text
from reviewer import review_python_code


def run_static_checks(path: Path) -> list[str]:
    notes: list[str] = []
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        notes.append("`py_compile`: syntax OK")
    except SyntaxError as error:
        notes.append(f"`py_compile`: syntax error at line {error.lineno}: {error.msg}")
    return notes


def review_file(
    path: Path,
    *,
    model: str,
    base_url: str,
    timeout: int,
    focus: str | None,
) -> dict[str, Any]:
    if path.suffix != ".py":
        raise ValueError("Only .py files are supported.")
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    code = path.read_text(encoding="utf-8")
    static_checks = run_static_checks(path)
    review = review_python_code(
        code,
        model=model,
        base_url=base_url,
        timeout=timeout,
        focus=focus,
    )
    return {
        "file": str(path.resolve()),
        "model": model,
        "focus": focus,
        "static_checks": static_checks,
        "review": review,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a Python file with local Ollama.")
    parser.add_argument("--file", type=str, required=True, help="Path to a .py file.")
    parser.add_argument("--model", type=str, default="llama3.1", help="Ollama reviewer model.")
    parser.add_argument("--base-url", type=str, default="http://localhost:11434")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--focus",
        type=str,
        default="",
        help="Optional focus area (e.g. security, performance).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="Output directory (default: reviews/<timestamp>).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    file_path = Path(args.file).expanduser().resolve()
    focus = args.focus.strip() or None

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir) if args.output_dir else Path("reviews") / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = review_file(
            file_path,
            model=args.model,
            base_url=args.base_url,
            timeout=args.timeout,
            focus=focus,
        )
    except Exception as error:
        print(f"Review error: {error}")
        raise SystemExit(1) from error

    review = result["review"]
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file": result["file"],
        "model": result["model"],
        "focus": result["focus"],
        "static_checks": result["static_checks"],
        "summary": review.get("summary"),
        "finding_count": review.get("finding_count"),
        "findings": review.get("findings"),
    }
    write_text(out_dir / "review_findings.json", json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
    write_text(
        out_dir / "review_report.md",
        render_file_review_markdown(
            file_path=result["file"],
            review=review,
            model=result["model"],
            static_checks=result["static_checks"],
            focus=result["focus"],
        ),
    )

    print(render_file_review_cli_summary(result["file"], review))
    print()
    print(f"Wrote: {out_dir / 'review_report.md'}")
    print(f"Wrote: {out_dir / 'review_findings.json'}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
