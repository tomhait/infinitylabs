"""Loading HotpotQA, sampling a fixed development pool, and building the search corpus."""

import json
import os
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / "cache" / "hf"))

POOL_PATH = DATA_DIR / "dev_pool.jsonl"
CORPUS_PATH = DATA_DIR / "corpus.jsonl"
POOL_SIZE = 2000
SEED = 42


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def _to_record(ex):
    """Convert the Hugging Face columnar layout into a simpler per-example dict."""
    paragraphs = [
        {"title": t, "sentences": [s.strip() for s in sents]}
        for t, sents in zip(ex["context"]["title"], ex["context"]["sentences"])
    ]
    supporting = [
        {"title": t, "sent_id": i}
        for t, i in zip(ex["supporting_facts"]["title"], ex["supporting_facts"]["sent_id"])
    ]
    return {
        "id": ex["id"],
        "question": ex["question"],
        "answer": ex["answer"],
        "type": ex["type"],
        "level": ex["level"],
        "supporting_facts": supporting,
        "gold_titles": sorted({sf["title"] for sf in supporting}),
        "paragraphs": paragraphs,
    }


def load_split(split="validation"):
    from datasets import load_dataset

    ds = load_dataset("hotpotqa/hotpot_qa", "distractor", split=split)
    return [_to_record(ex) for ex in ds]


def load_dev_pool(n=POOL_SIZE, seed=SEED):
    """Fixed random sample of the validation split, cached to disk so every cycle uses the same questions."""
    if POOL_PATH.exists():
        return _read_jsonl(POOL_PATH)
    records = load_split("validation")
    pool = random.Random(seed).sample(records, n)
    _write_jsonl(POOL_PATH, pool)
    return pool


def paragraph_text(paragraph):
    return " ".join(paragraph["sentences"])


def contains_answer(paragraph, answer):
    from src.evaluate import normalize_answer

    ans = normalize_answer(answer)
    text = normalize_answer(paragraph["title"] + " " + paragraph_text(paragraph))
    return bool(ans) and f" {ans} " in f" {text} "


def bridge_hops(ex):
    """(hop1_title, hop2_title) for a bridge question: hop 2 is the only gold paragraph containing the answer.
    None when the answer appears in both or neither gold paragraph."""
    gold = [p for p in ex["paragraphs"] if p["title"] in ex["gold_titles"]]
    with_answer = [p for p in gold if contains_answer(p, ex["answer"])]
    if ex["type"] != "bridge" or len(with_answer) != 1:
        return None
    hop2 = with_answer[0]["title"]
    hop1 = next(p["title"] for p in gold if p["title"] != hop2)
    return hop1, hop2


def build_corpus(examples):
    """Union of all context paragraphs, deduplicated by title (Wikipedia titles are unique)."""
    corpus = {}
    for ex in examples:
        for p in ex["paragraphs"]:
            if p["title"] not in corpus:
                corpus[p["title"]] = {
                    "pid": len(corpus),
                    "title": p["title"],
                    "sentences": p["sentences"],
                    "text": paragraph_text(p),
                }
    return list(corpus.values())


def load_corpus(examples=None):
    if CORPUS_PATH.exists():
        return _read_jsonl(CORPUS_PATH)
    corpus = build_corpus(examples if examples is not None else load_dev_pool())
    _write_jsonl(CORPUS_PATH, corpus)
    return corpus
