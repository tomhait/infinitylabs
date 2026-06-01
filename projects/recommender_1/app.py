import psycopg2
import asyncio
import aiohttp
import re
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    """Handles startup state initialization and cleanup"""
    print("Connecting to database and caching data structures for the model...")

    session = aiohttp.ClientSession()

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
        print("Model successfully cached in memory. Ready for server traffic!")

        yield

    except Exception as e:
        print(f"Failed to initialize application data: {e}")
        raise e
    finally:
        await session.close()
        model_state.clear()
        print("Network resources successfully closed down.")


app = FastAPI(title="MovieLens Recommendation Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_user_liked_history(ratings_df, user_id: int, liked_threshold: float) -> list:
    """Extracts a validated list of up to 200 movie IDs the user liked."""
    user_ratings = ratings_df[ratings_df['userId'] == user_id]
    if user_ratings.empty:
        raise HTTPException(status_code=404, detail=f"User profile {user_id} not found.")

    user_liked = user_ratings[user_ratings['rating'] >= liked_threshold]
    user_liked = user_liked.sort_values(by='timestamp', ascending=False)['movieId'].unique()[:200]

    user_liked_history = user_liked[::-1]

    if len(user_liked_history) < 5:
        raise HTTPException(
            status_code=422,
            detail=f"User {user_id} has liked only {len(user_liked_history)} items. (Minimum 5 required)"
        )
    return user_liked_history


def get_unseen_candidate_movies(recommender, ratings_df, user_id: int) -> list:
    """Finds all movie IDs in the system that this specific user hasn't rated yet."""
    pivot_movie_ids = recommender.liked_data.index.unique()
    user_seen_ids = ratings_df[ratings_df['userId'] == user_id]['movieId'].unique()
    return np.setdiff1d(pivot_movie_ids, user_seen_ids).tolist()


async def fetch_enriched_movie_metadata(row, movies_df, links_df, ext_provider) -> dict:
    """Enriches a single dataframe recommendation row with local DB fallbacks and external IMDb assets."""
    m_id = int(row['movieId'])
    score = float(row['log_score'])

    local_movie = movies_df[movies_df['movieId'] == m_id]
    local_title = str(local_movie.iloc[0]['title']) if not local_movie.empty else "Unknown Title"
    local_genres = str(local_movie.iloc[0]['genres']) if not local_movie.empty else "Unknown"

    year_match = re.search(r'\((\d{4})\)', local_title)
    movie_year = year_match.group(1) if year_match else "--"
    title = re.sub(r'\s*\(\d{4}\)', '', local_title).strip()
    poster = "--"

    link_row = links_df[links_df['movieId'] == m_id]
    if not link_row.empty and link_row.iloc[0]['imdbId']:
        imdb_id = link_row.iloc[0]['imdbId']
        try:
            movie_obj = Movie(title="", movie_id=imdb_id)
            await ext_provider.get_movie_data(movie_obj)

            if movie_obj.get_title():
                title = movie_obj.get_title()
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


@app.get("/recommend")
async def get_recommendations(user_id: int = Query(..., description="Target User ID")):
    recommender = model_state.get("recommender")
    dm = model_state.get("data_manager")
    ext_provider = model_state.get("external_provider")

    if not recommender or not dm or not ext_provider:
        raise HTTPException(status_code=503, detail="Model engine initialization pending.")

    ratings_df = dm.get_ratings()
    train_movies = get_user_liked_history(ratings_df, user_id, dm.liked_th)
    test_movies = get_unseen_candidate_movies(recommender, ratings_df, user_id)

    recommendations_df, error_msg = recommender.recommend(
        user_id=user_id,
        train_movies=train_movies,
        test_movies=test_movies,
        min_ratings=200
    )
    if error_msg:
        raise HTTPException(status_code=400, detail=error_msg)

    top_10 = recommendations_df.head(10)
    tasks = [
        fetch_enriched_movie_metadata(row, dm.get_movies(), dm.get_links(), ext_provider)
        for _, row in top_10.iterrows()
    ]
    enriched_recommendations = await asyncio.gather(*tasks)

    return {
        "user_id": user_id,
        "recommendations": enriched_recommendations
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")