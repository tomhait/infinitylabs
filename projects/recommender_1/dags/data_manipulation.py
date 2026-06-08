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
        self.links = None

    def setup(self, cursor):
        try:
            self.ratings = pd.read_sql_query("SELECT * FROM ratings;", cursor.connection)
            print(f"Successfully retrieved {len(self.ratings)} rows from ratings.")

            self.ratings.columns = [
                'userId' if c == 'user_id' else 'movieId' if c == 'movie_id' else c
                for c in self.ratings.columns
            ]

            self.movies = pd.read_sql_query("SELECT * FROM movies;", cursor.connection)
            self.movies.columns = [
                'movieId' if c == 'movie_id' else c for c in self.movies.columns
            ]
            print(f"Successfully retrieved {len(self.movies)} rows from movies.")

            self.links = pd.read_sql_query("SELECT * FROM links;", cursor.connection)
            self.links.columns = [
                'movieId' if c == 'movie_id' else 'imdbId' if c == 'imdb_id' else c
                for c in self.links.columns
            ]
            self.links['imdbId'] = self.links['imdbId'].apply(
                lambda x: f"tt{str(int(x)).zfill(7)}" if pd.notna(x) else None
            )

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

    def get_links(self):
        return self.links
