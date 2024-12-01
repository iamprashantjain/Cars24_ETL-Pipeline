import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
from exception.exception import customexception
from logger.logging import logging

warnings.filterwarnings('ignore')

def fetch_data(city_id):
    print(city_id)
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.cars24.com',
        'referer': 'https://www.cars24.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'x-user-city-id': str(city_id),
    }
    json_data = {
        'searchFilter': [],
        'cityId': city_id,
        'sort': 'bestmatch',
        'size': 1000,
        'searchAfter': [20.105531692504883, '10212333714'],
    }
    try:
        response = requests.post('https://b2c-catalog-gateway.c24.tech/listing/v1/buy-used-car', headers=headers, json=json_data, verify=False)
        return pd.DataFrame(response.json().get('content', []))
    except Exception as e:
        # print(f"Error for city_id {city_id}: {e}")
        return pd.DataFrame()


city_ids = range(1, 100000000)
final_df = pd.DataFrame()

logging.info("Appointment ID extraction started")
with ThreadPoolExecutor(max_workers=500) as executor:
    futures = [executor.submit(fetch_data, city_id) for city_id in city_ids]
    for future in as_completed(futures):
        df = future.result()
        if not df.empty:
            final_df = pd.concat([final_df, df], ignore_index=True)
            # print(final_df.shape)
            
logging.info("Appointment ID extraction finished")

output_file_path = '/opt/airflow/output/cars24_stage1_output.xlsx'
final_df.to_excel(output_file_path, index=False)
# final_df.to_excel('cars24_appointment_ids.xlsx', index=False)