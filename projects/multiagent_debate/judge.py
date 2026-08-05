"""Optional LLM judge: stronger-case verdict under a fixed rubric (not truth)."""

from __future__ import annotations

import json
import re

from llm import ModelTierConfig, chat, resolve_tiers
from state import DebateState

JUDGE_MAX_TOKENS = 2048


def _balance_object(text: str) -> str | None:
    """Return the first top-level {...} span using brace depth (not regex)."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _extract_json_object(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("Judge returned an empty response")

    # Prefer fenced block contents when present
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    candidate = fence.group(1).strip() if fence else text

    span = _balance_object(candidate) or _balance_object(text)
    if not span:
        raise ValueError(
            "Judge did not return a JSON object "
            f"(response starts with: {text[:120]!r})"
        )
    try:
        return json.loads(span)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Judge JSON parse failed: {exc}; span={span[:200]!r}") from exc


def _clip(value: object, lo: int, hi: int) -> int:
    try:
        n = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        n = lo
    return max(lo, min(hi, n))


def _normalize_verdict(raw: dict) -> dict:
    pro = raw.get("pro") or {}
    con = raw.get("con") or {}

    pro_scores = {
        "grounding": _clip(pro.get("grounding"), 0, 2),
        "logic": _clip(pro.get("logic"), 0, 2),
        "engagement": _clip(pro.get("engagement"), 0, 1),
        "humility": _clip(pro.get("humility"), 0, 2),
    }
    con_scores = {
        "grounding": _clip(con.get("grounding"), 0, 2),
        "logic": _clip(con.get("logic"), 0, 2),
        "engagement": _clip(con.get("engagement"), 0, 2),
        "humility": _clip(con.get("humility"), 0, 2),
    }
    pro_scores["total"] = sum(pro_scores.values())
    con_scores["total"] = sum(con_scores.values())

    margin = abs(pro_scores["total"] - con_scores["total"])
    if margin >= 2:
        winner = "pro" if pro_scores["total"] > con_scores["total"] else "con"
    else:
        winner = "tie"

    return {
        "pro": pro_scores,
        "con": con_scores,
        "winner": winner,
        "margin": margin,
        "rationale": str(raw.get("rationale") or "").strip(),
        "note": (
            "Verdict = stronger case under rubric; not objective truth. "
            "Tie if margin < 2."
        ),
    }


def _judge_prompt(state: DebateState) -> tuple[str, str]:
    findings = "\n".join(f"- {line}" for line in state.finding_lines)
    system = (
        "You are an impartial debate judge. Score ONLY from the transcript. "
        "Do not invent facts or sources. "
        "Respond with a single JSON object only — no markdown fences, no prose. "
        "Schema: "
        '{"pro":{"grounding":0-2,"logic":0-2,"engagement":0-1,"humility":0-2},'
        '"con":{"grounding":0-2,"logic":0-2,"engagement":0-2,"humility":0-2},'
        '"rationale":"..."}. '
        "Do NOT include winner or totals. "
        "Keep rationale to 2-4 short sentences."
    )
    user = (
        f"Question: {state.question}\n\n"
        f"Pro stance: {state.pro_stance}\n"
        f"Con stance: {state.con_stance}\n\n"
        f"Findings:\n{findings}\n\n"
        f"Pro argument:\n{state.pro_argument}\n\n"
        f"Con argument:\n{state.con_argument}\n\n"
        "Return ONLY the JSON object."
    )
    return system, user


def _call_judge(system: str, user: str, *, provider: str, model: str) -> str:
    return chat(
        system,
        user,
        provider=provider,
        model=model,
        temperature=0.1,
        max_tokens=JUDGE_MAX_TOKENS,
    )


def judge(
    state: DebateState,
    *,
    tiers: ModelTierConfig | None = None,
) -> DebateState:
    """Score claim strength. Default judge provider: Gemini."""
    tiers = tiers or resolve_tiers()
    provider, model = tiers.for_role("judge")
    state.judge_provider = provider
    system, user = _judge_prompt(state)

    attempts: list[tuple[str, str]] = [(provider, model)]
    fallback = (tiers.provider, tiers.debate_model)
    if fallback != (provider, model):
        attempts.append(fallback)

    last_error: Exception | None = None
    for attempt_i, (prov, mod) in enumerate(attempts):
        for retry in range(2):
            try:
                text = _call_judge(system, user, provider=prov, model=mod)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                print(f"   judge call failed ({prov}/{mod}): {exc}")
                break  # try next provider

            try:
                raw = _extract_json_object(text)
                state.verdict = _normalize_verdict(raw)
                state.judge_provider = prov
                state.verdict["judge_provider"] = prov
                state.verdict["judge_model"] = mod
                if attempt_i > 0 or retry > 0:
                    print(f"   judge succeeded on {prov}/{mod} (attempt {attempt_i + 1}, retry {retry})")
                return state
            except ValueError as exc:
                last_error = exc
                preview = (text or "")[:180].replace("\n", " ")
                print(f"   judge parse failed ({prov}/{mod}): {exc}")
                print(f"   preview: {preview!r}")
                # Tighten prompt on retry
                user = (
                    user
                    + "\n\nPREVIOUS OUTPUT WAS INVALID OR TRUNCATED. "
                    "Reply with one complete JSON object only, closed braces, no markdown."
                )

    raise RuntimeError(f"Judge failed after retries: {last_error}")
