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

class MovieProvider(ABC):
    """ Abstract base class for movie provider (e.g., OMDB)"""

    @abstractmethod
    def get_movie_data(self, movie):
        pass


class Movie:
    """ Holds the Movie's metadata"""
    def __init__(self, title, id):
        self.title = title
        self.id = id
        self.year = "--"
        self.movielens_rating = "--"
        self.omdb_rating = "--"
        self.metascore = "--"
        self.int_movie_db = "--"
        self.rotten_tomatoes = "--"
        self.matacritic = "--"

    def add_movielens_rating(self, rating):
        self.movielens_rating = rating

    def add_omdb_rating(self, rating):
        self.omdb_rating = rating

    def add_metascore(self, metascore):
        self.metascore = metascore

    def add_ratings(self, ratings):
        """ Parses OMDb ratings"""
        for rate in ratings:
            if rate['Source'] == "Internet Movie Database":
                self.int_movie_db = rate.get("Value")
            elif rate['Source'] == "Rotten Tomatoes":
                self.rotten_tomatoes = rate.get("Value")
            elif rate['Source'] == "Metacritic":
                self.matacritic = rate.get("Value")


    def get_int_movie_rate(self):
        return self.int_movie_db

    def get_rotten_rate(self):
        return self.rotten_tomatoes

    def get_metacritic_rate(self):
        return self.matacritic

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
    """  Interface for the local dataset MovieLens"""
    def __init__(self, dir_path: Path):
        self.path = dir_path
        self._parse_data()

    def get_movie_data(self, title: str):
        """ Returns a Movie instance with the local movie data"""
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

    def _parse_data(self):
        """ Parses local MovieLens dataset"""
        self.df_ratings = pd.read_csv(self.path / "ratings.csv")
        self.df_movies = pd.read_csv(self.path / "movies.csv")
        self.df_map = pd.read_csv(self.path / "links.csv", dtype=str)
        self.df_map["imdbId"] = "tt" + self.df_map["imdbId"]
        self.df_movies["year"] = self.df_movies['title'].str.extract(r'\((\d{4})\)')
        self.df_movies['title'] = self.df_movies['title'].str.replace(r'\s*\(\d{4}\)', '', regex=True)
        self.df_movies["year"] = pd.to_numeric(self.df_movies["year"])

    def get_movie_list(self, title):
        """ Returns list of 10 movies containing the title"""
        match = self.df_movies[self.df_movies["title"].str.contains(title, case=False, regex=False)]
        if match.empty:
            return []
        return match["title"].head(10).tolist()


class ExternalMovieProvider(
    MovieProvider):
    """  Interface for remote OMDb API"""

    def __init__(self):
        self.api_key = os.getenv("MY_API_KEY")
        self.url = os.getenv("API_URL")

    def get_movie_data(self, movie: Movie):
        """ Updates a Movie instance with OMDb data"""
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
                movie.add_metascore(movie_json.get("Metascore"))
                movie.add_ratings(movie_json.get("Ratings"))
                movie.set_title(movie_json.get("Title"))
            else:
                print(f"Movie was not found: {movie_json.get('Error')}")
        except requests.exceptions.RequestException as e:
            print(f"API connection error: {e}")



class MovieService:
    """ Interface for collecting data from local and external databases"""
    def __init__(self, local_prov: MovieProvider, external_prov: MovieProvider):
        self.local_prov = local_prov
        self.external_prov = external_prov

    def get_full_report(self, title):
        """
        Combines data from local and external movie data
        and returns it as a Movie instance
        """
        movie = self.local_prov.get_movie_data(title)
        if movie is not None:
            self.external_prov.get_movie_data(movie)
        return movie


class MovieWebAPI:
    """ Creates a Movie web API using FastAPI"""
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
                    "average_rating": movie.get_omdb_rating(),
                    "Internet_Movie_Database": movie.get_int_movie_rate(),
                    "Rotten_Tomatoes": movie.get_rotten_rate(),
                    "Metacritic": movie.get_metacritic_rate()
                }
            })
