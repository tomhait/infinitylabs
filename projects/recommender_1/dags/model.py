import numpy as np

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