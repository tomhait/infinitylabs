from datetime import datetime, timedelta
import os
import psycopg2
from airflow import DAG
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


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 30),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
        'movielens_auto_update',
        default_args=default_args,
        description='Automatically update MovieLens CSVs when they appear',
        schedule='*/5 * * * *',
        catchup=False,
) as dag:
    process_data = PythonOperator(
        task_id='bulk_load_to_movielens_db',
        python_callable=run_ingestion
    )
    for file_name in REQUIRED_FILES:
        sensor_task = FileSensor(
            task_id=f'wait_for_{file_name.replace(".", "_")}',
            filepath=os.path.join(DATA_DIR, file_name),
            fs_conn_id='fs_default',
            poke_interval=30,
            timeout=3600,
            mode='reschedule'
        )
        sensor_task >> process_data