import pandas as pd
from movies_app import *
from pathlib import Path
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path("./ml-latest-small")

app = FastAPI()
templates = Jinja2Templates(directory=".")

template_name = "movie_app.html"

local_prov = LocalMovieProvider(BASE_DIR)
external_prov = ExternalMovieProvider()
movie_service = MovieService(local_prov, external_prov)

@app.get("/search-movies")
async def search_movies(q: str = Query(..., min_length=2)):
    titles = local_prov.get_movie_list(q)
    return [{"title": t} for t in titles]

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse(template_name, {
        "request": request,
        "local": None,
        "external": None
    })

@app.post("/submit", response_class=HTMLResponse)
async def post_form(request: Request, movie_title: str = Form(...)):
    movie = movie_service.get_full_report(movie_title)

    # Handle the case where no movie was found
    if isinstance(movie, dict) and "error" in movie:
        return templates.TemplateResponse("movie_app.html", {
            "request": request,
            "error_message": f"Could not find movie: {movie_title}",
            "local": None,
            "external": None
        })

    return templates.TemplateResponse("movie_app.html", {
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
