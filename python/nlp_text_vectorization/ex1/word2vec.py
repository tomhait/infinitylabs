import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).parent
CORPUS = ROOT / "wikitext-103" / "wiki.train.tokens"
SAVE_PATH = ROOT / "word2vec.pt"
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# Hyperparams
MAX_TOKENS = None  # set None for full corpus
MIN_COUNT, EMBED_DIM, WINDOW, NEGATIVES = 10, 100, 5, 5
EPOCHS, BATCH_SIZE, LR = 5, 4096, 1e-3


def load_ids(path: Path, min_count: int, max_tokens: int | None):
    tokens = []
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line or (line.startswith("=") and line.endswith("=")):
            continue
        tokens.extend(w.lower() for w in line.split())
        if max_tokens and len(tokens) >= max_tokens:
            tokens = tokens[:max_tokens]
            break

    counts = Counter(tokens)
    words = [w for w, c in counts.most_common() if c >= min_count]
    w2i = {w: i for i, w in enumerate(words)}
    ids = np.array([w2i[t] for t in tokens if t in w2i], dtype=np.int64)
    freqs = np.array([counts[w] for w in words], dtype=np.float64)
    noise = freqs ** 0.75
    noise /= noise.sum()
    return ids, words, w2i, noise


def make_pairs(ids: np.ndarray, window: int):
    centers, contexts = [], []
    for i, c in enumerate(ids):
        for j in range(max(0, i - window), min(len(ids), i + window + 1)):
            if j != i:
                centers.append(c)
                contexts.append(ids[j])
    return np.array(centers), np.array(contexts)


class SkipGram(nn.Module):
    def __init__(self, vocab: int, dim: int):
        super().__init__()
        self.in_emb = nn.Embedding(vocab, dim)
        self.out_emb = nn.Embedding(vocab, dim)

    def forward(self, center, context, neg):
        v = self.in_emb(center)
        pos = (v * self.out_emb(context)).sum(1)
        neg_s = torch.bmm(self.out_emb(neg), v.unsqueeze(2)).squeeze(2)
        return -(F.logsigmoid(pos) + F.logsigmoid(-neg_s).sum(1)).mean()


def analogy(vecs, words, w2i, a, b, c, expected=None, k=5):
    """Vector offset (N13-1090): a:b :: c:?  →  b - a + c."""
    for w in (a, b, c):
        if w not in w2i:
            print(f"  {a}:{b} :: {c}:?  (missing {w!r})")
            return False
    target = F.normalize(vecs[w2i[b]] - vecs[w2i[a]] + vecs[w2i[c]], dim=0)
    sims = vecs @ target
    for w in (a, b, c):
        sims[w2i[w]] = -1
    top = sims.topk(k)
    hits = [words[i] for i in top.indices.tolist()]
    mark = ""
    if expected:
        mark = " ✓" if expected in hits else f" (want {expected})"
    print(f"  {a}:{b} :: {c}:? -> {', '.join(hits)}{mark}")
    return expected in hits if expected else True


REGULARITIES = {
    "syntactic — adjective comparative": [
        ("good", "better", "rough", "rougher"),
        ("fast", "faster", "strong", "stronger"),
        ("big", "bigger", "small", "smaller"),
    ],
    "syntactic — adjective superlative": [
        ("good", "best", "bad", "worst"),
        ("great", "greatest", "large", "largest"),
    ],
    "syntactic — noun plural": [
        ("year", "years", "law", "laws"),
        ("car", "cars", "apple", "apples"),
        ("man", "men", "woman", "women"),
        ("mouse", "mice", "child", "children"),
    ],
    "syntactic — verb past tense": [
        ("walk", "walked", "dance", "danced"),
        ("see", "saw", "return", "returned"),
        ("go", "went", "take", "took"),
        ("sing", "sang", "swim", "swam"),
    ],
    "syntactic — verb 3rd person": [
        ("walk", "walks", "speak", "speaks"),
        ("see", "sees", "return", "returns"),
    ],
    "semantic — gender": [
        ("man", "king", "woman", "queen"),
        ("man", "actor", "woman", "actress"),
        ("brother", "sister", "uncle", "aunt"),
        ("he", "she", "his", "her"),
    ],
    "semantic — capital city": [
        ("france", "paris", "italy", "rome"),
        ("japan", "tokyo", "china", "beijing"),
        ("germany", "berlin", "spain", "madrid"),
    ],
    "semantic — currency": [
        ("usa", "dollar", "japan", "yen"),
        ("uk", "pound", "europe", "euro"),
    ],
}


def show_regularities(vecs, words, w2i):
    print("\nLinguistic regularities (vector offset, N13-1090):")
    ok = total = 0
    for name, items in REGULARITIES.items():
        print(f"\n{name}")
        for a, b, c, expected in items:
            total += 1
            if analogy(vecs, words, w2i, a, b, c, expected=expected):
                ok += 1
    print(f"\nexpected word in top-5: {ok}/{total}")


def evaluate(vecs, words, w2i):
    print("\nClassic test: king - man + woman ≈ queen")
    analogy(vecs, words, w2i, "man", "king", "woman", expected="queen")

    print("\nNearest neighbors:")
    for q in ["king", "paris", "computer", "music"]:
        if q not in w2i:
            continue
        sims = vecs @ vecs[w2i[q]]
        sims[w2i[q]] = -1
        print(q, "->", [words[i] for i in sims.topk(5).indices.tolist()])
    show_regularities(vecs, words, w2i)


def train():
    ids, words, w2i, noise = load_ids(CORPUS, MIN_COUNT, MAX_TOKENS)
    centers, contexts = make_pairs(ids, WINDOW)
    print(f"vocab={len(words):,}  pairs={len(centers):,}")

    model = SkipGram(len(words), EMBED_DIM).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=LR)

    for epoch in range(1, EPOCHS + 1):
        perm = np.random.permutation(len(centers))
        total, n = 0.0, 0
        for i in range(0, len(perm) - BATCH_SIZE, BATCH_SIZE):
            idx = perm[i : i + BATCH_SIZE]
            c = torch.tensor(centers[idx], device=DEVICE)
            ctx = torch.tensor(contexts[idx], device=DEVICE)
            neg = torch.tensor(
                np.random.choice(len(noise), (BATCH_SIZE, NEGATIVES), p=noise),
                device=DEVICE,
            )
            loss = model(c, ctx, neg)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
            n += 1
        print(f"epoch {epoch}/{EPOCHS}  loss={total / n:.4f}")

    emb = model.in_emb.weight.detach().cpu()
    torch.save({"words": words, "w2i": w2i, "emb": emb}, SAVE_PATH)
    print(f"saved {SAVE_PATH}")
    return F.normalize(emb.to(DEVICE), dim=1), words, w2i


def load_saved():
    ckpt = torch.load(SAVE_PATH, map_location=DEVICE, weights_only=False)
    words, w2i, emb = ckpt["words"], ckpt["w2i"], ckpt["emb"].to(DEVICE)
    print(f"loaded {SAVE_PATH}  vocab={len(words):,}")
    return F.normalize(emb, dim=1), words, w2i


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--train", action="store_true", help="train and save word2vec.pt")
    g.add_argument("--load", action="store_true", help="load word2vec.pt (no training)")
    args = p.parse_args()

    print(f"Device: {DEVICE}")
    if args.train:
        vecs, words, w2i = train()
    else:
        vecs, words, w2i = load_saved()
    evaluate(vecs, words, w2i)


if __name__ == "__main__":
    main()
