# Word2Vec on WikiText-103

Skip-gram word2vec with negative sampling in PyTorch, trained on [WikiText-103](https://blog.salesforceairesearch.com/the-wikitext-long-term-dependency-language-modeling-dataset/). Embeddings are evaluated with nearest neighbors and linguistic regularities (vector offset method from [Mikolov et al., N13-1090](https://aclanthology.org/N13-1090/)).

## Usage

```bash
python word2vec.py --train   # train, save word2vec.pt, then evaluate
python word2vec.py --load    # load word2vec.pt and evaluate only
```

Uses Apple MPS when available, otherwise CPU.

## Hyperparameters

| Setting | Value |
|---------|-------|
| Corpus | WikiText-103 train (full) |
| Min count | 10 |
| Embedding dim | 100 |
| Window | 5 |
| Negatives | 5 |
| Epochs | 5 |
| Batch size | 4096 |
| Learning rate | 1e-3 |

## Results

```
Device: mps
vocab=115,519  pairs=986,394,610
epoch 1/5  loss=2.5848
epoch 2/5  loss=2.2554
epoch 3/5  loss=2.2466
epoch 4/5  loss=2.2449
epoch 5/5  loss=2.2449
```

### Classic analogy: king − man + woman ≈ queen

```
man:king :: woman:? -> queen, regent, consort, empress, prince ✓
```

### Nearest neighbors

| Query | Neighbors |
|-------|-----------|
| king | prince, throne, confessor, ætheling, nephew |
| paris | brussels, vienna, amsterdam, berlin, france |
| computer | computers, software, simulation, handheld, mainframe |
| music | musical, pop, jazz, song, songs |

### Linguistic regularities (N13-1090 vector offset)

Expected word in top-5: **18 / 24**

#### Syntactic — adjective comparative

| Analogy | Top hits | |
|---------|----------|--|
| good:better :: rough:? | safer, deeper, harder, terrain, smoother | want *rougher* |
| fast:faster :: strong:? | stronger, weaker, moderate, greater, higher | ✓ |
| big:bigger :: small:? | larger, smaller, large, thicker, wider | ✓ |

#### Syntactic — adjective superlative

| Analogy | Top hits | |
|---------|----------|--|
| good:best :: bad:? | worst, sexiest, greatest, awards, award | ✓ |
| great:greatest :: large:? | largest, component, most, smallest, fraction | ✓ |

#### Syntactic — noun plural

| Analogy | Top hits | |
|---------|----------|--|
| year:years :: law:? | laws, legal, jurisprudence, unconstitutional, segregation | ✓ |
| car:cars :: apple:? | apps, intel, vendors, peripherals, processors | want *apples* |
| man:men :: woman:? | women, unmarried, officers, wives, soldiers | ✓ |
| mouse:mice :: child:? | children, infant, mothers, infants, unborn | ✓ |

#### Syntactic — verb past tense

| Analogy | Top hits | |
|---------|----------|--|
| walk:walked :: dance:? | dancing, dancers, danced, dances, sang | ✓ |
| see:saw :: return:? | returned, ended, returning, following, stint | ✓ |
| go:went :: take:? | took, taking, came, proceeded, gave | ✓ |
| sing:sang :: swim:? | swimming, swam, skate, swimmers, pools | ✓ |

#### Syntactic — verb 3rd person

| Analogy | Top hits | |
|---------|----------|--|
| walk:walks :: speak:? | speaks, fluently, fluent, spoke, spoken | ✓ |
| see:sees :: return:? | returns, abandons, returning, departure, escapes | ✓ |

#### Semantic — gender

| Analogy | Top hits | |
|---------|----------|--|
| man:king :: woman:? | queen, regent, consort, empress, prince | ✓ |
| man:actor :: woman:? | actress, dancer, streep, singer, playwright | ✓ |
| brother:sister :: uncle:? | daughter, niece, aunt, grandmother, mother | ✓ |
| he:she :: his:? | her, herself, husband, hers, 's | ✓ |

#### Semantic — capital city

| Analogy | Top hits | |
|---------|----------|--|
| france:paris :: italy:? | prague, vienna, berlin, stockholm, zürich | want *rome* |
| japan:tokyo :: china:? | shanghai, guangzhou, taipei, bangkok, beijing | ✓ |
| germany:berlin :: spain:? | seville, paris, córdoba, amsterdam, venice | want *madrid* |

#### Semantic — currency

| Analogy | Top hits | |
|---------|----------|--|
| usa:dollar :: japan:? | japanese, coins, coin, kyushu, currency | want *yen* |
| uk:pound :: europe:? | pounds, kg, ezra, greco, kilograms | want *euro* |

## Notes

- The classic gender analogy lands correctly: **queen** is the nearest neighbor of `king − man + woman`.
- Syntactic morphology (plurals, verb tense, comparatives) is mostly captured.
- Some semantic geography/currency analogies miss the exact target but stay in a related semantic neighborhood (other capitals, money-related words).
