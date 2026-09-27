"""Official-style HotpotQA answer metrics (exact match and token F1)."""

import re
import string
from collections import Counter


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
