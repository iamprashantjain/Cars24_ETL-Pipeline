#!/bin/bash

# Initialize the Airflow database
airflow db init

# Create Airflow admin user
airflow users create \
  --username admin \
  --firstname Airflow \
  --lastname Admin \
  --email admin@example.com \
  --role Admin \
  --password admin

airflow webserver & airflow scheduler