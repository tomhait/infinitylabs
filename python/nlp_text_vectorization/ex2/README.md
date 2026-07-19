# Hebrew Semantle (local)

Local Semantle game and solver using the same style of Hebrew word2vec model as [semantle.ishefi.com](https://semantle.ishefi.com).

## Setup

Needs **Python 3.10–3.12** (gensim does not build on 3.14).

```bash
python3.10 -m pip install gdown gensim numpy

mkdir -p hebrew_w2v_download
python3.10 -m gdown 'https://drive.google.com/uc?id=1ysGHa2XsqEzAcs-guFS-05b66bsdSwyU' \
  -O hebrew_w2v_download/wiki_tokenized_model.zip
cd hebrew_w2v_download && unzip -o wiki_tokenized_model.zip && cd ..
```

Model source: [hebrew-w2v](https://github.com/Iddoyadlin/hebrew-w2v) (same family as the online game).

## Usage

```bash
# play (random secret)
python3.10 local_semantle.py --play

# auto-solve
python3.10 local_semantle.py --solve
python3.10 local_semantle.py --solve --secret התרסקות

# candidate pool size (default 5000; 0 = all words in the model)
python3.10 local_semantle.py --solve --top-n 0
```

Score = `round(cosine × 100, 2)`. Rank in top-1000; **1000 means you found the secret**.

## Algorithm (exact-model constraints)

With the same embeddings as the scorer:

1. Guess a word \(g\) → get score \(s = \mathrm{sim}(g, \text{secret})\).
2. Keep only candidates \(c\) with \(\mathrm{sim}(c, g) = s\).
3. Guess again from what’s left.
4. Repeat until one word remains (or rank = 1000).

Usually **2–3 guesses**.

### Example: secret = `התרסקות`

```text
#1 פרשנות   sim=9.56   → left: {נחש, התרסקות}
#2 נחש      sim=15.6   → left: {התרסקות}
#3 התרסקות  sim=100    → found
```

If `--secret` is not in the `--top-n` pool, it is added automatically.
