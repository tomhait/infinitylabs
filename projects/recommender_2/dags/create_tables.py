import io
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extensions import AsIs

column_mappings = {
        "movies": ["movie_id", "title", "genres"],
        "users": ["user_id", "gender", "age", "occupation", "zip_code"],
        "ratings": ["user_id", "movie_id", "rating", "timestamp"]
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

def _create_users_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT PRIMARY KEY,
        gender VARCHAR(1) NOT NULL,
        age INT,
        occupation INT,
        zip_code VARCHAR(10)
    );
    """
    cursor.execute(create_query)

def _create_ratings_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS ratings (
        user_id INT,
        movie_id INT,
        rating NUMERIC(2, 1),
        timestamp BIGINT,
        is_processed BOOLEAN DEFAULT FALSE,
        PRIMARY KEY (user_id, movie_id)
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
        avg_hit_rate_k10 NUMERIC(5, 4),
        avg_mrr_rate_k10 NUMERIC(5, 4),
        avg_ndcg_rate_k10 NUMERIC(5, 4)
    );
    """
    cursor.execute(create_query)

def create_tables(cursor):
    _create_movies_table(cursor)
    _create_users_table(cursor)
    _create_ratings_table(cursor)

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

def _dat_to_tsv_buffer(file_path):
    buffer = io.StringIO()
    row_count = 0
    with open(file_path, "r", encoding="latin-1") as dat_file:
        for line in dat_file:
            buffer.write(line.replace("::", "\t"))
            row_count += 1
    buffer.seek(0)
    return buffer, row_count


staging_schemas = {
    "movies": "movie_id INT, title VARCHAR(255), genres VARCHAR(255)",
    "users": "user_id INT, gender VARCHAR(1), age INT, occupation INT, zip_code VARCHAR(10)",
    "ratings": "user_id INT, movie_id INT, rating NUMERIC(2, 1), timestamp BIGINT",
}

upsert_queries = {
    "movies": """
        INSERT INTO movies (movie_id, title, genres)
        SELECT DISTINCT ON (movie_id) movie_id, title, genres
        FROM {staging}
        ORDER BY movie_id
        ON CONFLICT (movie_id) DO UPDATE SET
            title = EXCLUDED.title,
            genres = EXCLUDED.genres
    """,
    "users": """
        INSERT INTO users (user_id, gender, age, occupation, zip_code)
        SELECT DISTINCT ON (user_id) user_id, gender, age, occupation, zip_code
        FROM {staging}
        ORDER BY user_id
        ON CONFLICT (user_id) DO UPDATE SET
            gender = EXCLUDED.gender,
            age = EXCLUDED.age,
            occupation = EXCLUDED.occupation,
            zip_code = EXCLUDED.zip_code
    """,
    "ratings": """
        INSERT INTO ratings (user_id, movie_id, rating, timestamp)
        SELECT DISTINCT ON (user_id, movie_id) user_id, movie_id, rating, timestamp
        FROM {staging}
        ORDER BY user_id, movie_id, timestamp DESC
        ON CONFLICT (user_id, movie_id) DO UPDATE SET
            rating = EXCLUDED.rating,
            timestamp = EXCLUDED.timestamp
    """,
}

def _drop_ratings_foreign_keys(cursor):
    cursor.execute("""
        DO $$
        DECLARE r RECORD;
        BEGIN
            FOR r IN (
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'ratings'::regclass
                  AND contype = 'f'
            ) LOOP
                EXECUTE format('ALTER TABLE ratings DROP CONSTRAINT IF EXISTS %I', r.conname);
            END LOOP;
        END $$;
    """)


def bulk_load_csv(cursor, table_name, file_path):
    if table_name not in column_mappings:
        raise ValueError(f"Unsupported table '{table_name}'.")

    if table_name == "ratings":
        _drop_ratings_foreign_keys(cursor)

    staging_table = f"{table_name}_staging"
    column_names = column_mappings[table_name]

    cursor.execute(f"DROP TABLE IF EXISTS {staging_table}")
    cursor.execute(
        f"CREATE TEMP TABLE {staging_table} ({staging_schemas[table_name]}) ON COMMIT DROP"
    )

    buffer, row_count = _dat_to_tsv_buffer(file_path)
    cursor.copy_from(
        buffer,
        staging_table,
        sep="\t",
        columns=column_names,
        null="",
    )

    cursor.execute(upsert_queries[table_name].format(staging=staging_table))

    print(f"Upserted {row_count} rows from '{file_path}' into '{table_name}'.")

def reapply_constraints(cursor):
    _drop_ratings_foreign_keys(cursor)
    cursor.execute(
        "ALTER TABLE ratings ADD CONSTRAINT fk_ratings_movies FOREIGN KEY (movie_id) REFERENCES movies(movie_id);")
    cursor.execute(
        "ALTER TABLE ratings ADD CONSTRAINT fk_ratings_users FOREIGN KEY (user_id) REFERENCES users(user_id);")
