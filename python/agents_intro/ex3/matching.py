"""Matching strategies for planted bugs vs reviewer findings."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

import requests

from llm import build_llm, chat_json

MATCH_MODES = ("deterministic", "embeddings", "llm_judge", "all")


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2]


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _line_overlap(a_start: int, a_end: int, b_start: int, b_end: int, slack: int = 5) -> bool:
    a0, a1 = a_start - slack, a_end + slack
    b0, b1 = b_start - slack, b_end + slack
    return not (a1 < b0 or b1 < a0)


def item_text(item: dict[str, Any]) -> str:
    return (
        f"category: {item.get('category', '')}\n"
        f"title: {item.get('title', '')}\n"
        f"detail: {item.get('detail', '')}\n"
        f"lines: {item.get('line_start', '')}-{item.get('line_end', '')}"
    )


def deterministic_score(planted: dict[str, Any], found: dict[str, Any]) -> float:
    score = 0.0
    if planted["category"] == found["category"]:
        score += 0.35
    if _line_overlap(
        planted["line_start"],
        planted["line_end"],
        found["line_start"],
        found["line_end"],
    ):
        score += 0.35
    planted_text = f"{planted['title']} {planted['detail']}"
    found_text = f"{found['title']} {found['detail']}"
    score += 0.30 * _jaccard(set(_tokenize(planted_text)), set(_tokenize(found_text)))
    return score


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _ollama_embed(text: str, *, model: str, base_url: str, timeout: int) -> list[float] | None:
    url = f"{base_url.rstrip('/')}/api/embeddings"
    try:
        response = requests.post(
            url,
            json={"model": model, "prompt": text},
            timeout=timeout,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        emb = data.get("embedding")
        if isinstance(emb, list) and emb and isinstance(emb[0], (int, float)):
            return [float(x) for x in emb]
    except requests.RequestException:
        return None
    return None


class EmbeddingBackend:
    """Ollama embeddings with local TF-IDF cosine fallback."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        timeout: int,
        corpus_texts: list[str],
    ):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.backend = "ollama"
        self._cache: dict[str, list[float]] = {}

        # Probe Ollama once.
        probe = _ollama_embed("probe", model=model, base_url=base_url, timeout=timeout)
        if not probe:
            self.backend = "tfidf_fallback"
            self._fit_tfidf(corpus_texts)

    def _fit_tfidf(self, corpus_texts: list[str]) -> None:
        docs = [_tokenize(t) for t in corpus_texts]
        df: Counter[str] = Counter()
        for tokens in docs:
            df.update(set(tokens))
        n_docs = max(1, len(docs))
        self._idf = {term: math.log((1 + n_docs) / (1 + count)) + 1.0 for term, count in df.items()}
        self._vocab = {term: i for i, term in enumerate(sorted(self._idf))}

    def _tfidf_vector(self, text: str) -> list[float]:
        tokens = _tokenize(text)
        tf = Counter(tokens)
        vec = [0.0] * len(self._vocab)
        length = max(1, len(tokens))
        for term, count in tf.items():
            idx = self._vocab.get(term)
            if idx is None:
                continue
            vec[idx] = (count / length) * self._idf.get(term, 0.0)
        return vec

    def embed(self, text: str) -> list[float]:
        if text in self._cache:
            return self._cache[text]
        if self.backend == "ollama":
            emb = _ollama_embed(text, model=self.model, base_url=self.base_url, timeout=self.timeout)
            if emb:
                self._cache[text] = emb
                return emb
            # Switch permanently if Ollama embeddings become unavailable mid-run.
            self.backend = "tfidf_fallback"
            if not hasattr(self, "_vocab"):
                self._fit_tfidf([text])
        vec = self._tfidf_vector(text)
        self._cache[text] = vec
        return vec

    def similarity(self, a: str, b: str) -> float:
        return _cosine(self.embed(a), self.embed(b))


class LLMJudge:
    def __init__(self, *, model: str, base_url: str, timeout: int):
        self.llm = build_llm(model=model, base_url=base_url, timeout=timeout, temperature=0.0)
        self._cache: dict[tuple[str, str], tuple[bool, float]] = {}

    def decide(self, planted: dict[str, Any], found: dict[str, Any]) -> tuple[bool, float]:
        key = (planted["id"], found["id"])
        if key in self._cache:
            return self._cache[key]

        system = (
            "You are a strict evaluation judge for code-review findings.\n"
            "Decide whether a reviewer finding refers to the SAME planted bug.\n"
            "Return ONLY JSON: {\"match\": true|false, \"confidence\": 0..1, \"reason\": \"...\"}"
        )
        user = (
            "Planted bug:\n"
            f"{item_text(planted)}\n\n"
            "Reviewer finding:\n"
            f"{item_text(found)}\n\n"
            "Do they describe the same underlying issue?"
        )
        try:
            payload = chat_json(
                self.llm,
                system,
                user,
                repair_hint='Return ONLY JSON like {"match": true, "confidence": 0.8, "reason": "..."}',
                max_attempts=2,
            )
            matched = bool(payload.get("match"))
            try:
                confidence = float(payload.get("confidence", 0.5))
            except (TypeError, ValueError):
                confidence = 0.5
            confidence = min(1.0, max(0.0, confidence))
        except Exception:
            matched = False
            confidence = 0.0

        self._cache[key] = (matched, confidence)
        return matched, confidence


def _greedy_match(
    planted_bugs: list[dict[str, Any]],
    review_findings: list[dict[str, Any]],
    candidates: list[tuple[float, str, str, dict[str, Any]]],
) -> dict[str, Any]:
    candidates.sort(reverse=True, key=lambda x: x[0])
    matched_planted: set[str] = set()
    matched_found: set[str] = set()
    matches: list[dict[str, Any]] = []

    for score, planted_id, found_id, meta in candidates:
        if planted_id in matched_planted or found_id in matched_found:
            continue
        matched_planted.add(planted_id)
        matched_found.add(found_id)
        planted = next(b for b in planted_bugs if b["id"] == planted_id)
        found = next(f for f in review_findings if f["id"] == found_id)
        matches.append(
            {
                "planted_id": planted_id,
                "finding_id": found_id,
                "similarity": round(score, 4),
                "planted_title": planted["title"],
                "finding_title": found["title"],
                "category": planted["category"],
                **meta,
            }
        )

    false_negatives = [b for b in planted_bugs if b["id"] not in matched_planted]
    false_positives = [f for f in review_findings if f["id"] not in matched_found]
    return {
        "matches": matches,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "tp": len(matches),
        "fp": len(false_positives),
        "fn": len(false_negatives),
    }


def match_findings(
    planted_bugs: list[dict[str, Any]],
    review_findings: list[dict[str, Any]],
    *,
    match_mode: str = "deterministic",
    threshold: float = 0.55,
    embed_threshold: float = 0.72,
    judge_threshold: float = 0.5,
    embed_model: str = "nomic-embed-text",
    judge_model: str = "llama3.1",
    base_url: str = "http://localhost:11434",
    timeout: int = 180,
    allow_llm: bool = True,
) -> dict[str, Any]:
    if match_mode not in MATCH_MODES:
        raise ValueError(f"Unknown match_mode '{match_mode}'. Expected one of {MATCH_MODES}.")

    embedder: EmbeddingBackend | None = None
    judge: LLMJudge | None = None
    embedding_backend = None

    needs_embeddings = match_mode in {"embeddings", "all"}
    needs_judge = match_mode in {"llm_judge", "all"}

    if needs_embeddings:
        corpus = [item_text(x) for x in planted_bugs] + [item_text(x) for x in review_findings]
        embedder = EmbeddingBackend(
            model=embed_model,
            base_url=base_url,
            timeout=timeout,
            corpus_texts=corpus or ["empty"],
        )
        embedding_backend = embedder.backend

    if needs_judge and allow_llm:
        judge = LLMJudge(model=judge_model, base_url=base_url, timeout=timeout)

    candidates: list[tuple[float, str, str, dict[str, Any]]] = []

    for planted in planted_bugs:
        for found in review_findings:
            votes: dict[str, Any] = {}
            yes_modes: list[str] = []
            scores: dict[str, float] = {}

            # Deterministic
            if match_mode in {"deterministic", "all"}:
                d_score = deterministic_score(planted, found)
                d_yes = d_score >= threshold
                votes["deterministic"] = {"yes": d_yes, "score": round(d_score, 4)}
                scores["deterministic"] = d_score
                if d_yes:
                    yes_modes.append("deterministic")

            # Embeddings
            if match_mode == "embeddings" or (match_mode == "all" and not yes_modes):
                assert embedder is not None
                e_score = embedder.similarity(item_text(planted), item_text(found))
                e_yes = e_score >= embed_threshold
                votes["embeddings"] = {"yes": e_yes, "score": round(e_score, 4)}
                scores["embeddings"] = e_score
                if e_yes:
                    yes_modes.append("embeddings")

            # LLM judge
            if match_mode == "llm_judge" or (match_mode == "all" and not yes_modes):
                if judge is not None:
                    matched, confidence = judge.decide(planted, found)
                    j_yes = matched and confidence >= judge_threshold
                    votes["llm_judge"] = {
                        "yes": j_yes,
                        "score": round(confidence, 4),
                        "matched": matched,
                    }
                    scores["llm_judge"] = confidence
                    if j_yes:
                        yes_modes.append("llm_judge")
                else:
                    # Offline/demo fallback: use deterministic as a weak proxy.
                    d_score = scores.get("deterministic", deterministic_score(planted, found))
                    j_yes = d_score >= threshold
                    votes["llm_judge"] = {
                        "yes": j_yes,
                        "score": round(d_score, 4),
                        "matched": j_yes,
                        "fallback": "deterministic",
                    }
                    scores["llm_judge"] = d_score
                    if j_yes:
                        yes_modes.append("llm_judge")

            if match_mode == "deterministic":
                accepted = "deterministic" in yes_modes
                score = scores.get("deterministic", 0.0)
            elif match_mode == "embeddings":
                accepted = "embeddings" in yes_modes
                score = scores.get("embeddings", 0.0)
            elif match_mode == "llm_judge":
                accepted = "llm_judge" in yes_modes
                score = scores.get("llm_judge", 0.0)
            else:  # all
                accepted = bool(yes_modes)
                score = max((scores[m] for m in yes_modes), default=0.0)

            if accepted:
                candidates.append(
                    (
                        score,
                        planted["id"],
                        found["id"],
                        {
                            "match_mode": match_mode,
                            "yes_modes": yes_modes,
                            "votes": votes,
                        },
                    )
                )

    result = _greedy_match(planted_bugs, review_findings, candidates)
    result["match_mode"] = match_mode
    result["match_threshold"] = threshold
    result["embed_threshold"] = embed_threshold
    result["judge_threshold"] = judge_threshold
    if embedding_backend is not None:
        result["embedding_backend"] = embedding_backend
    return result
