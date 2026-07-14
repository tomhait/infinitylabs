import sys
import os
import psycopg2
from datetime import timedelta
from airflow import DAG
from airflow.providers.standard.sensors.filesystem import FileSensor
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowSkipException
import pendulum

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion import run_ingestion, DATA_DIR, REQUIRED_FILES, DB_CONFIG
from data_manipulation import PrepareData
from model_training import (
    TrainNaiveBayesModel,
    TrainFactorMachineModel,
    TrainOneBPModel,
    evaluate_artifact_on_splits,
    evaluate_production_on_splits,
)
from model_storage import (
    PRODUCTION_FM_KWARGS,
    PRODUCTION_ONEBP_KWARGS,
    SUPPORTED_CANDIDATE_MODELS,
    CANDIDATE_MODEL_PATH,
    get_production_model_type,
    load_production_model,
    load_candidate_model,
    save_candidate_model,
    promote_candidate_to_production,
    ensure_model_dir,
)

DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "user": "airflow",
    "password": "airflow",
    "dbname": "movielens_1m"
}

EVAL_LIKED_TH = 4.0

# CANDIDATE_MODEL = os.getenv('CANDIDATE_MODEL', 'factorization_machine')
CANDIDATE_MODEL = os.getenv('CANDIDATE_MODEL', 'onebp')

def _save_metrics(cursor, conn, liked_th, min_ratings, metrics, top_k):
    avg_prec, avg_rec, avg_hit_rate, avg_f1, avg_mrr, avg_ndcg = metrics
    k = top_k - 1
    insert_query = """
    INSERT INTO model_metrics (
        execution_date, liked_threshold, min_ratings,
        avg_precision_k10, avg_recall_k10, avg_f1_k10, avg_hit_rate_k10,
        avg_mrr_rate_k10, avg_ndcg_rate_k10
    )
    VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s);
    """
    cursor.execute(
        insert_query,
        (
            liked_th,
            min_ratings,
            float(avg_prec[k]),
            float(avg_rec[k]),
            float(avg_f1[k]),
            float(avg_hit_rate[k]),
            float(avg_mrr[k]),
            float(avg_ndcg[k]),
        ),
    )
    conn.commit()
    print("Metrics successfully saved to database.")


def _build_eval_splits(dm, min_ratings, min_popularity, top_k):
    trainer = TrainNaiveBayesModel(
        dm,
        min_ratings=min_ratings,
        min_popularity=min_popularity,
        max_eval_k=top_k,
    )
    return trainer._build_user_splits()


def run_model_pipeline(liked_th=EVAL_LIKED_TH, min_ratings=200, min_popularity=20, top_k=10):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        dm = PrepareData(liked_th=liked_th)
        dm.setup(cursor)
        model_type = get_production_model_type()
        production = load_production_model()

        if model_type == 'factorization_machine' and production is not None:
            trainer_config = production.get('trainer_config', {})
            fm_kwargs = {**PRODUCTION_FM_KWARGS, **trainer_config}
            fm_kwargs.pop('liked_th', None)
            fm_kwargs.pop('eval_liked_th', None)
            fm_kwargs.pop('min_ratings', None)
            fm_kwargs.pop('min_popularity', None)
            trainer = TrainFactorMachineModel(
                dm,
                min_ratings=min_ratings,
                min_popularity=min_popularity,
                max_eval_k=top_k,
                **fm_kwargs,
            )
            print("Using Factorization Machine production model.")
            metrics = trainer.train()
        elif model_type == 'onebp' and production is not None:
            print("Using OneBP production model.")
            splits = _build_eval_splits(dm, min_ratings, min_popularity, top_k)
            metrics = evaluate_production_on_splits(
                dm,
                production,
                min_ratings=min_ratings,
                min_popularity=min_popularity,
                top_k=top_k,
                splits=splits,
            )
        else:
            trainer = TrainNaiveBayesModel(
                dm,
                min_ratings=min_ratings,
                min_popularity=min_popularity,
                max_eval_k=top_k,
            )
            print("Using Naive Bayes production model.")
            metrics = trainer.train()

        if metrics:
            _save_metrics(cursor, conn, liked_th, min_ratings, metrics, top_k)

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def run_train_fm_candidate(liked_th=EVAL_LIKED_TH, min_ratings=200, min_popularity=20, **kwargs):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        dm = PrepareData(liked_th=liked_th)
        dm.setup(cursor)
        trainer = TrainFactorMachineModel(
            dm,
            min_ratings=min_ratings,
            min_popularity=min_popularity,
            **PRODUCTION_FM_KWARGS,
        )
        model, feature_info = trainer.fit_production()
        artifact = {
            'model_type': 'factorization_machine',
            'model': model,
            'feature_info': feature_info,
            'trainer_config': {
                'eval_liked_th': liked_th,
                'min_ratings': min_ratings,
                'min_popularity': min_popularity,
                **PRODUCTION_FM_KWARGS,
            },
        }
        save_candidate_model(artifact)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def run_train_onebp_candidate(liked_th=EVAL_LIKED_TH, min_ratings=200, min_popularity=20, **kwargs):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        dm = PrepareData(liked_th=liked_th)
        dm.setup(cursor)
        trainer = TrainOneBPModel(
            dm,
            min_ratings=min_ratings,
            min_popularity=min_popularity,
            **PRODUCTION_ONEBP_KWARGS,
        )
        trainer.train()
        if trainer.model_artifact is None:
            raise RuntimeError("OneBP training did not produce a model artifact.")
        artifact = trainer.model_artifact
        artifact['trainer_config'] = {
            'eval_liked_th': liked_th,
            'min_ratings': min_ratings,
            'min_popularity': min_popularity,
            **PRODUCTION_ONEBP_KWARGS,
            **{
                k: v for k, v in artifact.get('trainer_config', {}).items()
                if k not in ('eval_liked_th', 'min_ratings', 'min_popularity')
            },
        }
        save_candidate_model(artifact)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def run_train_candidate(
    candidate_model='factorization_machine',
    liked_th=EVAL_LIKED_TH,
    min_ratings=200,
    min_popularity=20,
    **kwargs,
):
    trainers = {
        'factorization_machine': run_train_fm_candidate,
        'onebp': run_train_onebp_candidate,
    }
    if candidate_model not in trainers:
        supported = ', '.join(SUPPORTED_CANDIDATE_MODELS)
        raise ValueError(
            f"Unsupported candidate_model={candidate_model!r}. "
            f"Choose one of: {supported}"
        )
    print(f"Training candidate model: {candidate_model}")
    return trainers[candidate_model](
        liked_th=liked_th,
        min_ratings=min_ratings,
        min_popularity=min_popularity,
        **kwargs,
    )


def run_model_comparison(liked_th=EVAL_LIKED_TH, min_ratings=200, min_popularity=20, top_k=10, **kwargs):
    candidate = load_candidate_model()
    if candidate is None:
        raise AirflowSkipException(
            f"No candidate pickle found at {CANDIDATE_MODEL_PATH}."
        )

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        dm = PrepareData(liked_th=liked_th)
        dm.setup(cursor)
        splits = _build_eval_splits(dm, min_ratings, min_popularity, top_k)

        production = load_production_model()
        prod_type = get_production_model_type() if production else 'naive_bayes'
        candidate_type = candidate.get('model_type', 'factorization_machine')

        prod_metrics = evaluate_production_on_splits(
            dm,
            production,
            min_ratings=min_ratings,
            min_popularity=min_popularity,
            top_k=top_k,
            splits=splits,
        )
        candidate_metrics = evaluate_artifact_on_splits(
            dm,
            candidate,
            min_ratings=min_ratings,
            min_popularity=min_popularity,
            top_k=top_k,
            splits=splits,
        )

        prod_ndcg = float(prod_metrics[5][top_k - 1])
        candidate_ndcg = float(candidate_metrics[5][top_k - 1])
        print(f"Production ({prod_type}) NDCG @k={top_k}: {prod_ndcg:.4f}")
        print(f"Candidate ({candidate_type}) NDCG @k={top_k}: {candidate_ndcg:.4f}")
        is_better = candidate_ndcg > prod_ndcg
    finally:
        cursor.close()
        conn.close()

    if not is_better:
        raise AirflowSkipException(
            "Candidate model NDCG did not beat the current production model."
        )

    print("Success! Proceeding to deployment tasks.")
    return True


def run_save_model(**kwargs):
    candidate = load_candidate_model()
    if candidate is None:
        raise AirflowSkipException(
            f"No candidate model to promote at {CANDIDATE_MODEL_PATH}."
        )
    promote_candidate_to_production()


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2026, 6, 7, tz="UTC"),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

ensure_model_dir()

with DAG(
    'movielens_auto_update',
    default_args=default_args,
    description='Pipeline to monitor, ingest, manipulate and train on MovieLens CSV inputs',
    schedule='@hourly',
    catchup=False,
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
        op_kwargs={'liked_th': EVAL_LIKED_TH},
    )

    train_candidate_task = PythonOperator(
        task_id='train_candidate_model',
        python_callable=run_train_candidate,
        op_kwargs={
            'liked_th': EVAL_LIKED_TH,
            'candidate_model': CANDIDATE_MODEL,
        },
    )

    wait_for_candidate_model_task = FileSensor(
        task_id='wait_for_candidate_model_pkl',
        filepath=CANDIDATE_MODEL_PATH,
        fs_conn_id='fs_default',
        poke_interval=30,
        timeout=3600,
        mode='reschedule',
    )

    compare_performance_task = PythonOperator(
        task_id='compare_performance_vs_old_model',
        python_callable=run_model_comparison,
        op_kwargs={'liked_th': EVAL_LIKED_TH},
    )

    save_new_model_task = PythonOperator(
        task_id='save_new_model_task',
        python_callable=run_save_model,
    )

    sensor_tasks >> bulk_load_task >> train_model_task >> save_new_model_task
    wait_for_candidate_model_task >> train_candidate_task >> compare_performance_task >> save_new_model_task
