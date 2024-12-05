# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from datetime import datetime, timedelta
# import logging
# import pandas as pd
# from scripts.main import run_extract_stage_1_and_2

# default_args = {
#     'owner': 'airflow',
#     'retries': 1,
#     'retry_delay': timedelta(minutes=5),
#     'start_date': datetime(2024, 12, 5),
# }

# # Define the DAG
# with DAG(
#     'cars24_etl_pipeline',
#     default_args=default_args,
#     description='Cars24 API ETL Pipeline',
#     schedule_interval=None,
#     catchup=False,  # This avoids backfilling, meaning only future runs will be triggered
# ) as dag:


#     def run_combined_extract_task():
#         logging.info("Starting combined Extract Stage 1 and Stage 2")
#         run_extract_stage_1_and_2()

#     combined_extract_task = PythonOperator(
#         task_id='combined_extract',
#         python_callable=run_combined_extract_task,
#         retries=3,
#         retry_delay=timedelta(minutes=5),
#         dag=dag,
#     )



from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import logging
from scripts.main import run_extract_stage_1_and_2

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

    # Task 1: Run combined Extract Stage 1 and Stage 2
    def run_combined_extract_task():
        logging.info("Starting combined Extract Stage 1 and Stage 2")
        run_extract_stage_1_and_2()

    combined_extract_task = PythonOperator(
        task_id='combined_extract',
        python_callable=run_combined_extract_task,
        retries=3,  # Adjust retry logic if needed
        retry_delay=timedelta(minutes=5),
        dag=dag,
    )

    # Task 2: Copy the output file from Docker to the local system
    copy_file_to_local_task = BashOperator(
        task_id='copy_file_to_local',
        bash_command='docker cp cars24_etl_pipeline:/app/output/cars24_final_output.xlsx /output/cars24_final_output.xlsx',
        retries=1,
        dag=dag,
    )

    # Define task dependencies
    combined_extract_task >> copy_file_to_local_task
