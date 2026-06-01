import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extensions import AsIs

column_mappings = {
        "movies": "(movie_id, title, genres)",
        "links": "(movie_id, imdb_id, tmdb_id)",
        "ratings": "(user_id, movie_id, rating, timestamp)",
        "tags": "(user_id, movie_id, tag, timestamp)"
    }

def _create_movies_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS movies (
        movie_id INT PRIMARY KEY,
        title VARCHAR(255),
        genres VARCHAR(255)
    );
    """
    cursor.execute(create_query)

def _create_links_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS links (
        movie_id INT PRIMARY KEY REFERENCES movies(movie_id),
        imdb_id INT,
        tmdb_id INT
    );
    """
    cursor.execute(create_query)

def _create_ratings_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS ratings (
        user_id INT,
        movie_id INT REFERENCES movies(movie_id),
        rating NUMERIC(2, 1),
        timestamp BIGINT,
        PRIMARY KEY (user_id, movie_id)
    );
    """
    cursor.execute(create_query)

def _create_tags_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS tags (
        tag_id SERIAL PRIMARY KEY,
        user_id INT,
        movie_id INT REFERENCES movies(movie_id),
        tag TEXT,
        timestamp BIGINT
    );
    """
    cursor.execute(create_query)

def _create_metrics_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS model_metrics (
        run_id SERIAL PRIMARY KEY,
        execution_date TIMESTAMP NOT NULL,
        liked_threshold NUMERIC(2, 1),
        min_ratings INT,
        avg_precision_k10 NUMERIC(5, 4),
        avg_recall_k10 NUMERIC(5, 4),
        avg_f1_k10 NUMERIC(5, 4),
        avg_hit_rate_k10 NUMERIC(5, 4)
    );
    """
    cursor.execute(create_query)

def create_tables(cursor):
    _create_movies_table(cursor)
    _create_links_table(cursor)
    _create_ratings_table(cursor)
    _create_tags_table(cursor)
    _create_metrics_table(cursor)


def create_db(DB_CONFIG):
    dbname = DB_CONFIG['dbname']
    conn = psycopg2.connect(**{**DB_CONFIG, "dbname": "airflow"})
    try:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (dbname,))
            if not cursor.fetchone():
                cursor.execute("CREATE DATABASE %s;", (AsIs(dbname),))
                print(f"Database '{dbname}' created successfully.")
            else:
                print(f"Database '{dbname}' already exists. Skipping creation.")
    except Exception as e:
        print(f"An error occurred while creating the database: {e}")
        raise e
    finally:
        conn.close()

def bulk_load_csv(cursor, table_name, file_path):
    cursor.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS fk_{table_name}_movies;")
    cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
    columns = column_mappings.get(table_name, "")
    with open(file_path, 'r') as f:
        sql = f"""
                    COPY {table_name} {columns}
                    FROM STDIN 
                    WITH (FORMAT CSV, HEADER true, DELIMITER ',', QUOTE '"');
                """
        cursor.copy_expert(sql, f)


def reapply_constraints(cursor):
    cursor.execute("ALTER TABLE links DROP CONSTRAINT IF EXISTS fk_links_movies;")
    cursor.execute(
        "ALTER TABLE links ADD CONSTRAINT fk_links_movies FOREIGN KEY (movie_id) REFERENCES movies(movie_id);")

    cursor.execute("ALTER TABLE ratings DROP CONSTRAINT IF EXISTS fk_ratings_movies;")
    cursor.execute(
        "ALTER TABLE ratings ADD CONSTRAINT fk_ratings_movies FOREIGN KEY (movie_id) REFERENCES movies(movie_id);")

    cursor.execute("ALTER TABLE tags DROP CONSTRAINT IF EXISTS fk_tags_movies;")
    cursor.execute("ALTER TABLE tags ADD CONSTRAINT fk_tags_movies FOREIGN KEY (movie_id) REFERENCES movies(movie_id);")
