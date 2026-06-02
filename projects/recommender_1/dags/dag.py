import sys
import os
import psycopg2
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.sensors.filesystem import FileSensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
import pendulum

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion import run_ingestion, DATA_DIR, REQUIRED_FILES, DB_CONFIG
from data_manipulation import PrepareData
from model_training import TrainModel

DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "user": "airflow",
    "password": "airflow",
    "dbname": "movielens"
}

def run_model_pipeline(liked_th=3.5, min_ratings=200):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        dm = PrepareData(liked_th=liked_th)
        dm.setup(cursor)
        trainer = TrainModel(dm, min_ratings=min_ratings)
        metrics = trainer.train()

        if metrics:
            avg_prec, avg_rec, avg_hit_rate, avg_f1 = metrics

            # select k=10 as baseline for performance comparison
            p_k10 = float(avg_prec[9])
            r_k10 = float(avg_rec[9])
            f1_k10 = float(avg_f1[9])
            hit_rate_k10 = float(avg_hit_rate[9])

            insert_query = """
            INSERT INTO model_metrics (execution_date, liked_threshold, min_ratings, avg_precision_k10, avg_recall_k10, avg_f1_k10, avg_hit_rate_k10)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (liked_th, min_ratings, p_k10, r_k10, f1_k10, hit_rate_k10))
            conn.commit()
            print("Metrics successfully saved to database.")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def run_manipulation(liked_th = 3.5):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    dm = PrepareData(liked_th = liked_th)
    try:
        dm.get_rating_pivot_table(cursor)
        return dm
    except Exception as e:
        print(f"Data manipulation failed: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def run_model_comparison(**kwargs):
    """
    Implement in case there is a new model to perform with
    Return True in case the new model is better
    """
    is_better = False

    if not is_better:
        raise AirflowSkipException("New model performance did not beat the current production model.")

    print("Success! Proceeding to deployment tasks.")
    return True

def run_save_model(model):
    """
    Implement in case there is a better model to be updated
    """
    pass


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2026, 5, 1, tz="UTC"),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'movielens_auto_update',
    default_args=default_args,
    description='Pipeline to monitor, ingest, manipulate and train on MovieLens CSV inputs',
    schedule='@hourly',
    catchup=True,
) as dag:

    sensor_tasks = []
    for file_name in REQUIRED_FILES:
        sensor_task = FileSensor(
            task_id=f'wait_for_{file_name.replace(".", "_")}',
            filepath=os.path.join(DATA_DIR, file_name),
            fs_conn_id='fs_default',
            poke_interval=30,
            timeout=3600,
            mode='reschedule'
        )
        sensor_tasks.append(sensor_task)

    bulk_load_task = PythonOperator(
        task_id='bulk_load_to_movielens_db',
        python_callable=run_ingestion
    )

    train_model_task = PythonOperator(
        task_id='build_and_train_recommender',
        python_callable=run_model_pipeline,
        op_kwargs={'liked_th': 3.5}
    )

    compare_performance_task = PythonOperator(
        task_id='compare_performance_vs_old_model',
        python_callable=run_model_comparison
    )

    save_new_model_task = PythonOperator(
        task_id='save_new_model_task',
        python_callable=run_save_model
    )

    sensor_tasks >> bulk_load_task >> train_model_task >> compare_performance_task >> save_new_model_task
