def calculate_performance_k(recommendations_df, test_movies, k=10):
    """
    Calculates Precision/Recall k for a given user's recommendations.
    """
    top_k_recommended_movie_ids = recommendations_df['movieId'].head(k).tolist()

    user_actual_liked_movies = test_movies

    hits = 0
    for movie_id in top_k_recommended_movie_ids:
        if movie_id in user_actual_liked_movies:
            hits += 1

    precision = hits / k

    hit_rate = 1 if hits > 0 else 0

    hits = 0
    for movie_id in user_actual_liked_movies:
        if movie_id in top_k_recommended_movie_ids:
            hits += 1

    recall = hits / len(user_actual_liked_movies)

    return hit_rate, precision, recall