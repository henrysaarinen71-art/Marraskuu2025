import firebase_admin
from firebase_admin import credentials, firestore
import os
import requests
from datetime import datetime
import json

# Mapping for region codes to names for better readability in Firestore
REGION_MAPPING = {
    "KU049": "Espoo",
    "KU091": "Helsinki",
    "KU235": "Kauniainen",
    "KU092": "Vantaa"
}

# Mapping for data codes to names
DATA_TYPE_MAPPING = {
    "TYOTTOMATLOPUSSA": "Työttömät työnhakijat yhteensä",
    "TYOTTOMATMIEHET": "Työttömät työnhakijat, miehet",
    "TYOTTOMATNAISET": "Työttömät työnhakijat, naiset"
}

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using the service account key.
    """
    try:
        cred_path = 'firebase-credentials.json'

        if not os.path.exists(cred_path):
            print(f"Error: The Firebase credentials file was not found.")
            print(f"Please make sure a file named '{cred_path}' is in the same directory as this script.")
            return None

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        print("Firebase connection initialized successfully.")
        return firestore.client()

    except Exception as e:
        print(f"An error occurred during Firebase initialization: {e}")
        return None

def generate_month_codes(start_year, start_month, end_year=None, end_month=None):
    """
    Generates a list of month codes (YYYYMM) from the start date to the current month or specified end date.
    """
    month_codes = []
    current_date = datetime.now()
    
    if end_year is None:
        end_year = current_date.year
    if end_month is None:
        end_month = current_date.month

    year = start_year
    month = start_month

    while True:
        if year > end_year or (year == end_year and month > end_month):
            break
        
        month_codes.append(f"{year}M{month:02d}")
        
        month += 1
        if month > 12:
            month = 1
            year += 1
            
    return month_codes

def save_data_to_firestore(db, data_point):
    """
    Saves a single data point to the 'unemployment_data' collection in Firestore.
    """
    try:
        doc_ref = db.collection('unemployment_data').add(data_point)
        # print(f"Document added with ID: {doc_ref[1].id}") # Uncomment for verbose logging
    except Exception as e:
        print(f"Error saving data to Firestore: {e}")

def get_statfi_data(db):
    """
    Fetches unemployment data from StatFin API and saves it to Firestore.
    Iterates through years to fetch all historical data in chunks.
    """
    statfi_api_url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/tyonv/statfin_tyonv_pxt_12r5.px"
    
    current_year = datetime.now().year
    current_month = datetime.now().month

    print("Starting to fetch all historical data from StatFin API...")

    for year in range(2008, current_year + 1):
        month_values = []
        if year == current_year:
            month_values = generate_month_codes(year, 1, current_year, current_month)
        else:
            month_values = generate_month_codes(year, 1, year, 12)

        if not month_values:
            continue # Skip if no months for the current year (e.g., future months)

        print(f"Fetching data for year {year} ({len(month_values)} months)...")

        query_payload = {
            "query": [
                {
                    "code": "Alue",
                    "selection": {
                        "filter": "item",
                        "values": list(REGION_MAPPING.keys())
                    }
                },
                {
                    "code": "Kuukausi",
                    "selection": {
                        "filter": "item",
                        "values": month_values
                    }
                },
                {
                    "code": "Tiedot",
                    "selection": {
                        "filter": "item",
                        "values": list(DATA_TYPE_MAPPING.keys())
                    }
                }
            ],
            "response": {
                "format": "json-stat2"
            }
        }

        try:
            response = requests.post(statfi_api_url, json=query_payload)
            response.raise_for_status() # Raise an exception for HTTP errors
            data = response.json()

            # Parse the JSON-stat2 data
            dimensions = data['dimension']
            
            # Extract dimension IDs and labels
            region_ids = dimensions['Alue']['category']['index']
            month_ids = dimensions['Kuukausi']['category']['index']
            data_type_ids = dimensions['Tiedot']['category']['index']

            # Extract values
            values = data['value']

            # Iterate through the data and save to Firestore
            value_index = 0
            for month_id in month_ids:
                month_code = dimensions['Kuukausi']['category']['label'][month_id]
                for region_id in region_ids:
                    region_code = dimensions['Alue']['category']['label'][region_id]
                    for data_type_id in data_type_ids:
                        data_type_code = dimensions['Tiedot']['category']['label'][data_type_id]
                        
                        value = values[value_index]
                        value_index += 1

                        data_point = {
                            "region_code": region_code,
                            "region_name": REGION_MAPPING.get(region_code, region_code),
                            "year_month": month_code,
                            "data_type_code": data_type_code,
                            "data_type_name": DATA_TYPE_MAPPING.get(data_type_code, data_type_code),
                            "value": value,
                            "timestamp": firestore.SERVER_TIMESTAMP # Add server timestamp for when data was added
                        }
                        save_data_to_firestore(db, data_point)
            print(f"Data for year {year} fetched and saved to Firestore.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and year == current_year:
                print(f"Received 400 Bad Request for year {year}. This might mean data for some months is not yet available.")
                print("Attempting to find the last available month for the current year...")
                
                # Try to find the last available month by reducing the range
                for month_to_try in range(current_month, 0, -1):
                    print(f"  Trying up to {year}M{month_to_try:02d}...")
                    month_values_reduced = generate_month_codes(year, 1, year, month_to_try)
                    if not month_values_reduced:
                        continue

                    query_payload_reduced = {
                        "query": [
                            {
                                "code": "Alue",
                                "selection": {
                                    "filter": "item",
                                    "values": list(REGION_MAPPING.keys())
                                }
                            },
                            {
                                "code": "Kuukausi",
                                "selection": {
                                    "filter": "item",
                                    "values": month_values_reduced
                                }
                            },
                            {
                                "code": "Tiedot",
                                "selection": {
                                    "filter": "item",
                                    "values": list(DATA_TYPE_MAPPING.keys())
                                }
                            }
                        ],
                        "response": {
                            "format": "json-stat2"
                        }
                    }
                    try:
                        response_reduced = requests.post(statfi_api_url, json=query_payload_reduced)
                        response_reduced.raise_for_status()
                        data_reduced = response_reduced.json()

                        # Parse and save data for the reduced range
                        dimensions_reduced = data_reduced['dimension']
                        region_ids_reduced = dimensions_reduced['Alue']['category']['index']
                        month_ids_reduced = dimensions_reduced['Kuukausi']['category']['index']
                        data_type_ids_reduced = dimensions_reduced['Tiedot']['category']['index']
                        values_reduced = data_reduced['value']

                        value_index_reduced = 0
                        for month_id_reduced in month_ids_reduced:
                            month_code_reduced = dimensions_reduced['Kuukausi']['category']['label'][month_id_reduced]
                            for region_id_reduced in region_ids_reduced:
                                region_code_reduced = dimensions_reduced['Alue']['category']['label'][region_id_reduced]
                                for data_type_id_reduced in data_type_ids_reduced:
                                    data_type_code_reduced = dimensions_reduced['Tiedot']['category']['label'][data_type_id_reduced]
                                    
                                    value_reduced = values_reduced[value_index_reduced]
                                    value_index_reduced += 1

                                    data_point_reduced = {
                                        "region_code": region_code_reduced,
                                        "region_name": REGION_MAPPING.get(region_code_reduced, region_code_reduced),
                                        "year_month": month_code_reduced,
                                        "data_type_code": data_type_code_reduced,
                                        "data_type_name": DATA_TYPE_MAPPING.get(data_type_code_reduced, data_type_code_reduced),
                                        "value": value_reduced,
                                        "timestamp": firestore.SERVER_TIMESTAMP
                                    }
                                    save_data_to_firestore(db, data_point_reduced)
                        print(f"Successfully fetched and saved data for year {year} up to {year}M{month_to_try:02d}.")
                        break # Break from inner loop if successful
                    except requests.exceptions.HTTPError as inner_e:
                        if inner_e.response.status_code == 400:
                            print(f"  Still 400 Bad Request for {year}M{month_to_try:02d}. Trying earlier month.")
                        else:
                            print(f"  An unexpected HTTP error occurred while reducing month range for year {year}: {inner_e}")
                            break
                    except Exception as inner_e:
                        print(f"  An unexpected error occurred while reducing month range for year {year}: {inner_e}")
                        break
                else: # This else block executes if the inner loop completes without a 'break'
                    print(f"Could not fetch any data for year {year} after trying all months.")
            else:
                print(f"Error fetching data from StatFin API for year {year}: {e}")
        except KeyError as e:
            print(f"Error parsing StatFin API response for year {year} (missing key): {e}")
        except Exception as e:
            print(f"An unexpected error occurred for year {year}: {e}")
    
    print("All historical data fetching and saving to Firestore completed.")


def main():
    """
    Main function to run the application.
    """
    print("Starting the application...")
    db = initialize_firebase()

    if db:
        print("Successfully connected to Firestore.")
        get_statfi_data(db)
        print("Application finished.")
    else:
        print("Failed to connect to Firestore. Please check the error messages above.")

if __name__ == '__main__':
    main()