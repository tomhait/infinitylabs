from data_manipulation import PrepareData
from sklearn.model_selection import train_test_split
from model import NaiveBayesRecommender
from metrics import calculate_performance_k
import numpy as np

class TrainModel:
    def __init__(self, dm: PrepareData, min_ratings = 200):
        self.min_ratings = min_ratings
        self.dm = dm

    def _get_tested_users(self):
        num_ratings_per_user = self.dm.get_num_ratings_per_user()
        filtered_users = num_ratings_per_user[num_ratings_per_user >= self.min_ratings].index.tolist()

        print(f"Number of users with at least {self.min_ratings} ratings: {len(filtered_users)}")
        return filtered_users

    def _get_user_train_test(self, user_id):
        ratings = self.dm.get_ratings()
        user_ratings = ratings[ratings['userId'] == user_id]
        user_liked_movie_ids = user_ratings[user_ratings['rating'] >= self.dm.liked_th]
        user_liked_movie_ids = user_liked_movie_ids.sort_values(by='timestamp', ascending=False)['movieId'].unique()[
            :self.min_ratings]
        user_liked_movie_ids = user_liked_movie_ids[::-1]
        if len(user_liked_movie_ids) < 5:
            return [], []
        trainMovies, testMovies = train_test_split(user_liked_movie_ids, shuffle=False, test_size=0.2, random_state=42)
        return trainMovies, testMovies

    def _train_single(self, recommender, user_id):
        trainMovies, testMovies = self._get_user_train_test(user_id)
        recommendations_df, message = recommender.recommend(user_id=user_id, train_movies=trainMovies,
                                                            test_movies=testMovies)
        if message:
            print(message)
            return None
        prec, rec, hit_rates_user = [], [], []
        for k in range(1, self.min_ratings):
            hit_rate, pr, rc = calculate_performance_k(recommendations_df, testMovies, k=k)
            prec.append(pr)
            rec.append(rc)
            hit_rates_user.append(hit_rate)
        return prec, rec, hit_rates_user

    def _calc_metrics(self, prec, rec, hit_rates):
        precisions_array = np.array(prec)
        recalls_array = np.array(rec)
        hit_rates_array = np.array(hit_rates)
        average_prec_per_k = np.mean(precisions_array, axis=0)
        average_rec_per_k = np.mean(recalls_array, axis=0)
        average_hit_rates_per_k = np.mean(hit_rates_array, axis=0)

        denominator = average_prec_per_k + average_rec_per_k
        average_f1_per_k = np.divide(2 * average_prec_per_k * average_rec_per_k, denominator,
                                     out=np.zeros_like(denominator), where=denominator != 0)
        return average_prec_per_k, average_rec_per_k, average_hit_rates_per_k, average_f1_per_k

    def train(self):
        liked_df = self.dm.get_liked_df()
        movies = self.dm.get_movies()
        movie_rating_counts = self.dm.get_movie_rating_count()
        users_with_at_least_n_ratings = self._get_tested_users()
        recommender = NaiveBayesRecommender(liked_df, movies, movie_rating_counts)
        all_prec = []
        all_rec = []
        all_hit_rates = []
        for user_id in users_with_at_least_n_ratings:
            res = self._train_single(recommender, user_id)
            if not res:
                continue
            all_prec.append(res[0])
            all_rec.append(res[1])
            all_hit_rates.append(res[2])
        return self._calc_metrics(all_prec, all_rec, all_hit_rates)



