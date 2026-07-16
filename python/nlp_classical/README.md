# Yahoo! Answers Topic Classification (Classical NLP)

Classical (non–deep learning) baselines for the **Yahoo! Answers Topic Classification** dataset from Zhang, Zhao & LeCun (NeurIPS 2015): [*Character-level Convolutional Networks for Text Classification*](https://arxiv.org/abs/1509.01626).

## Dataset

| Split | Size |
|-------|------|
| Train | 1,400,000 |
| Test  | 60,000 |
| Classes | 10 topics |

Each example uses **question title + question content + best answer**, concatenated into one document (Zhang protocol). Labels are integers `1`–`10`.
Zhang et al paper: https://arxiv.org/pdf/1509.01626

## Methods

| Model | Features                                    | Classifier | Notes |
|-------|---------------------------------------------|------------|--------|
| Zhang-style baseline | Word unigram TF-IDF (`max_features=50,000`) | Multinomial logistic regression (`saga`) | Closest to their BoW-TF-IDF + logistic regression setup |
| TF-IDF + Naive Bayes | Word TF-IDF (optional n-grams up to 2)      | Multinomial Naive Bayes | Same style of features; only the classifier changes |

Hyperparameters (`C` for LR, `alpha` for NB) can be chosen with **stratified 3-fold GridSearchCV** on a 150k training subsample, then models are **refit on the full** training set and evaluated once on the official test set.

Metric: **test accuracy** (and error % = `100 − accuracy`), comparable to Zhang’s tables.

## Results (official test set)

| Model |    Accuracy |  Error |
|-------|------------:|-------:|
| TF-IDF + Logistic Regression | **72.454%** | 27.46% |
| TF-IDF + Multinomial NB |  **71.56%** | 28.44% |

## How to run

```bash
python3 train.py
```

## Output
```=== zhang_tfidf_logreg ===
Fitting 3 folds for each of 3 candidates, totalling 9 fits
zhang_tfidf_logreg CV best params: {'clf__C': 1.0}
zhang_tfidf_logreg CV best score:  69.10%
Refitting zhang_tfidf_logreg on full train (1,400,000) ...
zhang_tfidf_logreg: accuracy=72.54%  error=27.46%
```
```=== tfidf_nb ===
Fitting 3 folds for each of 3 candidates, totalling 9 fits
tfidf_nb CV best params: {'clf__alpha': 0.1}
tfidf_nb CV best score:  68.45%
Refitting tfidf_nb on full train (1,400,000) ...
tfidf_nb: accuracy=71.56%  error=28.44%
```