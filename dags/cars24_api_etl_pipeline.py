from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging
import pandas as pd
from scripts.cars24_api_extract1 import run_extract_stage_1
from scripts.cars24_api_extract2 import run_extract_stage_2

# Default arguments for Airflow tasks
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 12, 5),  # Adjust the start date accordingly
}

# Define the DAG
with DAG(
    'cars24_etl_pipeline',
    default_args=default_args,
    description='Cars24 API ETL Pipeline',
    schedule_interval=None,  # Set this to None to trigger the DAG manually, or use a cron expression for scheduled runs
    catchup=False,  # This avoids backfilling, meaning only future runs will be triggered
) as dag:

    # Task 1: Run Extract Stage 1
    def run_extract_stage_1_task():
        city_ids = range(150, 200)  # Modify the range as needed, based on your data
        logging.info(f"Starting Extract Stage 1 with city IDs: {city_ids}")
        return run_extract_stage_1(city_ids)

    extract_stage_1_task = PythonOperator(
        task_id='extract_stage_1',
        python_callable=run_extract_stage_1_task,
        retries=3,  # Adjust retry logic if needed
        retry_delay=timedelta(minutes=5),
        dag=dag,
    )

    # Task 2: Run Extract Stage 2 (depends on Task 1)
    def run_extract_stage_2_task():
        # Read the appointment IDs from the output of Extract Stage 1
        # input_file_path = '/opt/airflow/output/cars24_stage1_output.xlsx'
        input_file_path = '/app/output/cars24_stage1_output.xlsx'
        try:
            temp_df = pd.read_excel(input_file_path)
            appointment_ids = temp_df['appointmentId'].tolist()
            logging.info(f"Starting Extract Stage 2 with appointment IDs: {appointment_ids}")
            return run_extract_stage_2(appointment_ids)
        except Exception as e:
            logging.error(f"Error reading the file {input_file_path}: {e}")
            raise  # This will cause the task to fail

    extract_stage_2_task = PythonOperator(
        task_id='extract_stage_2',
        python_callable=run_extract_stage_2_task,
        retries=3,  # Adjust retry logic if needed
        retry_delay=timedelta(minutes=5),
        dag=dag,
    )

    # Define task dependencies
    extract_stage_1_task >> extract_stage_2_task