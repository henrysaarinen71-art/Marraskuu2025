import firebase_admin
from firebase_admin import credentials, firestore
import os
import requests
from datetime import datetime
import json
import base64

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
    Initializes the Firebase Admin SDK.
    
    It first tries to use credentials from a Base64-encoded environment variable
    (for use in GitHub Actions). If that fails, it falls back to a local
    'firebase-credentials.json' file (for local development).
    """
    try:
        # Try to get credentials from environment variable (for GitHub Actions)
        creds_base64 = os.environ.get('FIREBASE_CREDENTIALS_BASE64')
        if creds_base64:
            print("Initializing Firebase using credentials from environment variable.")
            creds_json_str = base64.b64decode(creds_base64).decode('utf-8')
            creds_dict = json.loads(creds_json_str)
            cred = credentials.Certificate(creds_dict)
        else:
            # Fallback to local file (for local development)
            print("Initializing Firebase using local 'firebase-credentials.json' file.")
            cred_path = 'firebase-credentials.json'
            if not os.path.exists(cred_path):
                print(f"Error: The Firebase credentials file was not found at '{cred_path}'.")
                print("For local development, ensure the file exists.")
                print("For GitHub Actions, ensure the FIREBASE_CREDENTIALS_BASE64 secret is set.")
                return None
            cred = credentials.Certificate(cred_path)

        # Initialize the app if not already initialized
        if not firebase_admin._apps:
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

def get_latest_month_from_firestore(db):
    """
    Queries Firestore to find the latest month for which data has been stored.
    """
    try:
        query = db.collection('unemployment_data').order_by('year_month', direction=firestore.Query.DESCENDING).limit(1)
        results = query.get()
        if results:
            latest_month_str = results[0].to_dict()['year_month']
            print(f"Latest month found in Firestore: {latest_month_str}")
            year = int(latest_month_str[:4])
            month = int(latest_month_str[5:])
            return year, month
    except Exception as e:
        print(f"Could not determine latest month from Firestore: {e}. Assuming no data exists.")
    return None, None

def get_statfi_data(db):
    """
    Fetches new unemployment data from StatFin API since the last update and saves it to Firestore.
    """
    statfi_api_url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/tyonv/statfin_tyonv_pxt_12r5.px"
    
    # Determine the starting month for the data fetch
    latest_year, latest_month = get_latest_month_from_firestore(db)
    
    start_year = 2008
    start_month = 1

    if latest_year and latest_month:
        # Start from the month after the latest one found
        start_month = latest_month + 1
        start_year = latest_year
        if start_month > 12:
            start_month = 1
            start_year += 1
    
    print(f"Starting data fetch from {start_year}M{start_month:02d} onwards.")

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Check if we are already up-to-date
    if start_year > current_year or (start_year == current_year and start_month > current_month):
        print("Data is already up-to-date. No new data to fetch.")
        return

    # Fetch data in yearly chunks from the start date
    for year in range(start_year, current_year + 1):
        fetch_start_month = start_month if year == start_year else 1
        fetch_end_month = current_month if year == current_year else 12

        month_values = generate_month_codes(year, fetch_start_month, year, fetch_end_month)

        if not month_values:
            continue

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
            response.raise_for_status()
            data = response.json()

            # Check if new data was actually returned
            if not data.get('value'):
                print(f"API returned no new data for year {year}. The data might not be published yet.")
                continue

            # Parse the JSON-stat2 data
            dimensions = data['dimension']
            region_ids = dimensions['Alue']['category']['index']
            month_ids = dimensions['Kuukausi']['category']['index']
            data_type_ids = dimensions['Tiedot']['category']['index']
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
                            "timestamp": firestore.SERVER_TIMESTAMP
                        }
                        save_data_to_firestore(db, data_point)
            print(f"Data for year {year} fetched and saved to Firestore.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f"Received 400 Bad Request for year {year}. This likely means data for the requested months is not yet available.")
            else:
                print(f"Error fetching data from StatFin API for year {year}: {e}")
        except KeyError as e:
            print(f"Error parsing StatFin API response for year {year} (missing key): {e}")
        except Exception as e:
            print(f"An unexpected error occurred for year {year}: {e}")
    
    print("Data update process completed.")


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