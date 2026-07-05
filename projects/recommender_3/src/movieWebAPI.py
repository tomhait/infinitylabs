import aiohttp
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse
from .movie_provider import *
from contextlib import asynccontextmanager

class MovieWebAPI:
    """ Creates a Movie web API using FastAPI"""
    def __init__(self, base_dir: str = "./ml-latest-small", template_dir: str = "."):

        self.base_dir = Path(base_dir)
        self.templates = Jinja2Templates(directory=template_dir)
        self.template_name = "./src/movie_app.html"


        self.local_prov = LocalMovieProvider(self.base_dir)
        self.external_prov = ExternalMovieProvider()
        self.movie_service = MovieService(self.local_prov, self.external_prov)

        self._setup_events()

    def _setup_events(self):
        """Manage the aiohttp session lifecycle."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup logic
            self.session = aiohttp.ClientSession()
            self.external_prov.set_session(self.session)
            yield
            # Shutdown logic
            await self.session.close()

        self.app = FastAPI(lifespan=lifespan)
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
            movie = await self.movie_service.get_full_report(movie_title)

            if movie is None:
                return self.templates.TemplateResponse(self.template_name, {
                    "request": request,
                    "error_message": f"Could not find movie: {movie_title}",
                    "local": None,
                    "external": None
                })

            ratings = movie.get_all_ratings()

            return self.templates.TemplateResponse(self.template_name, {
                "request": request,
                "local": {
                    "title": movie.get_title(),
                    "year": movie.get_year(),
                    "average_rating": ratings['movielens']
                },
                "external": {
                    "title": movie.get_title(),
                    "year": movie.get_year(),
                    "average_rating": ratings['omdb'],
                    "Internet_Movie_Database": ratings['internet'],
                    "Rotten_Tomatoes": ratings['rotten'],
                    "Metacritic": ratings['metacritic'],
                    "poster_url": movie.get_poster_url()
                }
            })
