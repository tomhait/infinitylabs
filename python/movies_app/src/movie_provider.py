import os
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv
from .movie import Movie
from .parsers import parse_movielens_data

load_dotenv()

__all__ = ("LocalMovieProvider", "ExternalMovieProvider", "MovieService")

class MovieProvider(ABC):
    """ Abstract base class for movie provider (e.g., OMDB)"""

    @abstractmethod
    def get_movie_data(self, movie):
        pass

class LocalMovieProvider(MovieProvider):
    """  Interface for the local dataset MovieLens"""
    def __init__(self, dir_path: Path):
        self.path = dir_path
        parsed_data = parse_movielens_data(self.path)
        self.df_ratings = parsed_data[0]
        self.df_movies = parsed_data[1]
        self.df_map = parsed_data[2]

    def get_movie_data(self, title: str):
        """ Returns a Movie instance with the local movie data"""
        match = self.df_movies[self.df_movies["title"].str.contains(title, case=False, regex=False)]
        if match.empty:
            return None
        match = match.iloc[0]
        movie_id = match["movieId"]
        movie_name = match["title"]
        avg_rating = self.df_ratings[self.df_ratings["movieId"] == movie_id]["rating"].mean()
        movie_imdb = self.df_map["imdbId"][self.df_map["movieId"]== str(movie_id)].iloc[0]
        movie = Movie.from_tuple((movie_name,movie_imdb))
        movie.movielens_rating = round(avg_rating, 2)
        movie.set_year(match['year'])
        return movie

    def get_movie_list(self, title):
        """ Returns list of 10 movies containing the title"""
        match = self.df_movies[self.df_movies["title"].str.contains(title, case=False, regex=False)]
        if match.empty:
            return []
        return match["title"].head(10).tolist()

class ExternalMovieProvider(MovieProvider):
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
                movie.omdb_rating = movie_json.get("imdbRating")
                movie.metascore_rating = movie_json.get("Metascore")
                movie.add_ratings(movie_json.get("Ratings"))
                movie.add_poster_url(movie_json.get("Poster"))
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