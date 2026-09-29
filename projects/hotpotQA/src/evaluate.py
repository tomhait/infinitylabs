"""Answer metrics (official HotpotQA EM/F1), retrieval metrics, error classification, and cost/latency summaries."""

import re
import string
from collections import Counter

import numpy as np
import pandas as pd


def normalize_answer(s):
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def exact_match(prediction, gold):
    return float(normalize_answer(prediction) == normalize_answer(gold))


def f1_score(prediction, gold):
    pred_norm, gold_norm = normalize_answer(prediction), normalize_answer(gold)
    # yes/no/noanswer must match exactly; partial overlap is meaningless for them
    if pred_norm in {"yes", "no", "noanswer"} or gold_norm in {"yes", "no", "noanswer"}:
        return float(pred_norm == gold_norm)
    pred_tokens, gold_tokens = pred_norm.split(), gold_norm.split()
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def evidence_recall(retrieved_titles, gold_titles, k):
    """Share of gold paragraphs found in the top-k."""
    top = set(retrieved_titles[:k])
    return sum(t in top for t in gold_titles) / len(gold_titles)


def both_gold_found(retrieved_titles, gold_titles, k):
    top = set(retrieved_titles[:k])
    return float(all(t in top for t in gold_titles))


def is_supported(prediction, context_text):
    """Proxy for groundedness: the normalized answer appears in the evidence the model was given."""
    pred = normalize_answer(prediction)
    if pred in {"yes", "no"}:
        return True
    return bool(pred) and f" {pred} " in f" {normalize_answer(context_text)} "


def classify_outcome(prediction, gold, retrieved_titles, gold_titles):
    """correct / format mismatch / retrieval failure / reasoning failure.

    A format mismatch is a wrong EM where one normalized answer contains the other
    ("Lapland" vs "Finland's northernmost province, Lapland"): right content, different wording.
    """
    if exact_match(prediction, gold):
        return "correct"
    pred, ref = normalize_answer(prediction), normalize_answer(gold)
    if pred and ref and pred not in {"yes", "no"} and (f" {pred} " in f" {ref} " or f" {ref} " in f" {pred} "):
        return "format mismatch"
    if retrieved_titles is not None and not all(t in set(retrieved_titles) for t in gold_titles):
        return "retrieval failure"
    return "reasoning failure"


def latency_stats(values, prefix):
    values = np.asarray(values, dtype=float)
    return {
        f"{prefix}_mean_s": values.mean(),
        f"{prefix}_p50_s": np.percentile(values, 50),
        f"{prefix}_p90_s": np.percentile(values, 90),
        f"{prefix}_p95_s": np.percentile(values, 95),
    }


def summarize_run(records):
    """One row of metrics for a list of per-question result records."""
    df = pd.DataFrame(records)
    summary = {
        "questions": len(df),
        "EM": df.em.mean(),
        "F1": df.f1.mean(),
        "EM_bridge": df[df.type == "bridge"].em.mean(),
        "EM_comparison": df[df.type == "comparison"].em.mean(),
        "F1_bridge": df[df.type == "bridge"].f1.mean(),
        "F1_comparison": df[df.type == "comparison"].f1.mean(),
    }
    if "both_gold" in df and df.both_gold.notna().any():
        summary["evidence_recall"] = df.evidence_recall.mean()
        summary["both_gold_recall"] = df.both_gold.mean()
        summary["unsupported_rate"] = 1 - df.supported.mean()
    summary.update(
        {
            "avg_retrieval_calls": df.n_retrieval_calls.mean(),
            "avg_llm_calls": df.n_llm_calls.mean(),
            "avg_prompt_tokens": df.prompt_tokens.mean(),
            "avg_completion_tokens": df.completion_tokens.mean(),
            "avg_cost_usd": df.cost_usd.mean(),
            "cost_per_1k_questions_usd": df.cost_usd.mean() * 1000,
        }
    )
    summary.update(latency_stats(df.retrieval_latency_s, "retrieval_latency"))
    summary.update(latency_stats(df.llm_latency_s, "llm_latency"))
    summary.update(latency_stats(df.total_latency_s, "total_latency"))
    return summary
