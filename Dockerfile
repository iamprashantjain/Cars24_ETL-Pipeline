FROM python:3.8-slim-buster

# Use root user to install dependencies
USER root

# Set environment variable for Airflow home directory
ENV AIRFLOW_HOME=/app/airflow

# Set working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install system dependencies and Python packages
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install apache-airflow[flask] flask-session pendulum==2.1.2

# Set Airflow-specific environment variables
ENV AIRFLOW_CORE_DAGBAG_IMPORT_TIMEOUT=10000
ENV AIRFLOW_CORE_ENABLE_XCOM_PICKLING=True

# Copy the rest of your application code
COPY . /app/

# Make start.sh executable
RUN chmod +x start.sh

# Set the entry point for the container
ENTRYPOINT ["/bin/sh", "start.sh"]