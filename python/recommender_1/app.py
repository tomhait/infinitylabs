import psycopg2
import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
import re

from dags.data_manipulation import PrepareData
from dags.model import NaiveBayesRecommender
from src.movie_provider import ExternalMovieProvider
from src.movie import Movie

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "airflow",
    "password": "airflow",
    "dbname": "movielens"
}

model_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Handles startup state initialization and cleanup """
    print("Connecting to database and caching data structures for the model...")
    async with aiohttp.ClientSession() as session:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            dm = PrepareData(liked_th=3.5)
            dm.setup(cursor)

            model_state["recommender"] = NaiveBayesRecommender(
                liked_data=dm.get_liked_df(),
                movies_df=dm.get_movies(),
                rating_counts=dm.get_movie_rating_count()
            )
            model_state["data_manager"] = dm

            ext_provider = ExternalMovieProvider()
            ext_provider.set_session(session)
            model_state["external_provider"] = ext_provider

            cursor.close()
            conn.close()
            print("Model and external OMDB provider successfully cached!")

            yield
        finally:
            model_state.clear()


app = FastAPI(title="MovieLens Recommendation Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/recommend")
async def get_recommendations(user_id: int = Query(..., description="Target User ID for calculation")):
    recommender = model_state.get("recommender")
    dm = model_state.get("data_manager")
    ext_provider = model_state.get("external_provider")

    if not recommender or not dm:
        raise HTTPException(status_code=503, detail="Model assets are still compiling.")

    ratings = dm.get_ratings()
    user_ratings = ratings[ratings['userId'] == user_id]

    if user_ratings.empty:
        raise HTTPException(status_code=404, detail=f"User profile {user_id} not found.")

    user_liked_movies = user_ratings[user_ratings['rating'] >= dm.liked_th]
    user_liked_movies = user_liked_movies.sort_values(by='timestamp', ascending=False)['movieId'].unique()[:200]
    user_liked_movies = user_liked_movies[::-1]

    if len(user_liked_movies) < 5:
        raise HTTPException(
            status_code=422,
            detail=f"User {user_id} has liked only {len(user_liked_movies)} items. (Minimum 5 required)"
        )

    pivot_movie_ids = recommender.liked_data.index.unique()
    seen_movie_ids = user_ratings['movieId'].unique()
    test_movies = np.setdiff1d(pivot_movie_ids, seen_movie_ids).tolist()

    recommendations_df, error_msg = recommender.recommend(
        user_id=user_id,
        train_movies=user_liked_movies,
        test_movies=test_movies,
        min_ratings=200
    )

    if error_msg:
        raise HTTPException(status_code=400, detail=error_msg)

    top_10 = recommendations_df.head(10)
    movies_df = dm.get_movies()
    links_df = dm.get_links()

    async def fetch_imdb_metadata(row):
        m_id = int(row['movieId'])
        score = float(row['log_score'])

        local_movie = movies_df[movies_df['movieId'] == m_id]
        local_title = str(local_movie.iloc[0]['title']) if not local_movie.empty else "Unknown Title"
        local_genres = str(local_movie.iloc[0]['genres']) if not local_movie.empty else "Unknown"


        year_match = re.search(r'\((\d{4})\)', local_title)
        local_year = year_match.group(1) if year_match else "--"

        clean_local_title = re.sub(r'\s*\(\d{4}\)', '', local_title).strip()

        link_row = links_df[links_df['movieId'] == m_id]

        title = clean_local_title
        movie_year = local_year
        poster = "--"

        if not link_row.empty and link_row.iloc[0]['imdbId']:
            imdb_id = link_row.iloc[0]['imdbId']
            try:
                movie_obj = Movie(title="", movie_id=imdb_id)
                await ext_provider.get_movie_data(movie_obj)
                imdb_title = movie_obj.get_title()
                if imdb_title:
                    title = imdb_title

                if movie_obj.get_year() and movie_obj.get_year() != "--":
                    movie_year = str(movie_obj.get_year())

                poster = movie_obj.get_poster_url()
            except Exception:
                pass

        return {
            "movie_id": m_id,
            "title": title,
            "year": movie_year,
            "genres": local_genres,
            "score": score,
            "poster_url": poster
        }

    tasks = [fetch_imdb_metadata(row) for _, row in top_10.iterrows()]
    results = await asyncio.gather(*tasks)

    return {
        "user_id": user_id,
        "recommendations": results
    }

app.mount("/", StaticFiles(directory="static", html=True), name="static")