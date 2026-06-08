import polars as pl
import os

class PrepareData:
    def __init__(self, liked_th = 3.5, parquet_dir="/opt/airflow/dags/data/parquet"):
        self.liked_th = liked_th
        self.parquet_path = os.path.join(parquet_dir, "ratings_history.parquet")
        os.makedirs(parquet_dir, exist_ok=True)

        self.liked_df = None
        self.rating_pivot = None
        self.movie_rating_counts = None
        self.num_ratings_per_user = None
        self.ratings = None
        self.movies = None
        self.links = None

    def setup(self, cursor, conn_uri):
        try:
            new_ratings_query = "SELECT user_id, movie_id, rating, timestamp FROM ratings WHERE is_processed = FALSE;"
            new_ratings = pl.read_database_uri(query=new_ratings_query, uri=conn_uri)
            print(f"Retrieved {new_ratings.height} new rows from ratings.")

            if new_ratings.height > 0:
                new_ratings = new_ratings.rename({'user_id': 'userId', 'movie_id': 'movieId'})

            if os.path.exists(self.parquet_path):
                historical_ratings = pl.read_parquet(self.parquet_path)
                if new_ratings.height > 0:
                    self.ratings = pl.concat([historical_ratings, new_ratings])
                    self.ratings.write_parquet(self.parquet_path)
                else:
                    self.ratings = historical_ratings
            else:
                self.ratings = new_ratings
                self.ratings.write_parquet(self.parquet_path)

            if new_ratings.height > 0:
                cursor.execute("UPDATE ratings SET is_processed = TRUE WHERE is_processed = FALSE;")
                cursor.connection.commit()

            self.movies = pl.read_database_uri(query="SELECT * FROM movies;", uri=conn_uri).rename(
                {'movie_id': 'movieId'})

            self.links = pl.read_database_uri(query="SELECT * FROM links;", uri=conn_uri).rename(
                {'movie_id': 'movieId', 'imdb_id': 'imdbId'})

            self.links = self.links.with_columns(
                pl.when(pl.col("imdbId").is_not_null())
                .then(
                    pl.lit("tt") + pl.col("imdbId").cast(pl.Int64).cast(pl.String).str.zfill(7)
                )
                .otherwise(None)
                .alias("imdbId")
            )

            self.num_ratings_per_user = self.ratings.group_by("userId").count()
            self.movie_rating_counts = self.ratings.group_by("movieId").count()

            print('Pivoting matrix via Polars...')
            self.rating_pivot = (
                self.ratings
                .pivot(index="movieId", on="userId", values="rating")
                .fill_null(0)
            )

            movie_id_col = self.rating_pivot["movieId"]
            matrix_only = self.rating_pivot.drop("movieId")

            self.liked_df = matrix_only.select([
                (pl.col(c) >= self.liked_th).cast(pl.Int8).alias(c) for c in matrix_only.columns
            ])
            self.liked_df.insert_column(0, movie_id_col)

        except Exception as e:
            print(f"Error while manipulating data: {e}")
            raise e

    def get_liked_df(self):
        df = self.liked_df.to_pandas().set_index("movieId")
        df.columns = df.columns.astype(int)
        return df

    def get_ratings_pivot(self):
        df = self.rating_pivot.to_pandas().set_index("movieId")
        df.columns = df.columns.astype(int)
        return df

    def get_movie_rating_count(self):
        return self.movie_rating_counts.to_pandas().set_index("movieId")["count"]

    def get_num_ratings_per_user(self):
        return self.num_ratings_per_user.to_pandas().set_index("userId")["count"]

    def get_ratings(self):
        return self.ratings.to_pandas()

    def get_movies(self):
        return self.movies.to_pandas()

    def get_links(self):
        return self.links.to_pandas()
