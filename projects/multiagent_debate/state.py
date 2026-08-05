"""Shared debate state for the Milestone 0 pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from retrieval import Source

QUESTION = (
    "Are current frontier LLMs aligned enough for safe general use "
    "in public-facing products?"
)

PRO_STANCE = (
    "Yes — current frontier LLMs are aligned enough for safe general use "
    "in public products, when deployed with standard product safeguards."
)

CON_STANCE = (
    "No — current frontier LLMs are not aligned enough for safe general use "
    "in public products; residual risks remain material."
)


@dataclass
class Finding:
    claim: str
    source_index: int  # 1-based index into state.sources
    source_title: str = ""
    doi: str | None = None

    def as_line(self) -> str:
        cite = f"[{self.source_index}] {self.source_title}"
        if self.doi:
            cite += f" (doi:{self.doi})"
        return f"{self.claim} — {cite}"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RoundRecord:
    round_index: int
    pro_argument: str
    con_argument: str
    uniqueness: float
    cosine: float


@dataclass
class DebateState:
    question: str = QUESTION
    pro_stance: str = PRO_STANCE
    con_stance: str = CON_STANCE
    sources: list[Source] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    pro_argument: str = ""
    con_argument: str = ""
    synthesis: str = ""
    scores: dict = field(default_factory=dict)
    rounds: list[RoundRecord] = field(default_factory=list)
    rounds_completed: int = 0
    max_rounds: int = 1
    early_stopped: bool = False
    early_stop_reason: str = ""
    uniqueness_collapse_threshold: float = 0.20
    verdict: dict = field(default_factory=dict)
    judge_provider: str = ""

    @property
    def finding_lines(self) -> list[str]:
        return [f.as_line() for f in self.findings]
