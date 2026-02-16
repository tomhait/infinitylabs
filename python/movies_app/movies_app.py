from abc import ABC, abstractmethod
import pandas as pd
import requests
from pathlib import Path
import httpx
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()  # This loads the variables from .env file

api_key = os.getenv("MY_API_KEY")

class MovieProvider(ABC):
    """ Abstract base class for movie provider (e.g., OMDB)"""

    @abstractmethod
    def get_movie_data(self, movie):
        pass


class Movie:
    def __init__(self, title, id):
        self.title = title
        self.year = "NA"
        self.id = id
        self.movielens_rating = "NA"
        self.omdb_rating = "NA"

    def add_movielens_rating(self, rating):
        self.movielens_rating = rating

    def add_omdb_rating(self, rating):
        self.omdb_rating = rating

    def set_title(self, title):
        self.title = title

    def get_imdb_id(self):
        return self.id

    def get_local_rating(self):
        return self.movielens_rating

    def get_omdb_rating(self):
        return self.omdb_rating

    def get_title(self):
        return self.title

    def set_year(self, year):
        self.year = int(year)

    def get_year(self):
        return self.year

    @classmethod
    def from_string(cls, title):
        return cls(title, "NA")

    @classmethod
    def from_tuple(cls, title_value):
        return cls(title_value[0], title_value[1])

# class IMDBMovies:
#     def __init__(self):
#         self._parse_data()
#
#     def _parse_data(self):
#         self.df_map = pd.read_table("imdbid_to_title.tsv", names=("imdb_id","title"))
#
#     def get_movie_list(self, title):
#         match = self.df_map[self.df_map["title"].str.contains(title, case=False, regex=False)]
#         if match.empty:
#             return []
#         return match["title"].head(10).tolist()
#
#     def get_movie_id(self, title):
#         match = self.df_map[self.df_map["title"].str.contains(title, case=False, regex=False)]
#         if match.empty:
#             return None
#         return match["imdb_id"].iloc[0]

class LocalMovieProvider(MovieProvider):
    """  Implements the interface for the local dataset MovieLens"""
    def __init__(self, dir_path: Path):
        self.path = dir_path
        self._parse_data()

    def get_movie_data(self, title: str):
        """ Returns a dict with movie name and average rating"""
        match = self.df_movies[self.df_movies["title"].str.contains(title, case=False, regex=False)]
        if match.empty:
            return None
        movie_id = match.iloc[0]["movieId"]
        movie_name = match.iloc[0]["title"]
        avg_rating = self.df_ratings[self.df_ratings["movieId"] == movie_id]["rating"].mean()
        movie_imdb = self.df_map["imdbId"][self.df_map["movieId"]== str(movie_id)].iloc[0]
        movie = Movie.from_tuple((movie_name,movie_imdb))
        movie.add_movielens_rating(round(avg_rating, 2))
        movie.set_year(match.iloc[0]['year'])
        return movie

    def get_id(self):
        pass

    def _parse_data(self):
        self.df_ratings = pd.read_csv(self.path / "ratings.csv")
        self.df_movies = pd.read_csv(self.path / "movies.csv")
        self.df_map = pd.read_csv(self.path / "links.csv", dtype=str)
        self.df_map["imdbId"] = "tt" + self.df_map["imdbId"]
        self.df_movies["year"] = self.df_movies['title'].str.extract(r'\((\d{4})\)')
        self.df_movies['title'] = self.df_movies['title'].str.replace(r'\s*\(\d{4}\)', '', regex=True)
        self.df_movies["year"] = pd.to_numeric(self.df_movies["year"])

    def get_movie_list(self, title):
        match = self.df_movies[self.df_movies["title"].str.contains(title, case=False, regex=False)]
        if match.empty:
            return []
        return match["title"].head(10).tolist()


class ExternalMovieProvider(
    MovieProvider):
    """  Implements the interface for the remote OMDB API"""

    def __init__(self, API_URL="https://www.omdbapi.com/"):
        self.api_key = api_key
        self.url = API_URL

    def get_movie_data(self, movie: Movie):
        """ Returns a dict with movie name and average rating"""
        params = {
            'apikey': self.api_key,
            'i': movie.get_imdb_id()
        }
        try:
            response = requests.get(self.url, params=params)
            response.raise_for_status()
            movie_json = response.json()
            if movie_json.get("Response"):
                movie.add_omdb_rating(movie_json.get("imdbRating"))
                movie.set_title(movie_json.get("Title"))
            else:
                print(f"Movie was not found: {movie_json.get('Error')}")
        except requests.exceptions.RequestException as e:
            print(f"API connection error: {e}")



class MovieService:
    def __init__(self, local_prov: MovieProvider, external_prov: MovieProvider):
        self.local_prov = local_prov
        self.external_prov = external_prov
        # self.imdb_movies = IMDBMovies()

    def get_full_report(self, title):
        """ Combines data from local and external movie data and returns it as dict"""
        movie = self.local_prov.get_movie_data(title)
        if movie:
            self.external_prov.get_movie_data(movie)
        return movie

    # def get_movie_list(self, title):
    #     return self.imdb_movies.get_movie_list(title)
# app = FastAPI()
# templates = Jinja2Templates(directory=".")
#
# class MovieWebAPI:
#     """ A client to interact with local and external movie data"""
#     template_name = "movie_app.html"
#
#     def __init__(self, api_key: str, movie_service: MovieService):
#         self.api_key = api_key
#         self.movie_service = movie_service
#
#     def get_by_title(self, title: str):
#         data = self.movie_service.get_full_report(title)
#
#

