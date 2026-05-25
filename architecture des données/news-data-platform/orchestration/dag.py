from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Ajouter le répertoire racine au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraping.hespress_scraper import main as scrape_data
from processing.clean_data import main as clean_data
from processing.transform import main as transform_data
from ingestion.batch_ingestion import run_batch_ingestion

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'news_data_pipeline',
    default_args=default_args,
    description='Pipeline de données pour la collecte et analyse d\'articles de presse',
    schedule_interval=timedelta(days=1),  # Exécution quotidienne
    catchup=False,
    tags=['news', 'scraping', 'data-engineering'],
)

# Tâche 1: Scraping des données
scrape_task = PythonOperator(
    task_id='scrape_articles',
    python_callable=scrape_data,
    dag=dag,
)

# Tâche 2: Nettoyage des données (Bronze -> Silver)
clean_task = PythonOperator(
    task_id='clean_data',
    python_callable=clean_data,
    dag=dag,
)

# Tâche 3: Transformation et analyse (Silver -> Gold)
transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

# Tâche 4: Ingestion dans PostgreSQL
ingest_task = PythonOperator(
    task_id='ingest_to_database',
    python_callable=run_batch_ingestion,
    dag=dag,
)

# Définir les dépendances
scrape_task >> clean_task >> transform_task >> ingest_task