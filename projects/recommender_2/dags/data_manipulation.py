import pandas as pd

class PrepareData:
    def __init__(self, liked_th = 3.5):
        self.liked_th = liked_th
        self.liked_df = None
        self.rating_pivot = None
        self.movie_rating_counts = None
        self.num_ratings_per_user = None
        self.ratings = None
        self.movies = None
        self.users = None
        self.links = None

    def setup(self, cursor):
        try:
            self.ratings = pd.read_sql_query(
                "SELECT user_id, movie_id, rating, timestamp FROM ratings;",
                cursor.connection,
            )
            print(f"Successfully retrieved {len(self.ratings)} rows from ratings.")

            self.ratings.columns = [
                'userId' if c == 'user_id' else 'movieId' if c == 'movie_id' else c
                for c in self.ratings.columns
            ]

            self.movies = pd.read_sql_query(
                "SELECT movie_id, title, genres FROM movies;",
                cursor.connection,
            )
            self.movies.columns = [
                'movieId' if c == 'movie_id' else c for c in self.movies.columns
            ]
            print(f"Successfully retrieved {len(self.movies)} rows from movies.")

            self.users = pd.read_sql_query(
                "SELECT user_id, gender, age, occupation, zip_code FROM users;",
                cursor.connection,
            )
            self.users.columns = [
                'userId' if c == 'user_id' else 'zipCode' if c == 'zip_code' else c
                for c in self.users.columns
            ]
            print(f"Successfully retrieved {len(self.users)} rows from users.")

            self.links = pd.DataFrame(columns=['movieId', 'imdbId'])

            self.num_ratings_per_user = self.ratings['userId'].value_counts()
            self.movie_rating_counts = self.ratings['movieId'].value_counts()

            self.rating_pivot = self.ratings.pivot_table(
                index='movieId', columns='userId', values='rating'
            ).fillna(0)

            print('Shape of ratings pivot table:', self.rating_pivot.shape)
            self.liked_df = (self.rating_pivot >= self.liked_th).astype(int)
        except Exception as e:
            print(f"Error while manipulating data: {e}")
            raise e

    def get_liked_df(self):
        return self.liked_df

    def get_ratings_pivot(self):
        return self.rating_pivot

    def get_movie_rating_count(self):
        return self.movie_rating_counts

    def get_num_ratings_per_user(self):
        return self.num_ratings_per_user

    def get_ratings(self):
        return self.ratings

    def get_movies(self):
        return self.movies

    def get_users(self):
        return self.users

    def get_links(self):
        return self.links
