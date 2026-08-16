"""Deterministic metrics — pipeline health + debate quality (not truth)."""

from __future__ import annotations

import math
import re
from collections import Counter

from state import DebateState

OVERCLAIM_PATTERNS = [
    r"\balways\b",
    r"\bnever\b",
    r"\bguarantees?\b",
    r"\bproven\b",
    r"\bundoubtedly\b",
    r"\bcertainly\b",
    r"\bno doubt\b",
    r"\bimpossible\b",
    r"\bperfect(?:ly)?\b",
    r"\bcompletely safe\b",
    r"\bfully aligned\b",
]

# Words expected more on Pro vs Con for this debate framing
PRO_LEAN = {
    "enough",
    "sufficient",
    "safeguard",
    "safeguards",
    "mitigation",
    "deployable",
    "manageable",
    "aligned",
    "practical",
    "acceptable",
}
CON_LEAN = {
    "insufficient",
    "residual",
    "jailbreak",
    "jailbreaks",
    "unsolved",
    "hazard",
    "catastrophic",
    "misaligned",
    "unsafe",
    "inadequate",
    "brittle",
    "exploit",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


# ---- TF-IDF uniqueness -------------------------------------------------

def _tfidf_vectors(docs: list[str]) -> list[dict[str, float]]:
    tokenized = [_tokenize(d) for d in docs]
    df: Counter[str] = Counter()
    for toks in tokenized:
        df.update(set(toks))
    n = len(docs)
    idf = {t: math.log((n + 1) / (df[t] + 1)) + 1.0 for t in df}
    vectors: list[dict[str, float]] = []
    for toks in tokenized:
        tf = Counter(toks)
        length = len(toks) or 1
        vec = {t: (tf[t] / length) * idf[t] for t in tf}
        vectors.append(vec)
    return vectors


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    if not keys:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def tfidf_uniqueness(pro: str, con: str) -> dict[str, float]:
    """High uniqueness = low cosine similarity between sides."""
    vecs = _tfidf_vectors([pro, con])
    sim = _cosine(vecs[0], vecs[1])
    return {
        "pro_con_tfidf_cosine": round(sim, 4),
        "pro_con_uniqueness": round(1.0 - sim, 4),
    }


# ---- Engagement ---------------------------------------------------------

def engagement_con_to_pro(pro: str, con: str) -> dict[str, float | int | bool]:
    pro_tokens = _tokenize(pro)
    con_l = con.lower()
    content = [t for t in pro_tokens if len(t) >= 5]
    if len(content) < 9:
        return {
            "engagement_hit_rate": 0.0,
            "engagement_hits": 0,
            "engagement_probes": 0,
            "con_engages_pro": False,
        }

    probes = []
    for i in range(0, len(content) - 2, 4):
        phrase = " ".join(content[i : i + 3])
        probes.append(phrase)
    probes = probes[:12]
    hits = sum(1 for p in probes if p in con_l)
    markers = (
        "however",
        "although",
        "rebut",
        "contrary",
        "pro argues",
        "team pro",
        "you claim",
        "opponent",
    )
    marker_hit = any(m in con_l for m in markers)
    hit_rate = hits / len(probes) if probes else 0.0
    engages = hit_rate >= 0.08 or marker_hit
    return {
        "engagement_hit_rate": round(hit_rate, 4),
        "engagement_hits": hits,
        "engagement_probes": len(probes),
        "con_engages_pro": engages,
    }


# ---- Overclaim densality ------------------------------------------------

def overclaim_density(text: str) -> dict[str, float | int]:
    words = max(_word_count(text), 1)
    matches = 0
    for pat in OVERCLAIM_PATTERNS:
        matches += len(re.findall(pat, text or "", flags=re.IGNORECASE))
    per_100 = 100.0 * matches / words
    return {
        "overclaim_count": matches,
        "overclaim_per_100_words": round(per_100, 3),
    }


# ---- Stance consistency -------------------------------------------------

def stance_consistency(
    pro_arg: str,
    con_arg: str,
    *,
    pro_stance: str,
    con_stance: str,
) -> dict[str, float | bool]:
    pro_toks = set(_tokenize(pro_arg))
    con_toks = set(_tokenize(con_arg))

    pro_own = len(pro_toks & PRO_LEAN)
    pro_opp = len(pro_toks & CON_LEAN)
    con_own = len(con_toks & CON_LEAN)
    con_opp = len(con_toks & PRO_LEAN)

    # Also count overlap with stance sentence tokens as soft signal
    pro_stance_toks = set(_tokenize(pro_stance)) - {"the", "a", "an", "and", "or", "for", "in", "to"}
    con_stance_toks = set(_tokenize(con_stance)) - {"the", "a", "an", "and", "or", "for", "in", "to"}
    pro_own += len(pro_toks & pro_stance_toks)
    con_own += len(con_toks & con_stance_toks)
    pro_opp += len(pro_toks & con_stance_toks)
    con_opp += len(con_toks & pro_stance_toks)

    def ratio(own: int, opp: int) -> float:
        denom = own + opp
        return own / denom if denom else 0.5

    pro_r = ratio(pro_own, pro_opp)
    con_r = ratio(con_own, con_opp)
    return {
        "pro_stance_consistency": round(pro_r, 4),
        "con_stance_consistency": round(con_r, 4),
        "pro_stays_on_side": pro_r >= 0.45,
        "con_stays_on_side": con_r >= 0.45,
    }


# ---- Academic sources + grounding --------------------------------------

def academic_source_metrics(state: DebateState) -> dict[str, float | int]:
    n = len(state.sources)
    peer = sum(1 for s in state.sources if s.is_peer_reviewed)
    with_doi = sum(1 for s in state.sources if s.doi)
    finding_peer = 0
    for f in state.findings:
        if 1 <= f.source_index <= len(state.sources):
            if state.sources[f.source_index - 1].is_peer_reviewed:
                finding_peer += 1
    return {
        "sources_count": n,
        "peer_reviewed_sources": peer,
        "peer_reviewed_source_ratio": round(peer / n, 4) if n else 0.0,
        "doi_source_ratio": round(with_doi / n, 4) if n else 0.0,
        "findings_from_peer_reviewed_ratio": (
            round(finding_peer / len(state.findings), 4) if state.findings else 0.0
        ),
    }


def grounding_rate(argument: str, state: DebateState) -> float:
    """Share of finding claim tokens that appear in the argument (proxy)."""
    if not state.findings:
        return 0.0
    arg = set(_tokenize(argument))
    hits = 0
    for f in state.findings:
        claim_toks = [t for t in _tokenize(f.claim) if len(t) >= 5]
        if not claim_toks:
            continue
        overlap = sum(1 for t in claim_toks if t in arg) / len(claim_toks)
        if overlap >= 0.25 or f"[{f.source_index}]" in argument:
            hits += 1
    return round(hits / len(state.findings), 4)


# ---- Pipeline structural checks ----------------------------------------

def score(state: DebateState) -> dict:
    pro_words = _word_count(state.pro_argument)
    con_words = _word_count(state.con_argument)
    synth_words = _word_count(state.synthesis)

    engagement = engagement_con_to_pro(state.pro_argument, state.con_argument)
    uniqueness = tfidf_uniqueness(state.pro_argument, state.con_argument)
    over_pro = overclaim_density(state.pro_argument)
    over_con = overclaim_density(state.con_argument)
    stance = stance_consistency(
        state.pro_argument,
        state.con_argument,
        pro_stance=state.pro_stance,
        con_stance=state.con_stance,
    )
    academic = academic_source_metrics(state)
    ground_pro = grounding_rate(state.pro_argument, state)
    ground_con = grounding_rate(state.con_argument, state)

    pipeline = {
        "has_question": bool(state.question.strip()),
        "findings_count": len(state.findings),
        "findings_ok": len(state.findings) >= 3,
        "sources_ok": len(state.sources) >= 3,
        "pro_nonempty": pro_words >= 80,
        "con_nonempty": con_words >= 80,
        "con_sees_pro": bool(engagement["con_engages_pro"]),
        "synthesis_ok": synth_words >= 60,
        "pro_word_count": pro_words,
        "con_word_count": con_words,
        "synthesis_word_count": synth_words,
    }
    binary = [
        pipeline["has_question"],
        pipeline["findings_ok"],
        pipeline["sources_ok"],
        pipeline["pro_nonempty"],
        pipeline["con_nonempty"],
        pipeline["con_sees_pro"],
        pipeline["synthesis_ok"],
    ]
    pipeline["total"] = sum(1 for c in binary if c)
    pipeline["max_total"] = len(binary)
    pipeline["pass"] = pipeline["total"] == pipeline["max_total"]

    quality = {
        **academic,
        **uniqueness,
        **engagement,
        "pro_overclaim_count": over_pro["overclaim_count"],
        "pro_overclaim_per_100_words": over_pro["overclaim_per_100_words"],
        "con_overclaim_count": over_con["overclaim_count"],
        "con_overclaim_per_100_words": over_con["overclaim_per_100_words"],
        **stance,
        "pro_grounding_rate": ground_pro,
        "con_grounding_rate": ground_con,
        "mean_grounding_rate": round((ground_pro + ground_con) / 2, 4),
    }

    return {
        "pipeline": pipeline,
        "quality": quality,
    }
