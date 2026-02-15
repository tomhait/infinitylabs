import pandas as pd
from movies_app import *
from pathlib import Path

BASE_DIR = Path("./ml-100k")

app = FastAPI()
templates = Jinja2Templates(directory=".")

template_name = "movie_app.html"

local_prov = LocalMovieProvider(BASE_DIR)
external_prov = ExternalMovieProvider("","")
movie_service = MovieService(local_prov, external_prov)

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
        # Initial load of the page
    return templates.TemplateResponse(template_name, {"request": request})

@app.post("/submit", response_class=HTMLResponse)
async def post_form(
    request: Request,
    movie_title: str = Form(...)  # Matches 'name' attribute in HTML
):
    data = movie_service.get_full_report(movie_title)

        # This is where Jinja takes the Python variables and puts them in the HTML
    return templates.TemplateResponse("movie_app.html", {
        "request": request,
        "movie_name": data['title'],
        "movie_score": data['average_rating']
    })

# if __name__ == "__main__":
#     local_prov = LocalMovieProvider(BASE_DIR)
#     external_prov = ExternalMovieProvider("","")
#     movie_service = MovieService(local_prov, external_prov)
#     #movie_api = MovieWebAPI("",movie_service)
#     #app = movie_api.app
