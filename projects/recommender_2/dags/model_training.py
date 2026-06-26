import gc
import os
import pandas as pd
import numpy as np
from functools import partial
from scipy import sparse
from sklearn.model_selection import train_test_split
from joblib import Parallel, delayed, effective_n_jobs

from data_manipulation import PrepareData
from metrics import calculate_performance_k
from models import NaiveBayesRecommender, TwoWayFM, MatrixFactorization, SVDModel


def _resolve_n_jobs(n_jobs):
    return effective_n_jobs(n_jobs)


def _get_candidate_movies_from_arrays(train_movies, test_movies, all_movies, popular_movies):
    train_movies = np.asarray(train_movies)
    test_movies = np.asarray(test_movies)
    candidates = np.setdiff1d(all_movies, train_movies)
    candidates = np.intersect1d(candidates, popular_movies)
    return np.union1d(candidates, test_movies)


def _evaluate_user_metrics(recommendations_df, test_movies, max_eval_k):
    prec, rec, hit_rates_user, mrr_user, ndcg_user = [], [], [], [], []
    for k in range(1, max_eval_k + 1):
        hit_rate, pr, rc, mrr, ndcg = calculate_performance_k(
            recommendations_df, test_movies, k=k, with_mrr=True, with_ndcg=True
        )
        prec.append(pr)
        rec.append(rc)
        hit_rates_user.append(hit_rate)
        mrr_user.append(mrr)
        ndcg_user.append(ndcg)
    return prec, rec, hit_rates_user, mrr_user, ndcg_user


def _feature_maps_from_info(feature_info):
    return {
        'user': feature_info['user_map'],
        'movie': feature_info['movie_map'],
        'gender': feature_info['gender_map'],
        'age': feature_info['age_map'],
        'occupation': feature_info['occupation_map'],
        'genre': feature_info['genre_map'],
    }


def _build_gender_map():
    """Binary one-hot gender indicators matching David's sex_m / sex_f columns."""
    return {'M': 0, 'F': 1}


def _build_genre_map(movies):
    genres = set()
    for value in movies['genres'].dropna():
        for genre in str(value).split('|'):
            genres.add(genre.lower())
    return {genre: index for index, genre in enumerate(sorted(genres))}


def _build_movie_genres_lookup(movies):
    return {
        row['movieId']: '|'.join(g.lower() for g in str(row['genres']).split('|'))
        if pd.notna(row['genres']) else ''
        for _, row in movies[['movieId', 'genres']].iterrows()
    }


def _encode_genre_columns(data, movie_genres, genre_map, genre_offset):
    row_idx = []
    col_idx = []
    for row_i, movie_id in enumerate(data['movieId'].to_numpy()):
        genres_str = movie_genres.get(movie_id, '')
        if not genres_str:
            continue
        for genre in genres_str.split('|'):
            if genre in genre_map:
                row_idx.append(row_i)
                col_idx.append(genre_offset + genre_map[genre])
    return np.array(row_idx, dtype=np.int64), np.array(col_idx, dtype=np.int64)


def _encode_feature_columns(data, feature_maps, offsets):
    """One-hot indices for user, movie, gender (sex_m/sex_f), age, and occupation."""
    return np.column_stack([
        offsets['user'] + data['userId'].map(feature_maps['user']).to_numpy(),
        offsets['movie'] + data['movieId'].map(feature_maps['movie']).to_numpy(),
        offsets['gender'] + data['gender'].map(feature_maps['gender']).to_numpy(),
        offsets['age'] + data['age'].map(feature_maps['age']).to_numpy(),
        offsets['occupation'] + data['occupation'].map(feature_maps['occupation']).to_numpy(),
    ])


def _build_sparse_matrix(n_samples, categorical_columns, genre_row_idx, genre_col_idx, n_features):
    n_categorical = categorical_columns.shape[1]
    row_idx_cat = np.repeat(np.arange(n_samples), n_categorical)
    col_idx_cat = categorical_columns.ravel()
    vals_cat = np.ones(len(row_idx_cat), dtype=np.float64)

    vals_genre = np.ones(len(genre_row_idx), dtype=np.float64)
    row_idx = np.concatenate([row_idx_cat, genre_row_idx])
    col_idx = np.concatenate([col_idx_cat, genre_col_idx])
    values = np.concatenate([vals_cat, vals_genre])
    return sparse.csr_matrix((values, (row_idx, col_idx)), shape=(n_samples, n_features))


def _encode_fm_user_movie_pairs(user_id, movie_ids, users, feature_info):
    user_row = users.loc[users['userId'] == user_id].iloc[0]
    feature_maps = _feature_maps_from_info(feature_info)
    offsets = feature_info['offsets']
    n_features = feature_info['n_features']
    n_candidates = len(movie_ids)
    pair_data = pd.DataFrame({
        'userId': np.full(n_candidates, user_id),
        'movieId': movie_ids,
        'age': np.full(n_candidates, user_row['age']),
        'gender': np.full(n_candidates, user_row['gender']),
        'occupation': np.full(n_candidates, user_row['occupation']),
    })
    feature_columns = _encode_feature_columns(pair_data, feature_maps, offsets)
    genre_row_idx, genre_col_idx = _encode_genre_columns(
        pair_data,
        feature_info['movie_genres'],
        feature_maps['genre'],
        offsets['genre'],
    )
    return _build_sparse_matrix(
        n_candidates,
        feature_columns,
        genre_row_idx,
        genre_col_idx,
        n_features,
    )


def _evaluate_fm_user(
    user_id,
    train_movies,
    test_movies,
    model,
    users,
    feature_info,
    all_movies,
    popular_movies,
    max_eval_k,
):
    candidates = _get_candidate_movies_from_arrays(
        train_movies, test_movies, all_movies, popular_movies
    )
    if len(candidates) == 0:
        return None

    X_candidates = _encode_fm_user_movie_pairs(
        user_id, candidates, users, feature_info
    )
    scores = model.predict(X_candidates)
    recommendations_df = pd.DataFrame({
        'movieId': candidates,
        'log_score': scores,
    }).sort_values('log_score', ascending=False)
    return _evaluate_user_metrics(recommendations_df, test_movies, max_eval_k)


def _evaluate_nb_user(user_id, train_movies, test_movies, recommender, max_eval_k, min_popularity):
    recommendations_df, message = recommender.recommend(
        user_id=user_id,
        train_movies=train_movies,
        test_movies=test_movies,
        min_ratings=min_popularity,
    )
    if message:
        return None
    return _evaluate_user_metrics(recommendations_df, test_movies, max_eval_k)


def _evaluate_lf_user(user_id, train_movies, test_movies, model, all_movies, popular_movies, max_eval_k):
    candidates = _get_candidate_movies_from_arrays(
        train_movies, test_movies, all_movies, popular_movies
    )
    if len(candidates) == 0:
        return None
    scores = model.predict_user_items(user_id, candidates)
    recommendations_df = pd.DataFrame({
        'movieId': candidates,
        'log_score': scores,
    }).sort_values('log_score', ascending=False)
    return _evaluate_user_metrics(recommendations_df, test_movies, max_eval_k)


def _run_parallel_user_eval(label, splits, eval_fn, n_jobs, backend='threading'):
    items = [
        (user_id, train_movies, test_movies)
        for user_id, (train_movies, test_movies) in splits.items()
    ]
    n_workers = _resolve_n_jobs(n_jobs)
    total_users = len(items)

    if n_workers == 1:
        results = []
        for idx, item in enumerate(items, start=1):
            if idx == 1 or idx % 50 == 0 or idx == total_users:
                print(f"{label} evaluation progress: {idx}/{total_users} users")
            result = eval_fn(*item)
            if result is not None:
                results.append(result)
        return results

    print(
        f"{label} parallel evaluation with {n_workers} {backend} workers "
        f"over {total_users} users."
    )
    raw = Parallel(n_jobs=n_workers, backend=backend)(
        delayed(eval_fn)(user_id, train_movies, test_movies)
        for user_id, train_movies, test_movies in items
    )
    gc.collect()
    return [result for result in raw if result is not None]


def _resolve_user_split(dm, user_id, min_ratings, splits=None):
    if splits is not None and user_id in splits:
        return splits[user_id]
    liked_ratings = dm.get_ratings()
    liked_ratings = liked_ratings[liked_ratings['rating'] >= dm.liked_th]
    user_ratings = liked_ratings[liked_ratings['userId'] == user_id]
    user_liked_movie_ids = user_ratings.sort_values(
        by='timestamp', ascending=False
    )['movieId'].unique()[:min_ratings]
    user_liked_movie_ids = user_liked_movie_ids[::-1]
    if len(user_liked_movie_ids) < 5:
        return [], []
    return train_test_split(
        user_liked_movie_ids, shuffle=False, test_size=0.2, random_state=42
    )


def _top_recommendations_nb(artifact, user_id, train_movies, test_movies, min_popularity, top_k):
    recommendations_df, message = artifact['recommender'].recommend(
        user_id=user_id,
        train_movies=train_movies,
        test_movies=test_movies,
        min_ratings=min_popularity,
    )
    if message:
        return None, message
    return recommendations_df.head(top_k), None


def _top_recommendations_fm(artifact, dm, user_id, train_movies, test_movies, min_popularity, top_k):
    model = artifact['model']
    users = artifact['users']
    feature_info = artifact['feature_info']
    movie_rating_counts = dm.get_movie_rating_count()
    all_movies = dm.get_liked_df().index.unique()
    popular_movies = movie_rating_counts[movie_rating_counts >= min_popularity].index
    candidates = _get_candidate_movies_from_arrays(
        train_movies, test_movies, all_movies, popular_movies
    )
    if len(candidates) == 0:
        return None, f"No valid candidate movies to recommend for user {user_id}."

    X_candidates = _encode_fm_user_movie_pairs(
        user_id, candidates, users, feature_info
    )
    scores = model.predict(X_candidates)
    recommendations_df = pd.DataFrame({
        'movieId': candidates,
        'log_score': scores,
    }).sort_values('log_score', ascending=False)
    return recommendations_df.head(top_k), None


def _top_recommendations_lf(artifact, dm, user_id, train_movies, test_movies, min_popularity, top_k):
    model = artifact['model']
    movie_rating_counts = dm.get_movie_rating_count()
    all_movies = dm.get_liked_df().index.unique()
    popular_movies = movie_rating_counts[movie_rating_counts >= min_popularity].index
    candidates = _get_candidate_movies_from_arrays(
        train_movies, test_movies, all_movies, popular_movies
    )
    if len(candidates) == 0:
        return None, f"No valid candidate movies to recommend for user {user_id}."

    scores = model.predict_user_items(user_id, candidates)
    recommendations_df = pd.DataFrame({
        'movieId': candidates,
        'log_score': scores,
    }).sort_values('log_score', ascending=False)
    return recommendations_df.head(top_k), None


def recommend_with_artifact(artifact, dm, user_id, train_movies, test_movies, top_k=10, min_popularity=None):
    trainer_config = artifact.get('trainer_config', {})
    if min_popularity is None:
        min_popularity = trainer_config.get('min_popularity', 20)

    model_type = artifact.get('model_type', 'naive_bayes')
    if model_type == 'naive_bayes':
        return _top_recommendations_nb(
            artifact, user_id, train_movies, test_movies, min_popularity, top_k
        )
    if model_type == 'factorization_machine':
        return _top_recommendations_fm(
            artifact, dm, user_id, train_movies, test_movies, min_popularity, top_k
        )
    if model_type in ('matrix_factorization', 'svd'):
        return _top_recommendations_lf(
            artifact, dm, user_id, train_movies, test_movies, min_popularity, top_k
        )
    return None, f"Unsupported production model type: {model_type}"


def get_user_recommendations(
    dm,
    artifacts,
    user_ids,
    top_k=10,
    min_ratings=200,
    min_popularity=20,
    splits=None,
    model_labels=None,
):
    model_labels = model_labels or {}
    movies_df = dm.get_movies()[['movieId', 'title']]
    recommendations = {}

    for user_id in user_ids:
        train_movies, test_movies = _resolve_user_split(dm, user_id, min_ratings, splits)
        if len(train_movies) == 0:
            recommendations[user_id] = {
                model_key: (None, f"User {user_id} has insufficient liked ratings for recommendations.")
                for model_key in artifacts
            }
            continue

        recommendations[user_id] = {}
        for model_key, artifact in artifacts.items():
            if model_key == 'naive_bayes':
                recs, message = _top_recommendations_nb(
                    artifact, user_id, train_movies, test_movies, min_popularity, top_k
                )
            elif model_key == 'factorization_machine':
                recs, message = _top_recommendations_fm(
                    artifact, dm, user_id, train_movies, test_movies, min_popularity, top_k
                )
            elif model_key in ('matrix_factorization', 'svd'):
                recs, message = _top_recommendations_lf(
                    artifact, dm, user_id, train_movies, test_movies, min_popularity, top_k
                )
            else:
                recs, message = None, f"Unknown model type: {model_key}"

            if recs is not None:
                recs = recs[['movieId', 'log_score']].merge(movies_df, on='movieId', how='left')
            recommendations[user_id][model_key] = (recs, message)

    return recommendations


def write_recommendations_file(path, recommendations, model_labels, top_k):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"Top {top_k} recommended movies per model\n")
        f.write("=" * 60 + "\n\n")
        for user_id, model_recs in recommendations.items():
            f.write(f"User {user_id}\n")
            f.write("-" * 40 + "\n")
            for model_key, (recs_df, message) in model_recs.items():
                label = model_labels.get(model_key, model_key)
                f.write(f"\n{label}\n")
                if message:
                    f.write(f"  {message}\n")
                    continue
                for rank, row in enumerate(recs_df.itertuples(index=False), start=1):
                    title = row.title if pd.notna(row.title) else "Unknown"
                    f.write(
                        f"  {rank:2d}. [{row.movieId}] {title} (score={row.log_score:.4f})\n"
                    )
            f.write("\n")
    print(f"Saved recommendations to {path}.")


class TrainModel:
    def __init__(
        self,
        dm: PrepareData,
        min_ratings=200,
        min_popularity=20,
        max_eval_k=None,
        n_jobs=1,
        eval_backend='threading',
    ):
        self.min_ratings = min_ratings
        self.min_popularity = min_popularity
        self.max_eval_k = max_eval_k if max_eval_k is not None else min_ratings - 1
        self.n_jobs = n_jobs
        self.eval_backend = eval_backend
        self.dm = dm
        self.model_artifact = None

    def _trainer_config(self):
        return {
            'liked_th': self.dm.liked_th,
            'min_ratings': self.min_ratings,
            'min_popularity': self.min_popularity,
        }

    def _get_tested_users(self):
        num_ratings_per_user = self.dm.get_num_ratings_per_user()
        filtered_users = num_ratings_per_user[num_ratings_per_user >= self.min_ratings].index.tolist()
        print(f"Number of users with at least {self.min_ratings} ratings: {len(filtered_users)}")
        return filtered_users

    def _get_user_train_test(self, user_id, liked_ratings=None):
        if liked_ratings is None:
            ratings = self.dm.get_ratings()
            user_ratings = ratings[ratings['userId'] == user_id]
        else:
            user_ratings = liked_ratings[liked_ratings['userId'] == user_id]
        user_liked_movie_ids = user_ratings[user_ratings['rating'] >= self.dm.liked_th]
        user_liked_movie_ids = user_liked_movie_ids.sort_values(
            by='timestamp', ascending=False
        )['movieId'].unique()[:self.min_ratings]
        user_liked_movie_ids = user_liked_movie_ids[::-1]
        if len(user_liked_movie_ids) < 5:
            return [], []
        train_movies, test_movies = train_test_split(
            user_liked_movie_ids, shuffle=False, test_size=0.2, random_state=42
        )
        return train_movies, test_movies

    def _build_user_splits(self, max_users=None):
        users = self._get_tested_users()
        if max_users is not None:
            users = users[:max_users]
        liked_ratings = self.dm.get_ratings()
        liked_ratings = liked_ratings[liked_ratings['rating'] >= self.dm.liked_th]
        splits = {}
        for user_id in users:
            train_movies, test_movies = self._get_user_train_test(user_id, liked_ratings)
            if len(train_movies) > 0 and len(test_movies) > 0:
                splits[user_id] = (train_movies, test_movies)
        return splits

    def _get_candidate_movies(self, train_movies, test_movies):
        movie_rating_counts = self.dm.get_movie_rating_count()
        all_movies = self.dm.get_liked_df().index.unique()
        popular_movies = movie_rating_counts[movie_rating_counts >= self.min_popularity].index
        return _get_candidate_movies_from_arrays(
            train_movies, test_movies, all_movies, popular_movies
        )

    def _evaluate_user(self, recommendations_df, test_movies):
        return _evaluate_user_metrics(recommendations_df, test_movies, self.max_eval_k)

    def _calc_metrics(self, prec, rec, hit_rates, mrr, ndcg):
        precisions_array = np.array(prec)
        recalls_array = np.array(rec)
        hit_rates_array = np.array(hit_rates)
        mrr_array = np.array(mrr)
        ndcg_array = np.array(ndcg)
        average_prec_per_k = np.mean(precisions_array, axis=0)
        average_rec_per_k = np.mean(recalls_array, axis=0)
        average_hit_rates_per_k = np.mean(hit_rates_array, axis=0)
        average_mrr_per_k = np.mean(mrr_array, axis=0)
        average_ndcg_per_k = np.mean(ndcg_array, axis=0)

        denominator = average_prec_per_k + average_rec_per_k
        average_f1_per_k = np.divide(
            2 * average_prec_per_k * average_rec_per_k,
            denominator,
            out=np.zeros_like(denominator),
            where=denominator != 0,
        )
        return (
            average_prec_per_k,
            average_rec_per_k,
            average_hit_rates_per_k,
            average_f1_per_k,
            average_mrr_per_k,
            average_ndcg_per_k,
        )

    def train(self):
        pass


class TrainFactorMachineModel(TrainModel):
    def __init__(
        self,
        dm: PrepareData,
        min_ratings=200,
        min_popularity=20,
        max_eval_k=None,
        n_jobs=1,
        eval_backend='threading',
        num_dim=16,
        num_epochs=10,
        learning_rate=0.05,
        batch_size=1024,
        train_sample_frac=1.0,
    ):
        super().__init__(
            dm,
            min_ratings=min_ratings,
            min_popularity=min_popularity,
            max_eval_k=max_eval_k,
            n_jobs=n_jobs,
            eval_backend=eval_backend,
        )
        self.num_dim = num_dim
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.train_sample_frac = train_sample_frac
        self.feature_info = None

    def _get_model_data(self):
        ratings = self.dm.get_ratings()
        users = self.dm.get_users()
        movies = self.dm.get_movies()
        data = ratings.merge(users, on='userId', how='inner')
        return data, users, movies

    def _build_index_map(self, values):
        sorted_values = np.sort(values)
        return {value: index for index, value in enumerate(sorted_values)}

    def _build_feature_maps(self, users, movies):
        return {
            'user': self._build_index_map(users['userId'].unique()),
            'movie': self._build_index_map(movies['movieId'].unique()),
            'gender': _build_gender_map(),
            'age': self._build_index_map(users['age'].unique()),
            'occupation': self._build_index_map(users['occupation'].unique()),
            'genre': _build_genre_map(movies),
        }

    def _build_feature_offsets(self, feature_maps):
        offset = 0
        offsets = {}
        for name in ('user', 'movie', 'gender', 'age', 'occupation', 'genre'):
            offsets[name] = offset
            offset += len(feature_maps[name])
        return offsets, offset

    def _encode_feature_columns(self, data, feature_maps, offsets):
        return _encode_feature_columns(data, feature_maps, offsets)

    def _build_sparse_matrix(
        self,
        n_samples,
        categorical_columns,
        genre_row_idx,
        genre_col_idx,
        n_features,
    ):
        return _build_sparse_matrix(
            n_samples,
            categorical_columns,
            genre_row_idx,
            genre_col_idx,
            n_features,
        )

    def _feature_maps_from_info(self, feature_info):
        return _feature_maps_from_info(feature_info)

    def _build_feature_info(self, feature_maps, offsets, n_features, movies):
        return {
            'offsets': offsets,
            'user_map': feature_maps['user'],
            'movie_map': feature_maps['movie'],
            'gender_map': feature_maps['gender'],
            'gender_labels': ['sex_m', 'sex_f'],
            'age_map': feature_maps['age'],
            'occupation_map': feature_maps['occupation'],
            'genre_map': feature_maps['genre'],
            'movie_genres': _build_movie_genres_lookup(movies),
            'n_features': n_features,
        }

    def _build_feature_info_only(self, data, users, movies):
        feature_maps = self._build_feature_maps(users, movies)
        offsets, n_features = self._build_feature_offsets(feature_maps)
        return self._build_feature_info(feature_maps, offsets, n_features, movies)

    def create_feature_matrix_from_data(self, data, users, movies, feature_info=None):
        if feature_info is None:
            feature_maps = self._build_feature_maps(users, movies)
            offsets, n_features = self._build_feature_offsets(feature_maps)
            feature_info = self._build_feature_info(feature_maps, offsets, n_features, movies)
        else:
            feature_maps = self._feature_maps_from_info(feature_info)
            offsets = feature_info['offsets']
            n_features = feature_info['n_features']

        feature_columns = self._encode_feature_columns(data, feature_maps, offsets)
        genre_row_idx, genre_col_idx = _encode_genre_columns(
            data,
            feature_info['movie_genres'],
            feature_maps['genre'],
            offsets['genre'],
        )
        X = self._build_sparse_matrix(
            len(data),
            feature_columns,
            genre_row_idx,
            genre_col_idx,
            n_features,
        )
        y = data['rating'].astype(np.float64).to_numpy()
        return X, y, feature_info

    def create_feature_matrix(self):
        data, users, movies = self._get_model_data()
        X, y, feature_info = self.create_feature_matrix_from_data(data, users, movies)
        self.feature_info = feature_info
        return X, y, feature_info

    def _build_train_data(self, data, splits):
        held_out = pd.DataFrame(
            [(user_id, movie_id) for user_id, (_, test_movies) in splits.items() for movie_id in test_movies],
            columns=['userId', 'movieId'],
        )
        held_out['_held_out'] = 1
        merged = data.merge(held_out, on=['userId', 'movieId'], how='left')
        return merged[merged['_held_out'].isna()].drop(columns=['_held_out'])

    def _encode_user_movie_pairs(self, user_id, movie_ids, users, feature_info):
        return _encode_fm_user_movie_pairs(
            user_id, movie_ids, users, feature_info
        )

    def _recommend_for_user(self, model, user_id, train_movies, test_movies, users, feature_info, data):
        movie_rating_counts = self.dm.get_movie_rating_count()
        all_movies = self.dm.get_liked_df().index.unique()
        popular_movies = movie_rating_counts[movie_rating_counts >= self.min_popularity].index
        candidates = _get_candidate_movies_from_arrays(
            train_movies, test_movies, all_movies, popular_movies
        )
        if len(candidates) == 0:
            return None, f"No valid candidate movies to recommend for user {user_id}."

        X_candidates = _encode_fm_user_movie_pairs(
            user_id, candidates, users, feature_info
        )
        scores = model.predict(X_candidates)
        recommendations_df = pd.DataFrame({
            'movieId': candidates,
            'log_score': scores,
        }).sort_values('log_score', ascending=False)
        return recommendations_df, None

    def train(self, splits=None):
        data, users, movies = self._get_model_data()
        if splits is None:
            splits = self._build_user_splits()

        feature_info = self._build_feature_info_only(data, users, movies)
        self.feature_info = feature_info

        train_data = self._build_train_data(data, splits)
        if self.train_sample_frac < 1.0:
            train_data = train_data.sample(frac=self.train_sample_frac, random_state=42)
        print(f"Training FM on {len(train_data)} ratings after holding out test liked movies.")
        X_train, y_train, _ = self.create_feature_matrix_from_data(
            train_data, users, movies, feature_info=feature_info
        )

        model = TwoWayFM(
            num_dim=self.num_dim,
            num_epochs=self.num_epochs,
            learning_rate=self.learning_rate,
            batch_size=self.batch_size,
            standardize_y=True,
            verbose=True,
        )
        model.fit(X_train, y_train)
        del X_train, y_train, train_data
        gc.collect()

        movie_rating_counts = self.dm.get_movie_rating_count()
        all_movies = self.dm.get_liked_df().index.unique()
        popular_movies = movie_rating_counts[movie_rating_counts >= self.min_popularity].index
        eval_fn = partial(
            _evaluate_fm_user,
            model=model,
            users=users,
            feature_info=feature_info,
            all_movies=all_movies,
            popular_movies=popular_movies,
            max_eval_k=self.max_eval_k,
        )
        user_results = _run_parallel_user_eval(
            "FM", splits, eval_fn, self.n_jobs, backend=self.eval_backend
        )
        all_prec = [result[0] for result in user_results]
        all_rec = [result[1] for result in user_results]
        all_hit_rates = [result[2] for result in user_results]
        all_mrr = [result[3] for result in user_results]
        all_ndcg = [result[4] for result in user_results]

        self.model_artifact = {
            'model_type': 'factorization_machine',
            'model': model,
            'feature_info': feature_info,
            'users': users,
            'trainer_config': {
                **self._trainer_config(),
                'num_dim': self.num_dim,
                'num_epochs': self.num_epochs,
                'learning_rate': self.learning_rate,
                'batch_size': self.batch_size,
                'train_sample_frac': self.train_sample_frac,
            },
        }
        return self._calc_metrics(all_prec, all_rec, all_hit_rates, all_mrr, all_ndcg)

    def fit_production(self):
        data, users, movies = self._get_model_data()
        feature_info = self._build_feature_info_only(data, users, movies)
        self.feature_info = feature_info

        train_data = data
        if self.train_sample_frac < 1.0:
            train_data = train_data.sample(frac=self.train_sample_frac, random_state=42)
        print(f"Training production FM on {len(train_data)} ratings.")
        X_train, y_train, _ = self.create_feature_matrix_from_data(
            train_data, users, movies, feature_info=feature_info
        )

        model = TwoWayFM(
            num_dim=self.num_dim,
            num_epochs=self.num_epochs,
            learning_rate=self.learning_rate,
            batch_size=self.batch_size,
            standardize_y=True,
            verbose=True,
        )
        model.fit(X_train, y_train)
        del X_train, y_train
        gc.collect()
        return model, feature_info


class TrainLatentFactorModel(TrainModel):
    def _get_model_data(self):
        ratings = self.dm.get_ratings()
        return ratings.merge(self.dm.get_users(), on='userId', how='inner')

    def _build_train_data(self, data, splits):
        held_out = pd.DataFrame(
            [(user_id, movie_id) for user_id, (_, test_movies) in splits.items() for movie_id in test_movies],
            columns=['userId', 'movieId'],
        )
        held_out['_held_out'] = 1
        merged = data.merge(held_out, on=['userId', 'movieId'], how='left')
        return merged[merged['_held_out'].isna()].drop(columns=['_held_out'])

    def _get_eval_context(self):
        movie_rating_counts = self.dm.get_movie_rating_count()
        all_movies = self.dm.get_liked_df().index.unique()
        popular_movies = movie_rating_counts[movie_rating_counts >= self.min_popularity].index
        return all_movies, popular_movies

    def _evaluate_trained_model(self, model, splits, label):
        all_movies, popular_movies = self._get_eval_context()
        eval_fn = partial(
            _evaluate_lf_user,
            model=model,
            all_movies=all_movies,
            popular_movies=popular_movies,
            max_eval_k=self.max_eval_k,
        )
        user_results = _run_parallel_user_eval(
            label, splits, eval_fn, self.n_jobs, backend=self.eval_backend
        )
        all_prec = [result[0] for result in user_results]
        all_rec = [result[1] for result in user_results]
        all_hit_rates = [result[2] for result in user_results]
        all_mrr = [result[3] for result in user_results]
        all_ndcg = [result[4] for result in user_results]
        return self._calc_metrics(all_prec, all_rec, all_hit_rates, all_mrr, all_ndcg)


class TrainMatrixFactorizationModel(TrainLatentFactorModel):
    def __init__(
        self,
        dm: PrepareData,
        min_ratings=200,
        min_popularity=20,
        max_eval_k=None,
        n_jobs=1,
        eval_backend='threading',
        num_factors=20,
        max_iter=200,
        train_sample_frac=1.0,
    ):
        super().__init__(
            dm,
            min_ratings=min_ratings,
            min_popularity=min_popularity,
            max_eval_k=max_eval_k,
            n_jobs=n_jobs,
            eval_backend=eval_backend,
        )
        self.num_factors = num_factors
        self.max_iter = max_iter
        self.train_sample_frac = train_sample_frac

    def train(self, splits=None):
        data = self._get_model_data()
        if splits is None:
            splits = self._build_user_splits()

        train_data = self._build_train_data(data, splits)
        if self.train_sample_frac < 1.0:
            train_data = train_data.sample(frac=self.train_sample_frac, random_state=42)
        print(f"Training NMF on {len(train_data)} ratings after holding out test liked movies.")

        model = MatrixFactorization(
            num_factors=self.num_factors,
            max_iter=self.max_iter,
            verbose=True,
        )
        model.fit(
            train_data['userId'].to_numpy(),
            train_data['movieId'].to_numpy(),
            train_data['rating'].to_numpy(),
        )
        del train_data
        gc.collect()
        self.model_artifact = {
            'model_type': 'matrix_factorization',
            'model': model,
            'trainer_config': {
                **self._trainer_config(),
                'num_factors': self.num_factors,
                'max_iter': self.max_iter,
                'train_sample_frac': self.train_sample_frac,
            },
        }
        return self._evaluate_trained_model(model, splits, "NMF")


class TrainSVDModel(TrainLatentFactorModel):
    def __init__(
        self,
        dm: PrepareData,
        min_ratings=200,
        min_popularity=20,
        max_eval_k=None,
        n_jobs=1,
        eval_backend='threading',
        num_factors=20,
        train_sample_frac=1.0,
    ):
        super().__init__(
            dm,
            min_ratings=min_ratings,
            min_popularity=min_popularity,
            max_eval_k=max_eval_k,
            n_jobs=n_jobs,
            eval_backend=eval_backend,
        )
        self.num_factors = num_factors
        self.train_sample_frac = train_sample_frac

    def train(self, splits=None):
        data = self._get_model_data()
        if splits is None:
            splits = self._build_user_splits()

        train_data = self._build_train_data(data, splits)
        if self.train_sample_frac < 1.0:
            train_data = train_data.sample(frac=self.train_sample_frac, random_state=42)
        print(f"Training TruncatedSVD on {len(train_data)} ratings after holding out test liked movies.")

        model = SVDModel(num_factors=self.num_factors, verbose=True)
        model.fit(
            train_data['userId'].to_numpy(),
            train_data['movieId'].to_numpy(),
            train_data['rating'].to_numpy(),
        )
        del train_data
        gc.collect()
        self.model_artifact = {
            'model_type': 'svd',
            'model': model,
            'trainer_config': {
                **self._trainer_config(),
                'num_factors': self.num_factors,
                'train_sample_frac': self.train_sample_frac,
            },
        }
        return self._evaluate_trained_model(model, splits, "TruncatedSVD")


class TrainNaiveBayesModel(TrainModel):
    def _train_single(self, recommender, user_id, train_movies, test_movies):
        return _evaluate_nb_user(
            user_id,
            train_movies,
            test_movies,
            recommender,
            self.max_eval_k,
            self.min_popularity,
        )

    def train(self, splits=None):
        liked_df = self.dm.get_liked_df()
        movies = self.dm.get_movies()
        movie_rating_counts = self.dm.get_movie_rating_count()
        if splits is None:
            splits = self._build_user_splits()

        recommender = NaiveBayesRecommender(liked_df, movies, movie_rating_counts)
        eval_fn = partial(
            _evaluate_nb_user,
            recommender=recommender,
            max_eval_k=self.max_eval_k,
            min_popularity=self.min_popularity,
        )
        user_results = _run_parallel_user_eval(
            "Naive Bayes", splits, eval_fn, self.n_jobs, backend=self.eval_backend
        )
        all_prec = [result[0] for result in user_results]
        all_rec = [result[1] for result in user_results]
        all_hit_rates = [result[2] for result in user_results]
        all_mrr = [result[3] for result in user_results]
        all_ndcg = [result[4] for result in user_results]
        self.model_artifact = {
            'model_type': 'naive_bayes',
            'recommender': recommender,
            'trainer_config': self._trainer_config(),
        }
        return self._calc_metrics(all_prec, all_rec, all_hit_rates, all_mrr, all_ndcg)


def evaluate_saved_fm_model(
    dm,
    artifact,
    min_ratings=200,
    min_popularity=20,
    top_k=10,
    max_users=None,
    n_jobs=1,
    eval_backend='threading',
    splits=None,
):
    trainer = TrainFactorMachineModel(
        dm,
        min_ratings=min_ratings,
        min_popularity=min_popularity,
        max_eval_k=top_k,
        n_jobs=n_jobs,
        eval_backend=eval_backend,
    )
    if splits is None:
        splits = trainer._build_user_splits(max_users=max_users)

    model = artifact['model']
    feature_info = artifact['feature_info']
    data, users, movies = trainer._get_model_data()
    movie_rating_counts = dm.get_movie_rating_count()
    all_movies = dm.get_liked_df().index.unique()
    popular_movies = movie_rating_counts[movie_rating_counts >= min_popularity].index
    eval_fn = partial(
        _evaluate_fm_user,
        model=model,
        users=users,
        feature_info=feature_info,
        all_movies=all_movies,
        popular_movies=popular_movies,
        max_eval_k=top_k,
    )
    user_results = _run_parallel_user_eval(
        "Saved FM", splits, eval_fn, n_jobs, backend=eval_backend
    )
    all_prec = [result[0] for result in user_results]
    all_rec = [result[1] for result in user_results]
    all_hit_rates = [result[2] for result in user_results]
    all_mrr = [result[3] for result in user_results]
    all_ndcg = [result[4] for result in user_results]
    return trainer._calc_metrics(all_prec, all_rec, all_hit_rates, all_mrr, all_ndcg), splits


def compare_models(
    dm,
    min_ratings=200,
    min_popularity=20,
    top_k=10,
    max_users=None,
    n_jobs=1,
    eval_backend='threading',
    fm_kwargs=None,
    mf_kwargs=None,
    svd_kwargs=None,
    models=None,
):
    fm_kwargs = fm_kwargs or {}
    mf_kwargs = mf_kwargs or {}
    svd_kwargs = svd_kwargs or {}
    trainer_kwargs = {
        'min_ratings': min_ratings,
        'min_popularity': min_popularity,
        'max_eval_k': top_k,
        'n_jobs': n_jobs,
        'eval_backend': eval_backend,
    }
    base = TrainModel(dm, **trainer_kwargs)
    splits = base._build_user_splits(max_users=max_users)
    print(f"Evaluating {len(splits)} users with shared train/test splits (metrics @k=1..{top_k}).")

    all_model_trainers = {
        'naive_bayes': TrainNaiveBayesModel(dm, **trainer_kwargs),
        'factorization_machine': TrainFactorMachineModel(dm, **trainer_kwargs, **fm_kwargs),
        'matrix_factorization': TrainMatrixFactorizationModel(dm, **trainer_kwargs, **mf_kwargs),
        'svd': TrainSVDModel(dm, **trainer_kwargs, **svd_kwargs),
    }
    if models is not None:
        unknown_models = set(models) - set(all_model_trainers)
        if unknown_models:
            raise ValueError(f"Unknown model(s): {sorted(unknown_models)}")
    model_trainers = all_model_trainers if models is None else {name: all_model_trainers[name] for name in models}

    results = {'splits': splits, 'artifacts': {}}
    k = top_k - 1
    for name, trainer in model_trainers.items():
        print(f"\n--- {name.replace('_', ' ').title()} ---")
        metrics = trainer.train(splits=splits)
        results[name] = metrics
        results['artifacts'][name] = trainer.model_artifact
        print(
            f"{name.replace('_', ' ').title()} @k={top_k}: "
            f"precision={metrics[0][k]:.4f}, recall={metrics[1][k]:.4f}, "
            f"mrr={metrics[4][k]:.4f}, ndcg={metrics[5][k]:.4f}"
        )

    return results
