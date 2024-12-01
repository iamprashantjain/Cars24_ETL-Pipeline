import os
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
from collections import defaultdict
import pdb
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings;warnings.filterwarnings('ignore')
from exception.exception import customexception
from logger.logging import logging



# Load the appointment IDs
logging.info("reading appointment id from cars24_appointment_ids.xlsx")

input_file_path = '/opt/airflow/output/cars24_stage1_output.xlsx'
temp_df = pd.read_excel(input_file_path)
appointmentIds = temp_df['appointmentId'].tolist()

count = 1

def process_appointment(appointment):
    global count

    print(count)
    count += 1

    # Cookies and headers for the request
    cookies = {
        'statsigStableId': '477af838-cc81-4f93-9d88-dbce466d0236',
        '__cf_bm': 'PNHy10im3k0KCzHrN8t8s6sCwItrokXwMSr65ssmbsY-1727597780-1.0.1.1-wJizfeeqs.ZTyoYFtcGce.qv29SMhnLXOy0eHPNKa92GlQ3x3bDFdEnWwI8oz86c.nmdzRcMc05RAlqrXsQYZA',
        'c24-city': 'noida',
        'user_selected_city': '134',
        'pincode': '201301'
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.7',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Brave";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'sec-gpc': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }

    try:
        # Send GET request
        response = requests.get(
            f'https://www.cars24.com/buy-used-honda-city-2023-cars-new-delhi-{appointment}/',
            cookies=cookies,
            headers=headers,
        )

        # Parse the response content
        soup = BeautifulSoup(response.content, 'html.parser')
        script = soup.find('script', text=lambda t: t and '__PRELOADED_STATE__' in t)

        # Extract JSON content from the script tag
        js_content = script.string.strip()
        start_idx = js_content.find('{')
        end_idx = js_content.rfind('}') + 1
        json_content = js_content[start_idx:end_idx]

        # Load the JSON data
        data = json.loads(json_content)
        car_details_data = data.get('carDetails', [])

        # Normalize the nested data into a DataFrame
        car_details_df = pd.json_normalize(car_details_data)

        # Prepare to collect data3
        data3_dict = defaultdict(list)

        if car_details_df['specsFeatures'].empty or car_details_df['specsFeatures'][0] == []:
            # If specsFeatures is empty, add a column with "not available"
            car_details_df['specs_tag'] = 'not available'

        else:
            for index, row in car_details_df.iterrows():
                data1 = row['specsFeatures']
                if data1:
                    for specs in data1:
                        if 'data' in specs:
                            for item in specs['data']:
                                data3_dict[item['key']].append(item['value'])


            car_details_df['specs_tag'] = 'available'


        # Prepare to collect data4
        data4_dict = defaultdict(list)
        data2 = car_details_df['carImperfectionPanelData'][0]
        for item in data2:
            if item['key'] == 'tyresLife':
                for tyre in item['data']:
                    data4_dict[tyre['label']].append(tyre['status'])
            else:
                data4_dict[item['key']].append(item.get('count'))

        # Flatten the collected data into DataFrame columns
        for key, values in data3_dict.items():
            car_details_df[key] = pd.Series(values)

        for key, values in data4_dict.items():
            car_details_df[key] = pd.Series(values)

        # Specify the columns to keep
        specified_columns = [
            'content.appointmentId', 'content.make', 'content.model', 
            'content.variant', 'content.year', 'content.transmission', 
            'content.bodyType', 'content.fuelType', 'content.ownerNumber', 
            'content.odometerReading', 'content.cityRto', 'content.registrationNumber', 
            'content.listingPrice', 'content.onRoadPrice', 'content.fitnessUpto', 
            'content.insuranceType', 'content.insuranceExpiry', 
            'content.lastServicedAt', 'content.duplicateKey', 'content.city','specs_tag'
        ]

        # Combine all columns
        all_columns = specified_columns + list(data3_dict.keys()) + list(data4_dict.keys())
        car_details_df = car_details_df[all_columns]

        return car_details_df

    except Exception as e:
        return pd.DataFrame()


final_df = pd.DataFrame()

#Use ThreadPoolExecutor to process appointments concurrently
# max_workers = os.cpu_count()
max_workers = 100


logging.info("car details extraction started")
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_appointment = {executor.submit(process_appointment, appointment): appointment for appointment in appointmentIds}
    
    for future in as_completed(future_to_appointment):
        appointment = future_to_appointment[future]
        try:
            df = future.result()
                        
            if not df.empty:
                final_df = pd.concat([final_df, df], ignore_index=True)
        except Exception as e:
            # print(f"An error occurred while processing appointmentId {appointment}: {e}")
            pass

logging.info("car details extraction finished")
output_file_path = '/opt/airflow/output/cars24_final_output.xlsx'
final_df.to_excel(output_file_path, index=False)

# final_df.to_excel('cars24_final_data.xlsx', index=False)