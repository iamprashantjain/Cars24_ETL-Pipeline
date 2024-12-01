- This is a ETL Pipeline project of my Initial `Used car Price Prediction tool`.
- I'll be extracting data on a regular interval "Weekly/Monthly", saving it to cloud/dbs/locally using Docker & Airflow
- This Data will be used on my currently running project to perform `Continous Training`
- Folder Structure looks like below:


cars24_data_etl_pipeline/
├── dags/
│   └── cars24_etl_pipeline.py  #airflow DAG file
├── scripts/
│   ├── cars24_api_extract1.py
│   ├── cars24_api_extract2.py
│   ├── cars24_api_transform.py
│   ├── cars24_api_load.py
├── output/  <-- Folder where files will be saved and read by scripts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt


**Remove All Images**
`docker images`
`for /f %i in ('docker images -q') do docker rmi -f %i`