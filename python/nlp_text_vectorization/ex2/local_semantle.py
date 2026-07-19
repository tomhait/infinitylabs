import argparse
import random
from pathlib import Path

import numpy as np
from gensim.models import Word2Vec

MODEL = Path(__file__).parent / "hebrew_w2v_download" / "model.mdl"


def sim(a, b):
    return round(float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))) * 100, 2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--play", action="store_true")
    p.add_argument("--solve", action="store_true")
    p.add_argument("--secret", default=None)
    p.add_argument("--top-n", type=int, default=5000, help="candidate pool size; 0 = all words")
    args = p.parse_args()

    print("loading model...")
    kv = Word2Vec.load(str(MODEL)).wv
    if args.top_n <= 0:
        words = [w for w in kv.index_to_key if len(w) >= 2]
    else:
        words = [w for w in kv.index_to_key[: args.top_n] if len(w) >= 2]
    print(f"candidates: {len(words):,}")

    if args.secret:
        secret = args.secret
        if secret not in kv:
            raise SystemExit(f"secret {secret!r} not in model")
        if secret not in words:
            words.append(secret)
            print("secret was missing from pool, added")
    else:
        secret = random.choice(words[50:])

    svec = kv[secret]
    vecs = {w: kv[w] for w in words}

    nearest = sorted(words, key=lambda w: -sim(svec, vecs[w]))[:1000]
    rank = {w: i + 1 for i, w in enumerate(reversed(nearest))}

    def ask(w):
        if w not in kv:
            return None, -1
        return sim(svec, kv[w]), rank.get(w, -1)

    if args.play:
        n = 0
        while True:
            g = input("> ").strip()
            if g in ("q", "quit", "exit"):
                print("secret:", secret)
                break
            s, r = ask(g)
            if s is None:
                print("unknown")
                continue
            n += 1
            print(f"#{n} sim={s} rank={r}")
            if r == 1000:
                print("found in", n)
                break
        return

    if args.solve:
        left = set(words)
        used = set()
        guess = words[len(words) // 2]
        print("exact-model constraint: keep words with the same score to each guess\n")
        for step in range(1, 25):
            used.add(guess)
            s, r = ask(guess)
            print(f"#{step} {guess} sim={s} rank={r} left={len(left)}")
            if r == 1000:
                print("found:", guess)
                return
            left = {w for w in left if w not in used and sim(vecs[guess], vecs[w]) == s}
            if secret not in left and secret not in used:
                print("bug: secret dropped from candidates")
                return
            if not left:
                print("empty")
                return
            if len(left) <= 10:
                print(" ", left)
            guess = next(iter(left))
        print("gave up, secret:", secret)


if __name__ == "__main__":
    main()
