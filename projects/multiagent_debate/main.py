#!/usr/bin/env python3
"""Retrieval-backed multi-agent debate pipeline with optional rounds + judge."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents import argue_con, argue_pro, research, summarize
from judge import judge
from llm import resolve_tiers
from scorer import score, tfidf_uniqueness
from state import DebateState, RoundRecord

ROOT = Path(__file__).resolve().parent


def run(
    provider: str = "groq",
    *,
    rounds: int = 1,
    uniqueness_threshold: float = 0.20,
    enable_judge: bool = False,
    research_model: str | None = None,
    debate_model: str | None = None,
    summary_model: str | None = None,
    judge_provider: str | None = None,
    judge_model: str | None = None,
) -> DebateState:
    rounds = max(1, min(2, rounds))
    tiers = resolve_tiers(
        provider,
        research_model=research_model,
        debate_model=debate_model,
        summary_model=summary_model,
        judge_provider=judge_provider,
        judge_model=judge_model,
    )
    state = DebateState(
        max_rounds=rounds,
        uniqueness_collapse_threshold=uniqueness_threshold,
    )
    print(f"Debate provider: {tiers.provider}")
    print(
        f"Model tiers: research={tiers.research_model} | "
        f"debate={tiers.debate_model} | summary={tiers.summary_model}"
    )
    print(f"Rounds: up to {rounds} (early-stop if uniqueness < {uniqueness_threshold})")
    if enable_judge:
        print(f"Judge: {tiers.judge_provider}/{tiers.judge_model}")
    print(f"Question: {state.question}\n")

    print("1) Research (retrieval-backed)…")
    research(state, tiers=tiers)
    peer = sum(1 for s in state.sources if s.is_peer_reviewed)
    print(f"   {len(state.sources)} sources ({peer} peer-reviewed heuristic)")
    print(f"   {len(state.findings)} grounded findings")

    for r in range(1, rounds + 1):
        print(f"2.{r}) Team Pro (round {r})…")
        argue_pro(state, tiers=tiers, round_index=r)
        print(f"3.{r}) Team Con (round {r})…")
        argue_con(state, tiers=tiers, round_index=r)

        uniq = tfidf_uniqueness(state.pro_argument, state.con_argument)
        record = RoundRecord(
            round_index=r,
            pro_argument=state.pro_argument,
            con_argument=state.con_argument,
            uniqueness=float(uniq["pro_con_uniqueness"]),
            cosine=float(uniq["pro_con_tfidf_cosine"]),
        )
        state.rounds.append(record)
        state.rounds_completed = r
        print(
            f"   uniqueness={record.uniqueness:.4f} "
            f"(cosine={record.cosine:.4f})"
        )

        if r < rounds and record.uniqueness < uniqueness_threshold:
            state.early_stopped = True
            state.early_stop_reason = (
                f"uniqueness {record.uniqueness:.4f} < "
                f"threshold {uniqueness_threshold:.4f} after round {r}"
            )
            print(f"   early stop: {state.early_stop_reason}")
            break

    print("4) Summarizer…")
    summarize(state, tiers=tiers)

    if enable_judge:
        print(f"5) Judge ({tiers.judge_provider}/{tiers.judge_model})…")
        judge(state, tiers=tiers)

    state.scores = score(state)
    state.scores["models"] = tiers.as_dict()
    state.scores["termination"] = {
        "max_rounds": state.max_rounds,
        "rounds_completed": state.rounds_completed,
        "early_stopped": state.early_stopped,
        "early_stop_reason": state.early_stop_reason,
        "uniqueness_collapse_threshold": state.uniqueness_collapse_threshold,
        "round_uniqueness": [
            {"round": r.round_index, "uniqueness": r.uniqueness, "cosine": r.cosine}
            for r in state.rounds
        ],
    }
    if state.verdict:
        state.scores["verdict"] = state.verdict
    return state


def render(state: DebateState) -> str:
    source_lines = []
    for i, s in enumerate(state.sources, 1):
        flag = "peer-reviewed~" if s.is_peer_reviewed else "other/preprint~"
        source_lines.append(
            f"  [{i}] ({flag}) {s.title} ({s.year or 'n.d.'}) — {s.venue or 'venue?'}"
        )
        source_lines.append(f"       {s.url or s.doi or 'no link'}")

    finding_lines = [
        f"  {i}. {f.as_line()}" for i, f in enumerate(state.findings, 1)
    ]

    round_blocks: list[str] = []
    for r in state.rounds:
        round_blocks.extend(
            [
                f"--- ROUND {r.round_index} "
                f"(uniqueness={r.uniqueness:.4f}) ---",
                "TEAM PRO",
                r.pro_argument,
                "",
                "TEAM CON",
                r.con_argument,
                "",
            ]
        )

    model_lines = []
    models = (state.scores or {}).get("models") or {}
    if models:
        model_lines = [
            "MODEL TIERS",
            json.dumps(models, indent=2),
            "",
        ]

    lines = [
        "=" * 72,
        "DEBATE QUESTION",
        state.question,
        "",
        *model_lines,
        "TERMINATION",
        f"  max_rounds={state.max_rounds} completed={state.rounds_completed} "
        f"early_stopped={state.early_stopped}",
        f"  reason={state.early_stop_reason or 'completed scheduled rounds'}",
        "",
        "RETRIEVED SOURCES",
        *source_lines,
        "",
        "FINDINGS (grounded in retrieved sources)",
        *finding_lines,
        "",
        *round_blocks,
        "NEUTRAL SYNTHESIS",
        state.synthesis,
        "",
    ]

    if state.verdict:
        lines.extend(
            [
                "JUDGED VERDICT (rubric — not truth)",
                json.dumps(state.verdict, indent=2),
                "",
            ]
        )

    lines.extend(
        [
            "DETERMINISTIC SCORE",
            json.dumps(state.scores, indent=2),
            "=" * 72,
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-agent debate MVP")
    parser.add_argument(
        "--provider",
        choices=["groq", "gemini"],
        default="groq",
        help="Debate pipeline provider (default: groq)",
    )
    parser.add_argument(
        "--research-model",
        default=None,
        help="Cheaper model for research JSON extraction",
    )
    parser.add_argument(
        "--debate-model",
        default=None,
        help="Stronger model for Pro/Con arguments",
    )
    parser.add_argument(
        "--summary-model",
        default=None,
        help="Cheaper model for neutral synthesis",
    )
    parser.add_argument(
        "--judge-provider",
        choices=["groq", "gemini"],
        default=None,
        help="Judge provider (default: gemini)",
    )
    parser.add_argument(
        "--judge-model",
        default=None,
        help="Judge model (default: gemini-flash-latest)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        choices=[1, 2],
        default=1,
        help="Max exchange rounds (default: 1). May early-stop on uniqueness collapse.",
    )
    parser.add_argument(
        "--uniqueness-threshold",
        type=float,
        default=0.20,
        help="Early-stop if pro-con TF-IDF uniqueness falls below this (default: 0.20)",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Run LLM judge (default provider: gemini) for a rubric verdict",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "outputs" / "debate_m0.txt",
        help="Where to write the transcript",
    )
    args = parser.parse_args()

    state = run(
        provider=args.provider,
        rounds=args.rounds,
        uniqueness_threshold=args.uniqueness_threshold,
        enable_judge=args.judge,
        research_model=args.research_model,
        debate_model=args.debate_model,
        summary_model=args.summary_model,
        judge_provider=args.judge_provider,
        judge_model=args.judge_model,
    )
    text = render(state)
    print("\n" + text)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    scores_path = args.out.with_suffix(".scores.json")
    scores_path.write_text(json.dumps(state.scores, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out}")
    print(f"Wrote {scores_path}")


if __name__ == "__main__":
    main()
