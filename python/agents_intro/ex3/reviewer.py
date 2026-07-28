"""Reviewer agent: find defects in a Python file without knowing planted count."""

from __future__ import annotations

from typing import Any

from llm import build_llm, chat_json

REVIEWER_SYSTEM = """You are Agent B: an expert Python code reviewer.

Review the provided Python source carefully.
Find real defects: bugs, edge-case failures, security issues, performance problems,
API design flaws, and maintainability issues.

Rules:
- Return ONLY valid JSON.
- Do NOT invent issues that are not supported by the code.
- You do NOT know how many bugs were planted.
- Prefer precise line ranges (1-based).
- Use categories from:
  logic, edge_case, security, performance, api_design, maintainability
- Each finding needs: id, category, line_start, line_end, title, detail, severity, confidence
- severity: critical|high|medium|low|nit
- confidence: number from 0 to 1
"""


def _validate_review(payload: dict[str, Any], code: str) -> dict[str, Any]:
    findings = payload.get("findings")
    summary = payload.get("summary", "")
    if not isinstance(findings, list):
        raise ValueError("Reviewer JSON missing 'findings' list.")
    if not isinstance(summary, str):
        summary = ""

    max_line = max(1, len(code.splitlines()))
    required = {
        "id",
        "category",
        "line_start",
        "line_end",
        "title",
        "detail",
        "severity",
        "confidence",
    }
    allowed_categories = {
        "logic",
        "edge_case",
        "security",
        "performance",
        "api_design",
        "maintainability",
    }
    allowed_severity = {"critical", "high", "medium", "low", "nit"}
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for idx, item in enumerate(findings, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Finding #{idx} is not an object.")
        missing = required - set(item)
        if missing:
            raise ValueError(f"Finding #{idx} missing fields: {sorted(missing)}")
        finding_id = str(item["id"]).strip() or f"F{idx}"
        if finding_id in seen:
            finding_id = f"{finding_id}_{idx}"
        seen.add(finding_id)
        category = str(item["category"]).strip().lower()
        if category not in allowed_categories:
            category = "logic"
        severity = str(item["severity"]).strip().lower()
        if severity not in allowed_severity:
            severity = "medium"
        try:
            line_start = int(item["line_start"])
            line_end = int(item["line_end"])
        except (TypeError, ValueError):
            line_start, line_end = 1, 1
        line_start = min(max(1, line_start), max_line)
        line_end = min(max(line_start, line_end), max_line)
        title = str(item["title"]).strip()
        detail = str(item["detail"]).strip()
        if not title or not detail:
            continue
        try:
            confidence = float(item["confidence"])
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = min(1.0, max(0.0, confidence))
        normalized.append(
            {
                "id": finding_id,
                "category": category,
                "line_start": line_start,
                "line_end": line_end,
                "title": title,
                "detail": detail,
                "severity": severity,
                "confidence": confidence,
            }
        )

    return {
        "summary": summary.strip(),
        "findings": normalized,
        "finding_count": len(normalized),
    }


def review_python_code(
    code: str,
    *,
    model: str,
    base_url: str,
    timeout: int,
    focus: str | None = None,
) -> dict[str, Any]:
    llm = build_llm(model=model, base_url=base_url, timeout=timeout, temperature=0.1)
    numbered = "\n".join(f"{i:>4}| {line}" for i, line in enumerate(code.splitlines(), start=1))
    focus_line = ""
    if focus:
        focus_line = f"\nFocus especially on: {focus.strip()}.\n"
    user_prompt = f"""Review this Python file. Report all meaningful defects you can justify.
{focus_line}
Source (with line numbers):
{numbered}

Return JSON:
{{
  "summary": "short overall assessment",
  "findings": [
    {{
      "id": "F1",
      "category": "logic",
      "line_start": 12,
      "line_end": 15,
      "title": "...",
      "detail": "...",
      "severity": "high",
      "confidence": 0.8
    }}
  ]
}}
"""
    repair = (
        "Return ONLY JSON with keys summary and findings. "
        "Each finding must include id, category, line_start, line_end, title, detail, severity, confidence."
    )
    payload = chat_json(
        llm,
        REVIEWER_SYSTEM,
        user_prompt,
        repair_hint=repair,
        max_attempts=3,
    )
    return _validate_review(payload, code=code)
