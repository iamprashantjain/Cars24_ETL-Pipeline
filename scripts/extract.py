import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings; warnings.filterwarnings('ignore')
import json
from bs4 import BeautifulSoup
from collections import defaultdict
from exception.exception import customexception
from logger.logging import logging

#scraping configuration
start_city_id=1
end_city_id=100000
max_workers=100

# Stage 1: Fetch appointment IDs for each city concurrently
def fetch_appointment_ids(city_id):
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
        df = pd.DataFrame(response.json().get('content', []))
        return df['appointmentId'].tolist()  # Return list of appointment IDs for this city_id
    except customexception as e:
        logging.info(f"Error fetching data for city_id {city_id}: {e}")
        return []  # Return an empty list in case of error

#fetch appointment id async
def fetch_all_appointment_ids(start, end, max_workers=max_workers):
    appointment_ids = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_appointment_ids, city_id): city_id for city_id in range(start, end+1)}

        for future in as_completed(futures):
            try:
                city_id = futures[future]
                city_appointments = future.result()
                if city_appointments:
                    appointment_ids.extend(city_appointments)
                logging.info(f"Fetched {len(city_appointments)} appointment IDs for city_id {city_id}")
            except Exception as e:
                logging.error(f"Error processing city_id {futures[future]}: {e}")
    
    return appointment_ids


# Stage 2: Fetch car details for each appointmentId concurrently
def process_appointment(appointment):
    logging.info(f"Currently Fetching: {appointment}")

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
            'content.lastServicedAt', 'content.duplicateKey', 'content.city', 'specs_tag'
        ]

        # Combine all columns
        all_columns = specified_columns + list(data3_dict.keys()) + list(data4_dict.keys())
        car_details_df = car_details_df[all_columns]

        return car_details_df

    except customexception as e:
        return pd.DataFrame()

#fetch car details async
def run_extract_stage_2(appointment_ids, max_workers=max_workers):
    final_df = pd.DataFrame()

    # Running threading logic inside the function
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_appointment = {executor.submit(process_appointment, appointment): appointment for appointment in appointment_ids}
        
        for future in as_completed(future_to_appointment):
            appointment = future_to_appointment[future]
            try:
                df = future.result()
                if not df.empty:
                    final_df = pd.concat([final_df, df], ignore_index=True)
            except Exception as e:
                pass

    return final_df

# Combined function for Stage 1 and Stage 2
def run_extract_stage_1_and_2(start_city_id=start_city_id, end_city_id=end_city_id, max_workers=max_workers):
    # Stage 1: Fetch appointment IDs
    logging.info("Starting Stage 1: Fetching appointment IDs")
    appointment_ids = fetch_all_appointment_ids(start_city_id, end_city_id)

    logging.info(f"Total appointment IDs fetched: {len(appointment_ids)}")

    # Stage 2: Fetch car details using the fetched appointment IDs
    logging.info("Starting Stage 2: Fetching car details")
    final_df = run_extract_stage_2(appointment_ids, max_workers)

    return final_df

#function to be called in dag script
def execute_pipeline(start_city_id=start_city_id, end_city_id=end_city_id, max_workers=max_workers, output_path='/app/output/cars24_raw_data.xlsx'):
    logging.info("Starting extract stage 1 and 2")
    final_df = run_extract_stage_1_and_2(start_city_id, end_city_id, max_workers)
    logging.info("Attempting to save Excel file")
    final_df.to_excel(output_path, index=False)
    logging.info(f"Data saved to {output_path}")
    return output_path


if __name__ == "__main__":
    execute_pipeline()