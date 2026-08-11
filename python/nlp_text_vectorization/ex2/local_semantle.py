import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from gensim.models import Word2Vec

MODEL = Path(__file__).resolve().parent.parent / "hebrew_w2v_download" / "model.mdl"
API = "https://semantle.ishefi.com/api/distance"


def is_hebrew(w):
    return len(w) >= 2 and all("א" <= c <= "ת" for c in w)


def api_ask(word, retries=5):
    url = f"{API}?word={urllib.parse.quote(word)}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "semantle-solver/1.0", "Accept": "application/json"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
            row = data[-1] if isinstance(data, list) else data
            s = row.get("similarity")
            if s is None:
                return None, -1
            return float(s), int(row.get("distance", -1))
        except urllib.error.HTTPError as e:
            if e.code >= 500 or e.code == 429:
                time.sleep(min(30, 2**attempt))
                continue
            return None, -1
        except Exception:
            time.sleep(min(30, 2**attempt))
    raise SystemExit("API unavailable")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--solve", action="store_true")
    p.add_argument("--top-n", type=int, default=0)
    p.add_argument("--sleep", type=float, default=0.2)
    p.add_argument("--max-guesses", type=int, default=100)
    args = p.parse_args()
    if not args.solve:
        p.error("use --solve")

    print("loading model...")
    kv = Word2Vec.load(str(MODEL)).wv
    keys = kv.index_to_key if args.top_n <= 0 else kv.index_to_key[: args.top_n]
    words = [w for w in keys if is_hebrew(w)]
    mat = np.stack([kv[w] for w in words]).astype(np.float64)
    mat /= np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    w2i = {w: i for i, w in enumerate(words)}
    print(f"candidates: {len(words):,}")
    print(f"API: {API}\n")

    used = set()
    hist_i, hist_s = [], []
    warm = []
    guess = words[len(words) // 2]
    neighbor_queue = []

    for step in range(1, args.max_guesses + 1):
        time.sleep(args.sleep)
        used.add(guess)
        s, r = api_ask(guess)
        if s is None:
            print(f"#{step} {guess} → unknown")
        else:
            print(f"#{step} {guess} sim={s} rank={r}")
            if r == 1000:
                print("found:", guess)
                return
            if guess in w2i:
                hist_i.append(w2i[guess])
                hist_s.append(s / 100.0)
            if r > 0:
                warm.append((r, guess))
                warm.sort(reverse=True)
                warm = warm[:10]
                for w, _ in kv.most_similar(guess, topn=40):
                    if is_hebrew(w) and w not in used and w not in neighbor_queue:
                        neighbor_queue.append(w)

        while neighbor_queue and neighbor_queue[0] in used:
            neighbor_queue.pop(0)
        if neighbor_queue:
            guess = neighbor_queue.pop(0)
            continue

        if not hist_i:
            guess = next(w for w in words if w not in used)
            continue

        G = mat[hist_i]
        target = np.asarray(hist_s)
        err = ((mat @ G.T - target) ** 2).sum(axis=1)
        for w in used:
            if w in w2i:
                err[w2i[w]] = np.inf
        guess = words[int(np.argmin(err))]

    print("gave up. best warm:", warm[:5])


if __name__ == "__main__":
    main()
