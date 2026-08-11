# Hebrew Semantle solver

Solves the daily word on [semantle.ishefi.com](https://semantle.ishefi.com).

## Setup

Python 3.10–3.12. Put the Hebrew word2vec model at `../hebrew_w2v_download/model.mdl`
([hebrew-w2v](https://github.com/Iddoyadlin/hebrew-w2v)):

```bash
python3.10 -m pip install gdown gensim numpy

cd ..
mkdir -p hebrew_w2v_download
python3.10 -m gdown 'https://drive.google.com/uc?id=1ysGHa2XsqEzAcs-guFS-05b66bsdSwyU' \
  -O hebrew_w2v_download/wiki_tokenized_model.zip
cd hebrew_w2v_download && unzip -o wiki_tokenized_model.zip
```

## Usage

```bash
cd ex2
python3.10 local_semantle.py --solve
python3.10 local_semantle.py --solve --top-n 30000 --max-guesses 100
```

`--top-n 0` (default) uses all Hebrew words in the model.

## Algorithm

1. Guess a word via `GET /api/distance?word=...` → similarity and rank (1000 = win).
2. Choose the next unused word whose local similarities to past guesses best match the API scores.
3. If a guess is in the top‑1000 (`rank > 0`), also try its nearest neighbors in the local model.

Example run:

```text
#1 אלגוריה   sim=49.32
#2 אינטימיות sim=43.06
#3 נפלאה     sim=56.32
#4 תענוג     sim=100.0  rank=1000
found: תענוג
```
