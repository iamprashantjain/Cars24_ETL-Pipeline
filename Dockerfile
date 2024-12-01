# Use the official Airflow image from Apache as the base image
FROM apache/airflow:2.5.0

# Install any additional Python packages your DAG requires
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set the Airflow home directory
ENV AIRFLOW_HOME=/opt/airflow

# Set the working directory to the Airflow home
WORKDIR $AIRFLOW_HOME

# Copy the DAGs and Python scripts into the container
COPY ./dags /opt/airflow/dags
COPY ./scripts /opt/airflow/scripts

# Expose the Airflow UI port
EXPOSE 8080

# Run the Airflow webserver by default (this can be changed later)
ENTRYPOINT ["airflow"]
CMD ["webserver"]