from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

DATA = Path(__file__).resolve().parent
COLS = ["label", "title", "content", "answer"]
CV_SIZE = 150_000


def load(path: Path):
    df = pd.read_csv(path, header=None, names=COLS, keep_default_na=False)
    text = (df["title"] + " " + df["content"] + " " + df["answer"]).str.strip()
    return text, df["label"]


def tfidf():
    return TfidfVectorizer(min_df=2)

def tfidf_nb():
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2)

def report(name, y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    print(f"{name}: accuracy={acc * 100:.2f}%  error={(1 - acc) * 100:.2f}%")


def tune(name, pipe, param_grid, x, y):
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    search = GridSearchCV(
        pipe,
        param_grid=param_grid,
        cv=cv,
        scoring="accuracy",
        n_jobs=-1,
        refit=True,
        verbose=1,
    )
    search.fit(x, y)
    print(f"{name} CV best params: {search.best_params_}")
    print(f"{name} CV best score:  {search.best_score_ * 100:.2f}%")
    return search.best_params_


x_train, y_train = load(DATA / "train.csv")
x_test, y_test = load(DATA / "test.csv")

x_cv = x_train.sample(n=CV_SIZE, random_state=42)
y_cv = y_train.loc[x_cv.index]

configs = [
    (
        "zhang_tfidf_logreg",
        Pipeline(
            [
                ("tfidf", tfidf()),
                ("clf", LogisticRegression(solver="saga", max_iter=100, random_state=42)),
            ]
        ),
        {"clf__C": [0.5, 1.0, 2.0]},
    ),
    (
        "tfidf_nb",
        Pipeline([("tfidf", tfidf_nb()),
                  ("clf", MultinomialNB())]),
        {"clf__alpha": [0.1, 0.5, 1.0]},
    ),
]

for name, pipe, grid in configs:
    print(f"\n=== {name} ===")
    best = tune(name, pipe, grid, x_cv, y_cv)
    pipe.set_params(**best)
    print(f"Refitting {name} on full train ({len(y_train):,}) ...")
    pipe.fit(x_train, y_train)
    report(name, y_test, pipe.predict(x_test))
