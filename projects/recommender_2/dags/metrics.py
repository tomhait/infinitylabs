import numpy as np
from sklearn.metrics import ndcg_score

def calculate_mrr_at_k(recommendations_df, test_movies, k=10):
    relevant = set(test_movies)
    for rank, movie_id in enumerate(recommendations_df['movieId'].head(k), start=1):
        if movie_id in relevant:
            return 1.0 / rank
    return 0.0


def calculate_ndcg_at_k(recommendations_df, test_movies, k=10):
    if k < 2 or len(recommendations_df) < 2:
        return 0.0
    top_k = recommendations_df.head(k)
    if len(top_k) < 2:
        return 0.0
    y_true = np.array([[1 if movie_id in test_movies else 0 for movie_id in top_k['movieId']]])
    y_score = np.array([top_k['log_score'].tolist()])
    return float(ndcg_score(y_true, y_score, k=k))


def calculate_performance_k(recommendations_df, test_movies, k=10, with_mrr=False, with_ndcg=False):
    top_k_recommended_movie_ids = recommendations_df['movieId'].head(k).tolist()
    user_actual_liked_movies = test_movies
    relevant = set(user_actual_liked_movies)

    hits = 0
    for movie_id in top_k_recommended_movie_ids:
        if movie_id in relevant:
            hits += 1

    precision = hits / k
    hit_rate = 1 if hits > 0 else 0

    hits = 0
    for movie_id in user_actual_liked_movies:
        if movie_id in top_k_recommended_movie_ids:
            hits += 1

    recall = hits / len(user_actual_liked_movies)

    metrics = [hit_rate, precision, recall]
    if with_mrr:
        metrics.append(calculate_mrr_at_k(recommendations_df, test_movies, k))
    if with_ndcg:
        metrics.append(calculate_ndcg_at_k(recommendations_df, test_movies, k))

    return tuple(metrics)
