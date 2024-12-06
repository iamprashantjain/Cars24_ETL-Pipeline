from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import logging
from scripts.main import execute_pipeline

# Default arguments for Airflow tasks
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 12, 6),
}

# Define the DAG
with DAG(
    'cars24_etl_pipeline',
    default_args=default_args,
    description='Cars24 API ETL Pipeline',
    schedule_interval=None,
    catchup=False,
) as dag:

    # Task 1: Run combined Extract Stage 1 and Stage 2
    def run_combined_extract_task():
        logging.info("Starting combined Extract Stage 1 and Stage 2")
        execute_pipeline()

    combined_extract_task = PythonOperator(
        task_id='combined_extract',
        python_callable=run_combined_extract_task,
        retries=3,  # Adjust retry logic if needed
        retry_delay=timedelta(minutes=5),
        execution_timeout=timedelta(minutes=30),
        dag=dag,
    )
    
    
    # ==== since we have mapped volumes between docker container & local system so no need to create a task to copy ====
    # ==== In order to write data to dbs or cloud we need to create a task and write a flow of task ====