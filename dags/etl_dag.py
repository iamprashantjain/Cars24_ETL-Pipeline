from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from datetime import datetime, timedelta
import logging
from scripts.extract import execute_pipeline
from scripts.transform import perform_transformation

# Default arguments for Airflow tasks
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 12, 6),
}

#file path
RAW_DATA_FILE_PATH = '/app/output/cars24_raw_data.xlsx'
TRANSFORMED_DATA_FILE_PATH = '/app/output/cars24_transformed_data.xlsx'

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
        task_id='extract_stage',
        python_callable=run_combined_extract_task,
        retries=3,  # Adjust retry logic if needed
        retry_delay=timedelta(minutes=5),
        execution_timeout=timedelta(minutes=30),
        dag=dag,
    )    

    # Task 2: Check if raw data file is saved
    check_raw_data_file = FileSensor(
        task_id='check_raw_data_file',
        filepath=RAW_DATA_FILE_PATH,
        poke_interval=30,  # Check every 30 seconds
        timeout=600,  # Timeout after 10 minutes
        mode='poke',  # 'poke' mode keeps the worker busy; consider 'reschedule' for larger systems
        dag=dag,
    )

    # Task 3: Perform the transformation stage
    def run_transform_task():
        logging.info("Starting Transformation Stage")
        perform_transformation()

    transform_task = PythonOperator(
        task_id='transform_stage',
        python_callable=run_transform_task,
        retries=3,  # Adjust retry logic if needed
        retry_delay=timedelta(minutes=5),
        execution_timeout=timedelta(minutes=30),
        dag=dag,
    )

    # Task 4: Check if transformed data file is saved
    check_transformed_data_file = FileSensor(
        task_id='check_transformed_data_file',
        filepath=TRANSFORMED_DATA_FILE_PATH,
        poke_interval=30,  # Check every 30 seconds
        timeout=600,  # Timeout after 10 minutes
        mode='poke',  # 'poke' mode keeps the worker busy; consider 'reschedule' for larger systems
        dag=dag,
    )

    # Define task dependencies
    combined_extract_task >> check_raw_data_file >> transform_task >> check_transformed_data_file