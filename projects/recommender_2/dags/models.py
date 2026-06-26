import numpy as np
from scipy import sparse
from sklearn.decomposition import NMF, TruncatedSVD


class TwoWayFM:
    """
    Models a Factorization Machine
    if reg_penalty is not zero - performs L2 regularization
    """
    def __init__(self, num_dim, reg_penalty = 0.01, num_epochs = 100,
                 learning_rate = 0.05, batch_size=32, random_seed=42, verbose = True,
                 standardize_y = True):
        self.k = num_dim
        self.reg_penalty = 2 * reg_penalty if reg_penalty is not None else 0.0
        self.epoch = num_epochs
        self.lr = learning_rate
        self.batch_size = batch_size
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)
        self.verbose = verbose
        self.standardize_y = standardize_y
        self.y_mean = None
        self.y_std = None
        self._fitted = False

        self.w0 = 0.0
        self.w = None
        self.V = None

    def _setup(self, num_features):
        self.w0 = 0.0
        self.w = np.zeros(num_features)
        self.V = self.rng.normal(0.0, 0.1, (num_features, self.k))

    def _standardize_y(self, y, fit = False):
        y = np.asarray(y, dtype=float)
        if not self.standardize_y:
            return y
        if fit:
            self.y_mean = np.mean(y)
            self.y_std = np.std(y)
        return (y - self.y_mean) / (self.y_std + 1e-8)

    def _inverse_standardize_y(self, y_hat):
        if not self.standardize_y:
            return y_hat
        return y_hat * (self.y_std + 1e-8) + self.y_mean

    @staticmethod
    def _elementwise_square(X_batch):
        if sparse.issparse(X_batch):
            return X_batch.multiply(X_batch)
        return X_batch ** 2

    def _forward_batch(self, X_batch):
        """
        Computes forward batch for a mini batch.
        Works directly on sparse or dense X without densifying.
        """
        linear_terms = self.w0 + np.asarray(X_batch @ self.w).ravel()
        sum_v_x = np.asarray(X_batch @ self.V)
        sum_v2_x2 = np.asarray(self._elementwise_square(X_batch) @ (self.V ** 2))
        interaction_terms = 0.5 * np.sum(sum_v_x ** 2 - sum_v2_x2, axis=1)
        y_hat = linear_terms + interaction_terms
        return y_hat, sum_v_x

    def _gradient(self, X_batch, y_batch):
        """
        Performs gradient descent on a mini-batch.
        Returns the sum of squared (standardized) residuals for logging.
        """
        actual_batch_size = X_batch.shape[0]
        y_hat, sum_v_x = self._forward_batch(X_batch)
        residual = y_hat - y_batch
        errors = 2 * residual
        grad_w0 = np.mean(errors)

        grad_w = np.asarray(X_batch.T @ errors).ravel() / actual_batch_size + self.reg_penalty * self.w
        term1 = np.asarray(X_batch.T @ (errors[:, np.newaxis] * sum_v_x))
        term2 = self.V * np.asarray(self._elementwise_square(X_batch).T @ errors)[:, np.newaxis]

        grad_V = (term1 - term2) / actual_batch_size + self.reg_penalty * self.V

        self.w0 -= self.lr * grad_w0
        self.w -= self.lr * grad_w
        self.V -= self.lr * grad_V
        return float(np.sum(residual ** 2))

    def fit(self, X, y):
        num_samples, num_features = X.shape
        if sparse.issparse(X):
            X = X.tocsr()
        self._setup(num_features)
        y = np.asarray(y, dtype=float)
        y = self._standardize_y(y, fit=True)
        self._fitted = True
        y_scale = (self.y_std + 1e-8) ** 2 if self.standardize_y else 1.0
        for epoch in range(self.epoch):
            indices = self.rng.permutation(num_samples)
            total_sq_error = 0.0
            for start_idx in range(0, num_samples, self.batch_size):
                end_idx = min(start_idx + self.batch_size, num_samples)
                batch_idx = indices[start_idx:end_idx]
                X_batch = X[batch_idx]
                y_batch = y[batch_idx]
                total_sq_error += self._gradient(X_batch, y_batch)
            if self.verbose:
                mse = total_sq_error / num_samples * y_scale
                print(f"Epoch {epoch + 1}/{self.epoch} MSE: {mse:.6f}")

    def predict(self, X):
        if not self._fitted:
            raise ValueError("Call fit() before predict().")
        if sparse.issparse(X):
            X = X.tocsr()
        y_hat, _ = self._forward_batch(X)
        return self._inverse_standardize_y(y_hat)

class NaiveBayesRecommender:
    def __init__(self, liked_data, movies_df, rating_counts):
        self.liked_data = liked_data
        self.movies_df = movies_df
        self.rating_counts = rating_counts
        self.num_total_users = liked_data.shape[1]
        self.all_movie_ids_in_liked_data = liked_data.index.unique()

    def _get_user_liked_movies(self, train_movies, last_n):
        """
        Retrieves the last_n liked movies from the training set for a user.
        """
        user_liked_movie_ids_for_model = train_movies[::-1][:last_n]
        user_liked_movie_ids_for_model = np.intersect1d(user_liked_movie_ids_for_model, self.liked_data.index.unique())
        return user_liked_movie_ids_for_model

    def _get_candidate_movie_ids(self, train_movies, test_movies, min_ratings):
        """
        Identifies candidate movies for recommendation.
        """
        popular_movies = self.rating_counts[self.rating_counts >= min_ratings].index

        candidate_movie_ids_set = np.setdiff1d(self.all_movie_ids_in_liked_data, train_movies)
        candidate_movie_ids = np.intersect1d(candidate_movie_ids_set, popular_movies)
        candidate_movie_ids = np.union1d(candidate_movie_ids, test_movies)

        return candidate_movie_ids

    def _calculate_prior_probabilities(self, L_A, num_users_for_prob_calc, laplace_smoothing):
        """
        Calculates the log prior probabilities P(like A) for candidate movies.
        """
        num_liked_A_total_series = L_A.sum(axis=1)
        log_P_A_priors = np.log((num_liked_A_total_series + laplace_smoothing) / (num_users_for_prob_calc + 2 * laplace_smoothing))
        return log_P_A_priors

    def _calculate_conditional_probabilities(self, L_A, L_B, num_liked_A_total_series, laplace_smoothing, power=1.5):
        """
        Calculates the log conditional probabilities P(liked Bi | like A).
        Power > 1.0 penalizes random noise and rewards strong co-occurrence.
        """
        intersection_matrix = L_A.dot(L_B.T)
        weighted_intersection = np.power(intersection_matrix, power)
        numerator = weighted_intersection + laplace_smoothing
        denominator = num_liked_A_total_series + (2 * laplace_smoothing)
        P_Bi_given_A_matrix = numerator.divide(denominator, axis=0)
        log_P_Bi_given_A_matrix = np.log(P_Bi_given_A_matrix)
        return log_P_Bi_given_A_matrix

    def _combine_probabilities_and_format_recommendations(self, log_scores_series):
        """
        Formats the recommendation DataFrame based on the log scores.
        """
        recommended_movies_df = log_scores_series.reset_index()
        recommended_movies_df.columns = ['movieId', 'log_score']
        recommended_movies_df = recommended_movies_df.merge(self.movies_df[['movieId', 'title']], on='movieId', how='left')
        recommended_movies_df = recommended_movies_df[np.isfinite(recommended_movies_df['log_score'])]
        return recommended_movies_df

    def recommend(self, user_id, train_movies, test_movies, last_n=10, laplace_smoothing=1, min_ratings=20):
        """
        Generates Naive Bayes-like recommendations for a given user based on their liked movies.
        The score returned is a log-score.

        Args:
            user_id (int): The ID of the user for whom to generate recommendations.
            train_movies (list): List of movie IDs to use for training.
            test_movies (list): List of movie IDs to use for testing.
            last_n (int): The number of last n liked movies - B1, ..., Bn to consider.
            laplace_smoothing (float): Smoothing parameter to avoid zero probabilities.
            min_ratings (int): Minimum number of ratings for a movie to be considered.

        Returns:
            tuple: (pd.DataFrame of recommended movies, str message).
        """
        user_liked_movie_ids_for_model = self._get_user_liked_movies(train_movies, last_n)

        if len(user_liked_movie_ids_for_model) == 0:
            return None, f"User {user_id} has not liked any movies yet in the training set. Cannot generate recommendations."

        candidate_movie_ids = self._get_candidate_movie_ids(train_movies, test_movies, min_ratings)

        if len(candidate_movie_ids) == 0:
            return None, f"No valid candidate movies to recommend for user {user_id}."

        liked_data_for_prob_calc = self.liked_data.drop(columns=[user_id])
        num_users_for_prob_calc = liked_data_for_prob_calc.shape[1]

        L_A = liked_data_for_prob_calc.loc[candidate_movie_ids]
        L_B = liked_data_for_prob_calc.loc[user_liked_movie_ids_for_model]

        log_P_A_priors = self._calculate_prior_probabilities(L_A, num_users_for_prob_calc, laplace_smoothing)
        log_P_Bi_given_A_matrix = self._calculate_conditional_probabilities(L_A, L_B, L_A.sum(axis=1), laplace_smoothing)

        sum_log_P_Bi_given_A_series = log_P_Bi_given_A_matrix.sum(axis=1)
        log_scores_series = log_P_A_priors + sum_log_P_Bi_given_A_series

        recommended_movies_df = self._combine_probabilities_and_format_recommendations(log_scores_series)

        if not recommended_movies_df.empty:
            return recommended_movies_df.sort_values(by='log_score', ascending=False), None
        else:
            return None, f"Could not generate recommendations for user {user_id}."


class MatrixFactorization:
    def __init__(self, num_factors=20, max_iter=200, random_seed=42, verbose=True):
        self.k = num_factors
        self.verbose = verbose
        self.global_mean = 0.0
        self.model = NMF(
            n_components=num_factors,
            init='random',
            random_state=random_seed,
            max_iter=max_iter,
        )
        self.user_map = {}
        self.movie_map = {}
        self.user_factors = None
        self._fitted = False

    def _build_maps(self, user_ids, movie_ids):
        unique_users = np.sort(np.unique(user_ids))
        unique_movies = np.sort(np.unique(movie_ids))
        self.user_map = {user_id: idx for idx, user_id in enumerate(unique_users)}
        self.movie_map = {movie_id: idx for idx, movie_id in enumerate(unique_movies)}
        return len(unique_users), len(unique_movies)

    def fit(self, user_ids, movie_ids, ratings):
        user_ids = np.asarray(user_ids)
        movie_ids = np.asarray(movie_ids)
        ratings = np.asarray(ratings, dtype=np.float64)
        n_users, n_movies = self._build_maps(user_ids, movie_ids)
        user_idx = np.array([self.user_map[u] for u in user_ids])
        movie_idx = np.array([self.movie_map[m] for m in movie_ids])

        self.global_mean = float(np.mean(ratings))
        matrix = sparse.csr_matrix(
            (ratings, (user_idx, movie_idx)),
            shape=(n_users, n_movies),
            dtype=np.float64,
        )
        self.user_factors = self.model.fit_transform(matrix)
        self._fitted = True

        if self.verbose:
            pred = np.sum(
                self.user_factors[user_idx] * self.model.components_[:, movie_idx].T, axis=1
            )
            mse = np.mean((ratings - pred) ** 2)
            print(f"NMF training MSE on observed ratings: {mse:.6f}")

    def predict_user_items(self, user_id, movie_ids):
        if not self._fitted:
            raise ValueError("Call fit() before predict_user_items().")
        movie_ids = np.asarray(movie_ids)
        if user_id not in self.user_map:
            return np.full(len(movie_ids), self.global_mean)

        u = self.user_map[user_id]
        user_factor = self.user_factors[u]
        scores = np.full(len(movie_ids), self.global_mean, dtype=np.float64)
        for pos, movie_id in enumerate(movie_ids):
            if movie_id in self.movie_map:
                i = self.movie_map[movie_id]
                scores[pos] = user_factor @ self.model.components_[:, i]
        return scores


class SVDModel:
    def __init__(self, num_factors=20, random_seed=42, verbose=True):
        self.k = num_factors
        self.random_seed = random_seed
        self.verbose = verbose
        self.global_mean = 0.0
        self.model = None
        self.user_map = {}
        self.movie_map = {}
        self.user_factors = None
        self._fitted = False

    def _build_maps(self, user_ids, movie_ids):
        unique_users = np.sort(np.unique(user_ids))
        unique_movies = np.sort(np.unique(movie_ids))
        self.user_map = {user_id: idx for idx, user_id in enumerate(unique_users)}
        self.movie_map = {movie_id: idx for idx, movie_id in enumerate(unique_movies)}
        return len(unique_users), len(unique_movies)

    def fit(self, user_ids, movie_ids, ratings):
        user_ids = np.asarray(user_ids)
        movie_ids = np.asarray(movie_ids)
        ratings = np.asarray(ratings, dtype=np.float64)
        n_users, n_movies = self._build_maps(user_ids, movie_ids)
        user_idx = np.array([self.user_map[u] for u in user_ids])
        movie_idx = np.array([self.movie_map[m] for m in movie_ids])

        self.global_mean = float(np.mean(ratings))
        matrix = sparse.csr_matrix(
            (ratings, (user_idx, movie_idx)),
            shape=(n_users, n_movies),
            dtype=np.float64,
        )
        n_components = min(self.k, min(n_users, n_movies) - 1)
        if n_components < 1:
            self._fitted = True
            return

        self.model = TruncatedSVD(n_components=n_components, random_state=self.random_seed)
        self.user_factors = self.model.fit_transform(matrix)
        self._fitted = True

        if self.verbose:
            pred = self.global_mean + np.sum(
                self.user_factors[user_idx] * self.model.components_[:, movie_idx].T, axis=1
            )
            mse = np.mean((ratings - pred) ** 2)
            print(f"TruncatedSVD training MSE on observed ratings: {mse:.6f}")

    def predict_user_items(self, user_id, movie_ids):
        if not self._fitted:
            raise ValueError("Call fit() before predict_user_items().")
        movie_ids = np.asarray(movie_ids)
        if self.model is None or user_id not in self.user_map:
            return np.full(len(movie_ids), self.global_mean)

        u = self.user_map[user_id]
        user_factor = self.user_factors[u]
        scores = np.full(len(movie_ids), self.global_mean, dtype=np.float64)
        for pos, movie_id in enumerate(movie_ids):
            if movie_id in self.movie_map:
                i = self.movie_map[movie_id]
                scores[pos] = self.global_mean + user_factor @ self.model.components_[:, i]
        return scores