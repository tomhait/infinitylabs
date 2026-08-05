"""Single-node agents: retrieval-backed research → pro → con → summarizer."""

from __future__ import annotations

import json
import re

from llm import ModelTierConfig, chat, resolve_tiers
from retrieval import format_sources_for_prompt, retrieve_sources
from state import DebateState, Finding


def _extract_json_array(text: str) -> list[dict]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Model did not return a JSON array of findings")


def research(
    state: DebateState,
    *,
    tiers: ModelTierConfig | None = None,
) -> DebateState:
    tiers = tiers or resolve_tiers()
    provider, model = tiers.for_role("research")
    print(f"   retrieving papers… (LLM {provider}/{model})")
    state.sources = retrieve_sources(state.question, max_sources=8)
    if len(state.sources) < 3:
        raise RuntimeError(
            f"Retrieved only {len(state.sources)} papers with abstracts; "
            "try again later or set semanticscholar_api_key in .env"
        )

    catalog = format_sources_for_prompt(state.sources)
    system = (
        "You are a research analyst. You MUST ground every finding in the "
        "provided retrieved papers only. Do not invent papers, DOIs, or facts "
        "absent from the abstracts. Return ONLY a JSON array of 5 objects, "
        'each: {"claim": "...", "source_index": <int>}. '
        "source_index is the [n] number from the paper list. "
        "Claims must be concrete and usable by both debate sides. No advocacy."
    )
    user = (
        f"Debate question:\n{state.question}\n\n"
        f"Retrieved papers:\n{catalog}\n\n"
        "Return JSON array of exactly 5 findings."
    )
    text = chat(
        system,
        user,
        provider=provider,
        model=model,
        temperature=0.2,
        max_tokens=800,
    )
    raw = _extract_json_array(text)

    findings: list[Finding] = []
    for item in raw[:5]:
        idx = int(item["source_index"])
        if idx < 1 or idx > len(state.sources):
            continue
        src = state.sources[idx - 1]
        claim = str(item.get("claim") or "").strip()
        if not claim:
            continue
        findings.append(
            Finding(
                claim=claim,
                source_index=idx,
                source_title=src.title,
                doi=src.doi,
            )
        )

    if len(findings) < 3:
        raise RuntimeError("Research produced fewer than 3 valid grounded findings")

    state.findings = findings
    return state


def _findings_block(state: DebateState) -> str:
    return "\n".join(f"- {line}" for line in state.finding_lines)


def argue_pro(
    state: DebateState,
    *,
    tiers: ModelTierConfig | None = None,
    round_index: int = 1,
) -> DebateState:
    tiers = tiers or resolve_tiers()
    provider, model = tiers.for_role("debate")
    if round_index == 1:
        system = (
            "You are Team Pro in a structured debate. "
            "Argue only for your assigned stance. Ground claims in the research "
            "findings and cite them by [n]. Write one focused argument "
            "(roughly 180-250 words). Do not invent sources."
        )
        user = (
            f"Question: {state.question}\n"
            f"Your stance: {state.pro_stance}\n\n"
            f"Research findings:\n{_findings_block(state)}\n\n"
            "Write Team Pro's opening argument."
        )
    else:
        system = (
            "You are Team Pro in round 2 of a structured debate. "
            "Argue only for your stance. Rebut Team Con's latest points, "
            "advance your case, cite findings by [n]. "
            "Roughly 180-250 words. Do not invent sources."
        )
        user = (
            f"Question: {state.question}\n"
            f"Your stance: {state.pro_stance}\n\n"
            f"Research findings:\n{_findings_block(state)}\n\n"
            f"Your previous argument:\n{state.pro_argument}\n\n"
            f"Team Con's latest argument:\n{state.con_argument}\n\n"
            "Write Team Pro's round-2 argument."
        )
    state.pro_argument = chat(
        system,
        user,
        provider=provider,
        model=model,
        max_tokens=450,
    )
    return state


def argue_con(
    state: DebateState,
    *,
    tiers: ModelTierConfig | None = None,
    round_index: int = 1,
) -> DebateState:
    tiers = tiers or resolve_tiers()
    provider, model = tiers.for_role("debate")
    if round_index == 1:
        system = (
            "You are Team Con in a structured debate. "
            "Argue only for your assigned stance. You may rebut Team Pro. "
            "Ground claims in the research findings and cite them by [n]. "
            "Write one focused argument (roughly 180-250 words). "
            "Do not invent sources."
        )
        user = (
            f"Question: {state.question}\n"
            f"Your stance: {state.con_stance}\n\n"
            f"Research findings:\n{_findings_block(state)}\n\n"
            f"Team Pro's argument:\n{state.pro_argument}\n\n"
            "Write Team Con's response."
        )
    else:
        system = (
            "You are Team Con in round 2 of a structured debate. "
            "Argue only for your stance. Rebut Team Pro's latest points, "
            "cite findings by [n]. Roughly 180-250 words. Do not invent sources."
        )
        user = (
            f"Question: {state.question}\n"
            f"Your stance: {state.con_stance}\n\n"
            f"Research findings:\n{_findings_block(state)}\n\n"
            f"Your previous argument:\n{state.con_argument}\n\n"
            f"Team Pro's latest argument:\n{state.pro_argument}\n\n"
            "Write Team Con's round-2 response."
        )
    state.con_argument = chat(
        system,
        user,
        provider=provider,
        model=model,
        max_tokens=450,
    )
    return state


def summarize(
    state: DebateState,
    *,
    tiers: ModelTierConfig | None = None,
) -> DebateState:
    tiers = tiers or resolve_tiers()
    provider, model = tiers.for_role("summary")
    history = ""
    if len(state.rounds) > 1:
        parts = []
        for r in state.rounds:
            parts.append(
                f"--- Round {r.round_index} ---\n"
                f"Pro:\n{r.pro_argument}\n\nCon:\n{r.con_argument}"
            )
        history = "\n\n".join(parts)

    system = (
        "You are a neutral synthesizer. Produce a plain-text synthesis of the "
        "debate (at most 200 words): main points of agreement, key disagreements, "
        "residual uncertainties, and what would change the conclusion. "
        "Do not declare a winner."
    )
    user = (
        f"Question: {state.question}\n\n"
        f"Findings:\n{_findings_block(state)}\n\n"
        + (f"Full round history:\n{history}\n\n" if history else "")
        + f"Final Pro ({state.pro_stance}):\n{state.pro_argument}\n\n"
        f"Final Con ({state.con_stance}):\n{state.con_argument}\n\n"
        "Write the neutral synthesis (≤200 words)."
    )
    state.synthesis = chat(
        system,
        user,
        provider=provider,
        model=model,
        temperature=0.2,
        max_tokens=350,
    )
    return state
