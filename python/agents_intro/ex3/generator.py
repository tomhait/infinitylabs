"""Generator agent: create Python code with a fixed planted-bug budget."""

from __future__ import annotations

from typing import Any

from llm import build_llm, chat_json, chat_python_and_json

BUG_BUDGET = {
    "logic": 4,
    "edge_case": 2,
    "security": 2,
    "performance": 2,
    "api_design": 1,
    "maintainability": 1,
}

DEFAULT_X = sum(BUG_BUDGET.values())  # 12

GENERATOR_SYSTEM = """You are Agent A: a Python code generator for an evaluation benchmark.

Your job is to generate ONE self-contained Python module that intentionally contains
exactly the requested number of planted bugs, with a precise ground-truth label for each.

Output format (STRICT):
1) First output a python fenced block with the full source:
```python
# code here
```
2) Then output a json fenced block with metadata only (NO code field):
```json
{"topic":"...","bugs":[...]}
```

Rules:
- Code must be syntactically valid Python 3.
- Planted bugs must be realistic and distinct (do not duplicate the same issue).
- Do NOT include comments that reveal bugs (no TODO BUG markers).
- Do NOT put the Python source inside JSON (JSON cannot safely hold raw multiline code).
- Each ground-truth item must include: id, category, line_start, line_end, title, detail.
- Categories must match the requested budget exactly.
- Explicit checklist in the bugs list: 4 logic, 2 edge_case, 2 security, 2 performance, 1 api_design, 1 maintainability.
- line_start/line_end are 1-based line numbers in the generated code.
- Prefer one cohesive module (helpers + main functions), ~80-160 lines.
"""

BUDGET_REPAIR_SYSTEM = """You relabel planted bugs for a Python evaluation benchmark.
Return ONLY valid JSON with keys topic and bugs.
Do not include source code.
Ensure bugs has exactly the requested count and exact category budget.
Each bug needs: id, category, line_start, line_end, title, detail.
Ids must be unique (B1..B12 preferred).
"""


class CategoryBudgetError(ValueError):
    """Raised when bug category counts do not match the required budget."""

    def __init__(self, message: str, counts: dict[str, int]):
        super().__init__(message)
        self.counts = counts


def _count_categories(bugs: list[dict[str, Any]]) -> dict[str, int]:
    counts = {k: 0 for k in BUG_BUDGET}
    for bug in bugs:
        counts[bug["category"]] = counts.get(bug["category"], 0) + 1
    return counts


def _normalize_bugs(code: str, bugs: Any, expected_x: int) -> list[dict[str, Any]]:
    if not isinstance(bugs, list) or len(bugs) != expected_x:
        raise ValueError(
            f"Expected exactly {expected_x} bugs, got {0 if not isinstance(bugs, list) else len(bugs)}."
        )

    required = {"id", "category", "line_start", "line_end", "title", "detail"}
    lines = code.splitlines()
    max_line = max(1, len(lines))
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for idx, bug in enumerate(bugs, start=1):
        if not isinstance(bug, dict):
            raise ValueError(f"Bug #{idx} is not an object.")
        missing = required - set(bug)
        if missing:
            raise ValueError(f"Bug #{idx} missing fields: {sorted(missing)}")
        bug_id = str(bug["id"]).strip()
        if not bug_id or bug_id in seen_ids:
            bug_id = f"B{idx}"
            if bug_id in seen_ids:
                bug_id = f"B{idx}_{len(seen_ids)}"
        seen_ids.add(bug_id)
        category = str(bug["category"]).strip().lower()
        if category not in BUG_BUDGET:
            raise ValueError(f"Bug {bug_id} has unsupported category '{category}'.")
        try:
            line_start = int(bug["line_start"])
            line_end = int(bug["line_end"])
        except (TypeError, ValueError) as error:
            raise ValueError(f"Bug {bug_id} has invalid line numbers.") from error
        line_start = min(max(1, line_start), max_line)
        line_end = min(max(line_start, line_end), max_line)
        title = str(bug["title"]).strip()
        detail = str(bug["detail"]).strip()
        if not title or not detail:
            raise ValueError(f"Bug {bug_id} needs non-empty title/detail.")
        normalized.append(
            {
                "id": bug_id,
                "category": category,
                "line_start": line_start,
                "line_end": line_end,
                "title": title,
                "detail": detail,
            }
        )
    return normalized


def _validate_generation(
    code: str,
    meta: dict[str, Any],
    expected_x: int,
    *,
    strict_budget: bool = True,
) -> dict[str, Any]:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Generator returned empty Python code.")

    topic = meta.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        topic = "unspecified"

    normalized = _normalize_bugs(code, meta.get("bugs"), expected_x=expected_x)
    counts = _count_categories(normalized)
    budget_warning = None
    for category, expected in BUG_BUDGET.items():
        if counts.get(category, 0) != expected:
            msg = (
                f"Category budget mismatch for '{category}': "
                f"expected {expected}, got {counts.get(category, 0)}. Actual={counts}"
            )
            if strict_budget:
                raise CategoryBudgetError(msg, counts=counts)
            budget_warning = msg
            break

    compile(code, "<generated>", "exec")

    return {
        "topic": topic.strip(),
        "code": code if code.endswith("\n") else code + "\n",
        "bugs": normalized,
        "x": expected_x,
        "bug_budget": dict(BUG_BUDGET),
        "actual_bug_budget": counts,
        "budget_warning": budget_warning,
    }


def _repair_bug_budget(
    llm: Any,
    *,
    code: str,
    topic: str,
    bugs: list[dict[str, Any]],
    counts: dict[str, int],
    expected_x: int,
) -> dict[str, Any]:
    numbered = "\n".join(f"{i:>4}| {line}" for i, line in enumerate(code.splitlines(), start=1))
    user_prompt = f"""The Python code below already exists.
Current bug labels have wrong category counts: {counts}
Required exact budget: {BUG_BUDGET}
Required bug count: {expected_x}

Rewrite ONLY the bugs metadata so categories match the budget exactly.
Keep bugs grounded in real issues present in this code.
You may relabel categories and adjust titles/details/line ranges as needed.

Topic hint: {topic}

Source:
{numbered}

Current bugs JSON:
{bugs}

Return JSON:
{{
  "topic": "{topic}",
  "bugs": [ ... exactly {expected_x} items ... ]
}}
"""
    meta = chat_json(
        llm,
        BUDGET_REPAIR_SYSTEM,
        user_prompt,
        repair_hint=(
            f"Return ONLY JSON with topic + bugs. Exactly {expected_x} bugs and budget {BUG_BUDGET}."
        ),
        max_attempts=3,
    )
    meta.pop("code", None)
    return meta


def generate_buggy_module(
    *,
    model: str,
    base_url: str,
    timeout: int,
    expected_x: int = DEFAULT_X,
    topic_hint: str | None = None,
) -> dict[str, Any]:
    if expected_x != DEFAULT_X:
        raise ValueError(f"This implementation expects x={DEFAULT_X} (fixed bug budget).")

    llm = build_llm(model=model, base_url=base_url, timeout=timeout, temperature=0.4)
    topic_line = topic_hint or "utility module for processing user orders / inventory"
    user_prompt = f"""Create a Python module about: {topic_line}

Plant exactly {expected_x} bugs with this EXACT category budget:
- logic: 4
- edge_case: 2
- security: 2
- performance: 2
- api_design: 1
- maintainability: 1

Before finishing, count the categories in your bugs list and verify the budget.

Return EXACTLY this structure:

```python
<full python module here>
```

```json
{{
  "topic": "short topic",
  "bugs": [
    {{
      "id": "B1",
      "category": "logic",
      "line_start": 10,
      "line_end": 12,
      "title": "short title",
      "detail": "what is wrong and why"
    }}
  ]
}}
```

Remember: JSON must contain ONLY topic + bugs (no code field).
"""
    repair = (
        "Re-output using ```python``` then ```json```. "
        f"JSON bugs must be exactly {expected_x} items matching budget {BUG_BUDGET}."
    )

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            code, meta = chat_python_and_json(
                llm,
                GENERATOR_SYSTEM,
                user_prompt,
                repair_hint=repair,
                max_attempts=3,
            )
            meta.pop("code", None)
            try:
                return _validate_generation(code, meta, expected_x=expected_x, strict_budget=True)
            except CategoryBudgetError as budget_error:
                # Keep the code; repair only bug labels to match the budget.
                topic = str(meta.get("topic") or "unspecified")
                current_bugs = meta.get("bugs") if isinstance(meta.get("bugs"), list) else []
                repaired_meta = _repair_bug_budget(
                    llm,
                    code=code,
                    topic=topic,
                    bugs=current_bugs,
                    counts=budget_error.counts,
                    expected_x=expected_x,
                )
                try:
                    return _validate_generation(
                        code, repaired_meta, expected_x=expected_x, strict_budget=True
                    )
                except CategoryBudgetError:
                    # Last resort: accept total=x with a warning so the experiment continues.
                    result = _validate_generation(
                        code, repaired_meta, expected_x=expected_x, strict_budget=False
                    )
                    if result["budget_warning"] is None:
                        # If repair changed count incorrectly, fall through.
                        return result
                    return result
        except Exception as error:
            last_error = error
            user_prompt = (
                user_prompt
                + f"\n\nPrevious attempt {attempt} failed validation: {error}\n"
                + "Produce a fresh valid response and recount categories carefully."
            )
    assert last_error is not None
    raise last_error
