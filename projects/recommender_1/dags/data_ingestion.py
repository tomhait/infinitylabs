import os
import psycopg2
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator
from create_tables import create_tables, bulk_load_csv, create_db, reapply_constraints

DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "user": "airflow",
    "password": "airflow",
    "dbname": "movielens"
}

DATA_DIR = "/opt/airflow/dags/data"
REQUIRED_FILES = ["movies.csv", "links.csv", "ratings.csv", "tags.csv"]

def run_ingestion():
    create_db(DB_CONFIG)
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        create_tables(cursor)
        conn.commit()

        for file_name in REQUIRED_FILES:
            table_name = file_name.replace(".csv", "")
            bulk_load_csv(cursor, table_name, os.path.join(DATA_DIR, file_name))
            conn.commit()

        print("All data successfully ingested.")
        reapply_constraints(cursor)
        conn.commit()

        for file_name in REQUIRED_FILES:
            os.remove(os.path.join(DATA_DIR, file_name))

    except Exception as e:
        conn.rollback()
        print(f"Ingestion failed: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()
