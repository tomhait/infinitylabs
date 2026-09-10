#!/usr/bin/env python3
"""
Reproduce the winning FiQA retriever:

  hybrid_rrf_splade_bge + BAAI/bge-reranker-v2-m3 (top-50)

Requires prebuilt artifacts from the project:
  - artifacts/splade_cocondenser_ensembledistil/doc_embeddings.npz
  - artifacts/dense_sota_small/bge_small_en_v1_5/doc_embeddings.npy

Usage:
  # single query
  python reproduce_champion.py --query "What is an ETF?"

  # interactive REPL
  python reproduce_champion.py --interactive

  # evaluate on a qrels split (dev|test)
  python reproduce_champion.py --eval-split test
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sentence_transformers import CrossEncoder, SentenceTransformer, SparseEncoder

ROOT = Path(__file__).resolve().parent
SPLADE_ART = ROOT / "artifacts" / "splade_cocondenser_ensembledistil"
BGE_ART = ROOT / "artifacts" / "dense_sota_small" / "bge_small_en_v1_5"

SPLADE_MODEL = "naver/splade-cocondenser-ensembledistil"
BGE_MODEL = "BAAI/bge-small-en-v1.5"
BGE_QPREFIX = "Represent this sentence for searching relevant passages: "
CE_MODEL = "BAAI/bge-reranker-v2-m3"

K_RRF = 30
W_SPLADE = 1.0
W_BGE = 2.0
POOL_K = 100
RERANK_K = 50
TOP_K = 10


def pick_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def rrf_fuse(rankings, weights, k_rrf, top_n):
    scores = defaultdict(float)
    for ranking, w in zip(rankings, weights):
        for rank, doc_id in enumerate(ranking, 1):
            scores[doc_id] += w / (k_rrf + rank)
    return [d for d, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:top_n]]


def topk_from_scores(scores: np.ndarray, doc_ids: list[str], k: int) -> list[str]:
    if k >= len(scores):
        idx = np.argsort(-scores)
    else:
        part = np.argpartition(-scores, kth=k)[:k]
        idx = part[np.argsort(-scores[part])]
    return [doc_ids[i] for i in idx]


def recall_at_k(ranked, relevant, k):
    if not relevant:
        return 0.0
    return len(set(ranked[:k]) & relevant) / len(relevant)


def mrr_at_k(ranked, relevant, k):
    for i, doc_id in enumerate(ranked[:k], 1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked, relevant, k):
    if not relevant:
        return 0.0
    dcg = sum(1.0 / np.log2(i + 1) for i, d in enumerate(ranked[:k], 1) if d in relevant)
    ideal = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 1) for i in range(1, ideal + 1))
    return dcg / idcg if idcg else 0.0


class ChampionRetriever:
    """SPLADE + BGE weighted RRF, then BGE-reranker-v2-m3 on top-50."""

    def __init__(self, device: str | None = None):
        self.device = device or pick_device()
        print(f"Loading models on {self.device}…")

        corpus = pd.read_parquet(ROOT / "fiqa/corpus/corpus-00000-of-00001.parquet")
        corpus["_id"] = corpus["_id"].astype(str)
        corpus["text"] = corpus["text"].fillna("").astype(str).str.strip()
        self.doc_ids = corpus["_id"].tolist()
        self.docs_by_id = corpus.set_index("_id")["text"].to_dict()

        self.splade = SparseEncoder(SPLADE_MODEL, device=self.device)
        self.doc_csr = sparse.load_npz(SPLADE_ART / "doc_embeddings.npz").tocsr()
        assert self.doc_csr.shape[0] == len(self.doc_ids)

        self.bge = SentenceTransformer(BGE_MODEL, device=self.device)
        self.bge_emb = np.load(BGE_ART / "doc_embeddings.npy").astype(np.float32)
        assert self.bge_emb.shape[0] == len(self.doc_ids)

        self.ce = CrossEncoder(CE_MODEL, device=self.device, max_length=512)
        print("Ready.")

    def retrieve(self, query: str, top_k: int = TOP_K, rerank_k: int = RERANK_K, pool_k: int = POOL_K):
        # SPLADE
        q_sp = (
            self.splade.encode_query(
                [query],
                convert_to_tensor=True,
                convert_to_sparse_tensor=False,
                show_progress_bar=False,
            )
            .detach()
            .float()
            .cpu()
            .numpy()
            .ravel()
        )
        splade_cands = topk_from_scores(self.doc_csr @ q_sp, self.doc_ids, pool_k)

        # BGE
        q_bge = self.bge.encode(
            [BGE_QPREFIX + query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        bge_cands = topk_from_scores(self.bge_emb @ q_bge, self.doc_ids, pool_k)

        # Hybrid RRF
        hybrid = rrf_fuse(
            [splade_cands, bge_cands],
            [W_SPLADE, W_BGE],
            K_RRF,
            pool_k,
        )

        # CE rerank
        cands = hybrid[:rerank_k]
        pairs = [(query, self.docs_by_id[d]) for d in cands]
        scores = self.ce.predict(pairs, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
        order = np.argsort(-np.asarray(scores))
        ranked = [cands[i] for i in order]
        ranked = ranked + [d for d in hybrid if d not in set(ranked)]

        results = []
        for i, doc_id in enumerate(ranked[:top_k], 1):
            results.append(
                {
                    "rank": i,
                    "doc_id": doc_id,
                    "text": self.docs_by_id[doc_id],
                    "ce_score": float(scores[cands.index(doc_id)]) if doc_id in cands else None,
                }
            )
        return results


def eval_split(retriever: ChampionRetriever, split: str):
    queries = pd.read_parquet(ROOT / "fiqa/queries/queries-00000-of-00001.parquet")
    queries["_id"] = queries["_id"].astype(str)
    queries["text"] = queries["text"].fillna("").astype(str).str.strip()
    qmap = queries.set_index("_id")["text"].to_dict()

    qrels = pd.read_csv(ROOT / "fiqa-qrels" / f"{split}.tsv", sep="\t")
    qrels["query-id"] = qrels["query-id"].astype(str)
    qrels["corpus-id"] = qrels["corpus-id"].astype(str)
    qrels_map = qrels.groupby("query-id")["corpus-id"].apply(set).to_dict()

    rows = []
    t0 = time.perf_counter()
    for qid, rel in qrels_map.items():
        hits100 = retriever.retrieve(qmap[qid], top_k=100)
        ranked = [h["doc_id"] for h in hits100]
        rows.append(
            {
                "query_id": qid,
                "recall@10": recall_at_k(ranked, rel, 10),
                "mrr@10": mrr_at_k(ranked, rel, 10),
                "ndcg@10": ndcg_at_k(ranked, rel, 10),
                "recall@100": recall_at_k(ranked, rel, 100),
            }
        )
    elapsed = time.perf_counter() - t0
    pq = pd.DataFrame(rows)
    summary = {c: float(pq[c].mean()) for c in pq.columns if c != "query_id"}
    summary["n_queries"] = len(pq)
    summary["elapsed_s"] = elapsed
    print(json.dumps({"split": split, **summary}, indent=2))
    return summary


def print_hits(query: str, hits: list[dict]) -> None:
    print("Query:", query)
    for hit in hits:
        preview = hit["text"][:240].replace("\n", " ")
        ce = hit["ce_score"]
        ce_s = f"{ce:.4f}" if ce is not None else "n/a"
        print(f"[{hit['rank']}] id={hit['doc_id']} ce={ce_s}\n    {preview}…\n")


def interactive_loop(retriever: ChampionRetriever, top_k: int) -> None:
    print("Interactive mode. Empty line or 'quit' to exit.")
    while True:
        try:
            query = input("query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query or query.lower() in {"q", "quit", "exit"}:
            break
        t0 = time.perf_counter()
        hits = retriever.retrieve(query, top_k=top_k)
        print(f"(latency {time.perf_counter() - t0:.2f}s)")
        print_hits(query, hits)


def main():
    parser = argparse.ArgumentParser(description="Reproduce FiQA champion retriever")
    parser.add_argument("--query", type=str, default=None, help="Run a single query")
    parser.add_argument("--interactive", action="store_true", help="REPL until quit")
    parser.add_argument("--top-k", type=int, default=TOP_K)
    parser.add_argument("--eval-split", choices=["dev", "test"], default=None)
    parser.add_argument("--device", type=str, default=None)
    args = parser.parse_args()

    missing = [
        p
        for p in (
            SPLADE_ART / "doc_embeddings.npz",
            BGE_ART / "doc_embeddings.npy",
            ROOT / "fiqa/corpus/corpus-00000-of-00001.parquet",
        )
        if not p.exists()
    ]
    if missing:
        raise SystemExit(
            "Missing artifacts/data:\n"
            + "\n".join(f"  - {p}" for p in missing)
            + "\nBuild indexes via scripts/run_stage6b_splade.py (SPLADE) "
            "and stage6a BGE encode first."
        )

    retriever = ChampionRetriever(device=args.device)

    if args.eval_split:
        eval_split(retriever, args.eval_split)
        return

    if args.interactive:
        interactive_loop(retriever, args.top_k)
        return

    query = args.query or "What is the difference between an ETF and a mutual fund?"
    print_hits(query, retriever.retrieve(query, top_k=args.top_k))


if __name__ == "__main__":
    main()
