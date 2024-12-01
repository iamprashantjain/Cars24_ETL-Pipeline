from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import sys
import os
from exception.exception import customexception
from logger.logging import logging

# Import the extraction, transformation, and loading functions from your scripts
from scripts.cars24_api_extract1 import extract_stage1
from scripts.cars24_api_extract2 import extract_stage2
from scripts.cars24_api_transform import transform_data
from scripts.cars24_api_load import load_data

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 11, 30),  # Replace with the actual start date
    'retries': 1,
    'catchup': False,  # To avoid running the DAG for past dates
}

# Define the DAG
dag = DAG(
    'cars24_etl_pipeline',
    default_args=default_args,
    description='Cars24 ETL pipeline for extracting, transforming, and loading data',
    schedule_interval='@weekly',  # Schedule it to run daily
    catchup=False,
)

# Task 1: Run Stage 1 extraction (cars24_api_extract1.py)
extract_stage1_task = PythonOperator(
    task_id='extract_stage1',
    python_callable=extract_stage1,
    dag=dag,
)

# Task 2: Run Stage 2 extraction (cars24_api_extract2.py) - depends on Stage 1 completion
extract_stage2_task = PythonOperator(
    task_id='extract_stage2',
    python_callable=extract_stage2,
    dag=dag,
)

# # Task 3: Transform the data (cars24_api_transform.py) - depends on Stage 2 completion
# transform_data_task = PythonOperator(
#     task_id='transform_data',
#     python_callable=transform_data,
#     dag=dag,
# )

# # Task 4: Load the transformed data to S3 (cars24_api_load.py) - depends on transformation completion
# load_data_task = PythonOperator(
#     task_id='load_data',
#     python_callable=load_data,
#     dag=dag,
# )

# Define task dependencies to enforce the order of execution
# extract_stage1_task >> extract_stage2_task >> transform_data_task >> load_data_task
extract_stage1_task >> extract_stage2_task