import pandas as pd
import logging
from datetime import datetime

def perform_transformation():
    """
    Perform data transformation.
    Reads raw data, cleans it, and applies transformations before saving the output.
    """
    try:
        logging.info("Starting data transformation")

        # File paths
        input_file = "/app/output/cars24_raw_data.xlsx"
        output_file = "/app/output/cars24_transformed_data.xlsx"

        # Read raw data
        logging.info(f"Reading raw data from {input_file}")
        raw_data = pd.read_excel(input_file)

        # Step 1: Drop duplicate rows
        logging.info("Dropping duplicate rows")
        transformed_data = raw_data.drop_duplicates()

        # Step 2: Remove rows with missing values in specific columns
        required_columns = ['Displacementcc', 'GearBoxNumberOfGears']
        logging.info(f"Removing rows with missing values in {required_columns}")
        transformed_data = transformed_data[transformed_data[required_columns].notna().all(axis=1)]

        # Step 3: Drop unnecessary columns
        columns_to_drop = ['TransmissionType', 'specs_tag', 'content.city']
        logging.info(f"Dropping columns: {columns_to_drop}")
        transformed_data = transformed_data.drop(columns=columns_to_drop)

        # Step 4: Handle missing values
        na_columns = [
            'ABSAntilockBrakingSystem', 'PowerWindowsFront', 'PowerWindowsRear', 'AirConditioner',
            '12VPowerOutlet', 'MultifunctionDisplayScreen', 'EntertainmentDisplayScreen', 'VoiceRecognition'
        ]
        logging.info("Replacing NaN values with 'not available'")
        transformed_data[na_columns] = transformed_data[na_columns].fillna("not available")

        # Step 5: Date feature engineering
        logging.info("Performing date feature engineering")
        today = pd.to_datetime(datetime.now().date())

        # Fitness Upto
        if 'content.fitnessUpto' in transformed_data.columns:
            transformed_data['content.fitnessUpto'] = pd.to_datetime(
                transformed_data['content.fitnessUpto'], format='%d-%b-%Y'
            )
            transformed_data['content.fitnessUpto_months_remaining'] = (
                (transformed_data['content.fitnessUpto'].dt.year - today.year) * 12 +
                (transformed_data['content.fitnessUpto'].dt.month - today.month)
            )

        # Insurance Expiry
        if 'content.insuranceExpiry' in transformed_data.columns:
            transformed_data['content.insuranceExpiry'] = pd.to_datetime(
                transformed_data['content.insuranceExpiry'], unit='s'
            )
            transformed_data['content.insuranceExpiry_months_remaining'] = (
                (transformed_data['content.insuranceExpiry'].dt.year - today.year) * 12 +
                (transformed_data['content.insuranceExpiry'].dt.month - today.month)
            ).clip(lower=0)

        # Last Serviced
        if 'content.lastServicedAt' in transformed_data.columns:
            transformed_data['content.lastServicedAt'] = pd.to_datetime(
                transformed_data['content.lastServicedAt']
            )
            transformed_data['content.lastServicedAt_months_remaining'] = abs(
                (transformed_data['content.lastServicedAt'].dt.year - today.year) * 12 +
                (transformed_data['content.lastServicedAt'].dt.month - today.month)
            )

        # Drop original date columns
        logging.info("Dropping original date columns")
        date_columns_to_drop = ['content.fitnessUpto', 'content.insuranceExpiry', 'content.lastServicedAt']
        transformed_data = transformed_data.drop(columns=[col for col in date_columns_to_drop if col in transformed_data.columns])

        # Step 6: Feature encoding
        logging.info("Encoding features")
        tyre_columns = ['Left Front Tyre', 'Right Front Tyre', 'Left Rear Tyre', 'Right Rear Tyre', 'Spare Tyre']
        if set(tyre_columns).issubset(transformed_data.columns):
            transformed_data[tyre_columns] = transformed_data[tyre_columns].replace({'OK': 1, 'WARN': 0})
            transformed_data['Tyre_Health'] = transformed_data[tyre_columns].sum(axis=1)
            total_tyres = len(tyre_columns)
            transformed_data['tyre_health_pct'] = (transformed_data['Tyre_Health'] / total_tyres) * 100

        # Drop tyre columns
        logging.info("Dropping tyre-related columns")
        tyre_columns_to_drop = tyre_columns + ['Tyre_Health']
        transformed_data = transformed_data.drop(columns=[col for col in tyre_columns_to_drop if col in transformed_data.columns])

        # Step 7: Finalize dataset
        logging.info("Finalizing dataset")
        final_columns = [
            'ABSAntilockBrakingSystem', 'AirConditioner', 'Airbags', 'Bootspacelitres', 'Displacementcc',
            'FueltankCapacitylitres', 'GroundClearancemm', 'tyre_health_pct', 'MaxPowerbhp', 'MaxPowerrpm',
            'MaxTorqueNm', 'SeatingCapacity', 'content.bodyType', 'content.duplicateKey',
            'content.fitnessUpto_months_remaining', 'content.fuelType', 'content.insuranceExpiry_months_remaining',
            'content.insuranceType', 'content.make', 'content.odometerReading', 'content.ownerNumber',
            'content.transmission', 'content.year', 'defects', 'repainted', 'content.onRoadPrice'
        ]
        transformed_data = transformed_data[[col for col in final_columns if col in transformed_data.columns]]

        # Save the transformed data
        logging.info(f"Saving transformed data to {output_file}")
        transformed_data.to_excel(output_file, index=False)

        logging.info("Data transformation completed successfully")
        return output_file

    except Exception as e:
        logging.error(f"An error occurred during data transformation: {e}")
        raise


if __name__ == "__main__":
    perform_transformation()