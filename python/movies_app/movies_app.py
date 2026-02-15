from abc import ABC, abstractmethod
import pandas as pd
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path


class MovieProvider(ABC):
    """ Abstract base class for movie provider (e.g., OMDB)"""

    @abstractmethod
    def get_movie_data(self, title: str) -> dict:
        pass


class LocalMovieProvider(MovieProvider):
    """  Implements the interface for the local dataset MovieLens"""  # (David): Perhaps more general for local datasets. Further subclass for Movielens.

    def __init__(self, dir_path: Path):
        self.path = dir_path
        self._parse_data()

    def get_movie_data(self, title: str):  # use pandas to parse the file
        """ Returns a dict with movie name and average rating"""
        match = self.df_items[self.df_items["movie_name"].str.contains(title, case=False)]
        if match.empty:
            return {"error": "Movie not found"}
        movie_id = match.index[0]
        movie_name = match.iloc[0]["movie_name"]
        avg_rating = self.df_ratings[self.df_ratings["item_id"] == movie_id]["rating"].mean()
        return {
            "title": movie_name,
            "average_rating": round(avg_rating, 2)
        }


    def _parse_data(self):
        self.df_ratings = pd.read_table(self.path / 'u.data', header=None,
                                   names=("user_id", "item_id", "rating", "timestamp"))
        self.df_items = pd.read_csv(self.path / 'u.item', header = None,
                       sep="|", usecols=[0, 1], encoding = 'latin-1',
                       index_col = 0, names = ("movie_id","movie_name"))


class ExternalMovieProvider(
    MovieProvider):  # (David): maybe call this ExternalMovieProvider for consistency. Need have subclasses per resource?
    """  Implements the interface for the remote OMDB API"""

    def __init__(self, api_key, API_URL):
        pass

    def get_movie_data(self, title: str):
        """ Returns a dict with movie name and average rating"""

    pass


class MovieService:
    def __init__(self, local_prov: MovieProvider, external_prov: MovieProvider):
        pass

    def get_full_report(self, title):
        """ Combines data from local and external movie data and returns it as dict"""

    pass


class MovieWebAPI:
    """ A client to interact with local and external movie data"""
    #app = FastAPI()
    #templates = Jinja2Templates(directory=".")

    def __init__(self, api_key: str, movie_service: MovieService):
        self.api_key = api_key
        self.movie_service = movie_service

    def get_by_title(self, title: str):

