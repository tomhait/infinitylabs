"""
The main is for applying Ex. 3
Test the load to DB scalability
"""
import psycopg2
from .dags.create_tables import create_tables, bulk_load_csv, create_db
from timer import func_timer

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "airflow",
    "password": "airflow",
    "dbname": "movielens"
}

@func_timer
def main():
    create_db(DB_CONFIG)
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        create_tables(cursor)
        conn.commit()
        bulk_load_csv(cursor, "movies", "ml-latest-small/movies.csv")
        bulk_load_csv(cursor, "links", "ml-latest-small/links.csv")
        bulk_load_csv(cursor, "ratings", "ml-latest-small/ratings.csv")
        bulk_load_csv(cursor, "tags", "ml-latest-small/tags.csv")
        conn.commit()

    except Exception as e:
            conn.rollback()
            print(f"An error occurred: {e}")
    finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()