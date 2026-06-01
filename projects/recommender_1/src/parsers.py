import pandas as pd
from pathlib import Path

def parse_movielens_data(path: Path):
    """ Parses local MovieLens dataset"""
    df_ratings = pd.read_csv(path / "ratings.csv")
    df_movies = pd.read_csv(path / "movies.csv")
    df_map = pd.read_csv(path / "links.csv", dtype=str)
    df_map["imdbId"] = "tt" + df_map["imdbId"]
    df_movies["year"] = df_movies['title'].str.extract(r'\((\d{4})\)')
    df_movies['title'] = df_movies['title'].str.replace(r'\s*\(\d{4}\)', '', regex=True)
    df_movies["year"] = pd.to_numeric(df_movies["year"])
    return df_ratings, df_movies, df_map

