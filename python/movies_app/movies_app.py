import os
import pandas as pd
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

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
        if movie is not None:
            self.external_prov.get_movie_data(movie)
        return movie


class MovieWebAPI:
    def __init__(self, base_dir: str = "./ml-latest-small", template_dir: str = "."):

        self.base_dir = Path(base_dir)
        self.templates = Jinja2Templates(directory=template_dir)
        self.template_name = "movie_app.html"


        self.local_prov = LocalMovieProvider(self.base_dir)
        self.external_prov = ExternalMovieProvider()
        self.movie_service = MovieService(self.local_prov, self.external_prov)


        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self):
        """Define routes within the class context."""

        @self.app.get("/search-movies")
        async def search_movies(q: str = Query(..., min_length=2)):
            titles = self.local_prov.get_movie_list(q)
            return [{"title": t} for t in titles]

        @self.app.get("/", response_class=HTMLResponse)
        async def get_form(request: Request):
            return self.templates.TemplateResponse(self.template_name, {
                "request": request,
                "local": None,
                "external": None
            })

        @self.app.post("/submit", response_class=HTMLResponse)
        async def post_form(request: Request, movie_title: str = Form(...)):
            movie = self.movie_service.get_full_report(movie_title)

            if movie is None:
                return self.templates.TemplateResponse(self.template_name, {
                    "request": request,
                    "error_message": f"Could not find movie: {movie_title}",
                    "local": None,
                    "external": None
                })

            return self.templates.TemplateResponse(self.template_name, {
                "request": request,
                "local": {
                    "title": movie.get_title(),
                    "year": movie.get_year(),
                    "average_rating": movie.get_local_rating()
                },
                "external": {
                    "title": movie.get_title(),
                    "year": movie.get_year(),
                    "average_rating": movie.get_omdb_rating()
                }
            })
