import os
import requests
from datetime import datetime
from firebase_admin import firestore

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
    "TYOTTOMATNAISET": "Työttömät työnhakijat, naiset",
    "TYOTTOMAT20": "Alle 20-v. työttömät työnhakijat",
    "TYOTTOMAT25": "Alle 25-v. työttömät työnhakijat",
    "TYOTTOMAT50": "Yli 50-v. työttömät työnhakijat",
    "TYOTTOMATULK": "Ulkomaalaisia työttömiä työnhakijat",
    "PITKAAIKAISTYOTTOMAT": "Pitkäaikaistyöttömät"
}

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

# Mappings for unemployment by education level
GENDER_MAPPING = {
    "1": "Miehet",
    "2": "Naiset"
}

EDUCATION_LEVEL_MAPPING = {
    "1": "Perusasteen tutkinnon suorittaneet",
    "2": "Toisen asteen tutkinnon suorittaneet",
    "3": "Ammatillisen tutkinnon suorittaneet",
    "4": "Opistoasteen tutkinnon suorittaneet",
    "5": "Alemman korkeakouluasteen tutkinnon suorittaneet",
    "6": "Ylemmän korkeakouluasteen tutkinnon suorittaneet",
    "7": "Lisensiaatin tai tohtorin tutkinnon suorittaneet",
    "8": "Tutkijakoulutuksen suorittaneet",
    "9_X": "Tuntematon koulutusaste"
}

UNEMPLOYMENT_EDUCATION_COLLECTION = 'unemployment_by_education_summary'
DATA_RETENTION_MONTHS = 120 # Keep data for the last 10 years (120 months)

def save_single_unemployment_data_to_firestore(db, data_point):
    """
    Temporarily saves a single data point to the 'unemployment_data' collection in Firestore.
    To be phased out as data aggregation is implemented.
    """
    try:
        doc_ref = db.collection('unemployment_data').add(data_point)
    except Exception as e:
        print(f"Error saving single unemployment data point to Firestore: {e}")

def save_education_summary_to_firestore(db, year_month, summary_data):
    """
    Saves an aggregated monthly education unemployment summary to Firestore.
    The document ID will be the year_month (e.g., "2025M09").
    """
    try:
        doc_ref = db.collection(UNEMPLOYMENT_EDUCATION_COLLECTION).document(year_month)
        # Use set to overwrite or create the document
        doc_ref.set(summary_data)
        print(f"Monthly education unemployment summary for {year_month} saved to Firestore.")
    except Exception as e:
        print(f"Error saving education summary to Firestore for {year_month}: {e}")

def get_latest_education_month_from_firestore(db):
    """
    Queries Firestore to find the latest month for which education summary data has been stored.
    """
    try:
        query = db.collection(UNEMPLOYMENT_EDUCATION_COLLECTION).order_by('year_month', direction=firestore.Query.DESCENDING).limit(1)
        results = query.get()
        if results:
            latest_month_str = results[0].id # document ID is year_month
            print(f"Latest education summary month found in Firestore: {latest_month_str}")
            year = int(latest_month_str[:4])
            month = int(latest_month_str[5:])
            return year, month
    except Exception as e:
        print(f"Could not determine latest education summary month from Firestore: {e}. Assuming no data exists.")
    return None, None

def delete_oldest_education_summaries(db):
    """
    Deletes education summary documents older than DATA_RETENTION_MONTHS.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for old education summary data to delete...")
    today = datetime.now()
    
    # Calculate the cutoff date (DATA_RETENTION_MONTHS ago)
    target_month_num = today.year * 12 + today.month - DATA_RETENTION_MONTHS
    cutoff_year = target_month_num // 12
    cutoff_month = target_month_num % 12
    if cutoff_month == 0: # Handle cases where month is 0
        cutoff_month = 12
        cutoff_year -= 1
    
    cutoff_month_str = f"{cutoff_year}M{cutoff_month:02d}"

    try:
        # Get references to all documents that are older than the cutoff
        query = db.collection(UNEMPLOYMENT_EDUCATION_COLLECTION).where(firestore.FieldPath.document_id(), '<', cutoff_month_str)
        # Use a batch deletion for efficiency if many documents are expected
        old_docs = query.stream()
        
        deleted_count = 0
        for doc in old_docs:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Deleting old education summary for {doc.id}")
            doc.reference.delete()
            deleted_count += 1
        
        if deleted_count > 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Deleted {deleted_count} old education summary documents.")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No old education summary documents to delete.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error deleting old education summary documents: {e}")

def get_unemployment_by_education_data(db):
    """
    Fetches unemployment data by education level from StatFin API and saves it to Firestore.
    """
    statfi_api_url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/tyonv/statfin_tyonv_pxt_12te.px"

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data fetch for unemployment by education level...")

    # Determine the starting month for the data fetch
    latest_year, latest_month = get_latest_education_month_from_firestore(db)
    
    start_year = 2010 # StatFin data starts from 2008, but we start from 2010
    start_month = 1

    if latest_year and latest_month:
        # Start from the month after the latest one found
        start_month = latest_month + 1
        start_year = latest_year
        if start_month > 12:
            start_month = 1
            start_year += 1
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting education data fetch from {start_year}M{start_month:02d} onwards.")

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Check if we are already up-to-date
    if start_year > current_year or (start_year == current_year and start_month > current_month):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Education data is already up-to-date. No new data to fetch.")
        return

    # Fetch data in yearly chunks from the start date
    for year in range(start_year, current_year + 1):
        fetch_start_month = start_month if year == start_year else 1
        fetch_end_month = current_month if year == current_year else 12

        # If it's the current year, fetch month by month to avoid 400 errors for future months
        if year == current_year:
            for month in range(fetch_start_month, fetch_end_month + 1):
                month_values = [f"{year}M{month:02d}"]
                if not month_values:
                    continue

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching education data for {year}M{month:02d}...")

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
                            "code": "Sukupuoli",
                            "selection": {
                                "filter": "item",
                                "values": list(GENDER_MAPPING.keys())
                            }
                        },
                        {
                            "code": "Ikäryhmitys",
                            "selection": {
                                "filter": "item",
                                "values": ["SSS"] # All age groups
                            }
                        },
                        {
                            "code": "Työmarkkina-asema",
                            "selection": {
                                "filter": "item",
                                "values": ["2"] # Unemployed
                            }
                        }
                        ,
                        {
                            "code": "Koulutusaste",
                            "selection": {
                                "filter": "item",
                                "values": list(EDUCATION_LEVEL_MAPPING.keys())
                            }
                        },
                        {
                            "code": "Kuukausi",
                            "selection": {
                                "filter": "item",
                                "values": month_values
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

                    if not data.get('value'):
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no data for unemployment by education level for {year}M{month:02d}. The data might not be published yet.")
                        continue

                    dimensions = data['dimension']
                    region_ids = dimensions['Alue']['category']['index']
                    gender_ids = dimensions['Sukupuoli']['category']['index']
                    education_ids = dimensions['Koulutusaste']['category']['index']
                    month_ids = dimensions['Kuukausi']['category']['index']
                    values = data['value']

                    value_index = 0
                    for month_id in month_ids:
                        month_code = dimensions['Kuukausi']['category']['label'][month_id]
                        
                        monthly_summary = {
                            "year_month": month_code,
                            "timestamp": firestore.SERVER_TIMESTAMP,
                            "regions": {}
                        }

                        for region_id in region_ids:
                            region_code = dimensions['Alue']['category']['label'][region_id]
                            region_name = REGION_MAPPING.get(region_code, region_code)
                            monthly_summary["regions"][region_name] = {}

                            for gender_id in gender_ids:
                                gender_name = GENDER_MAPPING.get(dimensions['Sukupuoli']['category']['label'][gender_id], dimensions['Sukupuoli']['category']['label'][gender_id])
                                monthly_summary["regions"][region_name][gender_name] = {}

                                for education_id in education_ids:
                                    education_name = EDUCATION_LEVEL_MAPPING.get(dimensions['Koulutusaste']['category']['label'][education_id], dimensions['Koulutusaste']['category']['label'][education_id])
                                    
                                    value = values[value_index]
                                    value_index += 1

                                    monthly_summary["regions"][region_name][gender_name][education_name] = value
                        
                        save_education_summary_to_firestore(db, month_code, monthly_summary)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Unemployment by education level data for {year}M{month:02d} fetched and saved to Firestore.")

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 400:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received 400 Bad Request for {year}M{month:02d}. This likely means data for this month is not yet available.")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching education data from StatFin API for {year}M{month:02d}: {e}")
                except KeyError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for education data (missing key) for {year}M{month:02d}: {e}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for education data for {year}M{month:02d}: {e}")
        else: # For previous years, fetch in yearly chunks as before
            month_values = generate_month_codes(year, fetch_start_month, year, fetch_end_month)

            if not month_values:
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching education data for year {year} ({len(month_values)} months)...")

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
                        "code": "Sukupuoli",
                        "selection": {
                            "filter": "item",
                            "values": list(GENDER_MAPPING.keys())
                        }
                    },
                    {
                        "code": "Ikäryhmitys",
                        "selection": {
                            "filter": "item",
                            "values": ["SSS"] # All age groups
                        }
                    },
                    {
                        "code": "Työmarkkina-asema",
                        "selection": {
                            "filter": "item",
                            "values": ["2"] # Unemployed
                        }
                    }
                    ,
                    {
                        "code": "Koulutusaste",
                        "selection": {
                            "filter": "item",
                            "values": list(EDUCATION_LEVEL_MAPPING.keys())
                        }
                    },
                    {
                        "code": "Kuukausi",
                        "selection": {
                            "filter": "item",
                            "values": month_values
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

                if not data.get('value'):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no data for unemployment by education level for year {year}. The data might not be published yet.")
                    continue

                dimensions = data['dimension']
                region_ids = dimensions['Alue']['category']['index']
                gender_ids = dimensions['Sukupuoli']['category']['index']
                education_ids = dimensions['Koulutusaste']['category']['index']
                month_ids = dimensions['Kuukausi']['category']['index']
                values = data['value']

                value_index = 0
                for month_id in month_ids:
                    month_code = dimensions['Kuukausi']['category']['label'][month_id]
                    
                    monthly_summary = {
                        "year_month": month_code,
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "regions": {}
                    }

                    for region_id in region_ids:
                        region_code = dimensions['Alue']['category']['label'][region_id]
                        region_name = REGION_MAPPING.get(region_code, region_code)
                        monthly_summary["regions"][region_name] = {}

                        for gender_id in gender_ids:
                            gender_name = GENDER_MAPPING.get(dimensions['Sukupuoli']['category']['label'][gender_id], dimensions['Sukupuoli']['category']['label'][gender_id])
                            monthly_summary["regions"][region_name][gender_name] = {}

                            for education_id in education_ids:
                                education_name = EDUCATION_LEVEL_MAPPING.get(dimensions['Koulutusaste']['category']['label'][education_id], dimensions['Koulutusaste']['category']['label'][education_id])
                                
                                value = values[value_index]
                                value_index += 1

                                monthly_summary["regions"][region_name][gender_name][education_name] = value
                    
                    save_education_summary_to_firestore(db, month_code, monthly_summary)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Unemployment by education level data for year {year} fetched and saved to Firestore.")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Received 400 Bad Request for year {year}. This likely means data for the requested months is not yet available.")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching education data from StatFin API for year {year}: {e}")
            except KeyError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for education data (missing key): {e}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for education data: {e}")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Unemployment by education level data update process completed.")
    delete_oldest_education_summaries(db)

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
    
    start_year = 2010 # StatFin data starts from 2008, but we start from 2010
    start_month = 1

    if latest_year and latest_month:
        # Start from the month after the latest one found
        start_month = latest_month + 1
        start_year = latest_year
        if start_month > 12:
            start_month = 1
            start_year += 1
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data fetch from {start_year}M{start_month:02d} onwards.")

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Check if we are already up-to-date
    if start_year > current_year or (start_year == current_year and start_month > current_month):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Data is already up-to-date. No new data to fetch.")
        return

    # Fetch data in yearly chunks from the start date
    for year in range(start_year, current_year + 1):
        fetch_start_month = start_month if year == start_year else 1
        fetch_end_month = current_month if year == current_year else 12

        # If it's the current year, fetch month by month to avoid 400 errors for future months
        if year == current_year:
            for month in range(fetch_start_month, fetch_end_month + 1):
                month_values = [f"{year}M{month:02d}"]
                if not month_values:
                    continue

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching general unemployment data for {year}M{month:02d}...")

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
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no new data for {year}M{month:02d}. The data might not be published yet.")
                        continue

                    # Parse the JSON-stat2 data
                    dimensions = data['dimension']
                    region_ids = dimensions['Alue']['category']['index']
                    month_ids = dimensions['Kuukausi']['category']['index']
                    data_type_ids = dimensions['Tiedot']['category']['index']
                    values = data['value']

                    # Iterate through the a and save to Firestore
                    value_index = 0
                    for month_id in month_ids:
                        month_code = dimensions['Kuukausi']['category']['label'][month_id]
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Saving StatFin data for {month_code}...")
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
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] General unemployment data for {year}M{month:02d} fetched and saved to Firestore.")

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 400:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received 400 Bad Request for {year}M{month:02d}. This likely means data for this month is not yet available.")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching general unemployment data from StatFin API for {year}M{month:02d}: {e}")
                except KeyError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for general unemployment data (missing key) for {year}M{month:02d}: {e}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for general unemployment data for {year}M{month:02d}: {e}")
        else: # For previous years, fetch in yearly chunks as before
            month_values = generate_month_codes(year, fetch_start_month, year, fetch_end_month)

            if not month_values:
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching data for year {year} ({len(month_values)} months)...")

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
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no new data for year {year}. The data might not be published yet.")
                    continue

                # Parse the JSON-stat2 data
                dimensions = data['dimension']
                region_ids = dimensions['Alue']['category']['index']
                month_ids = dimensions['Kuukausi']['category']['index']
                data_type_ids = dimensions['Tiedot']['category']['index']
                values = data['value']

                # Iterate through the a and save to Firestore
                value_index = 0
                for month_id in month_ids:
                    month_code = dimensions['Kuukausi']['category']['label'][month_id]
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Saving StatFin data for {month_code}...")
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
                            save_single_unemployment_data_to_firestore(db, data_point) # Using the new placeholder function
                print(f"[{datetime.now().strftime('%H:%M:%S')}] General unemployment data for year {year} fetched and saved to Firestore.")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Received 400 Bad Request for year {year}. This likely means data for the requested months is not yet available.")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching general unemployment data from StatFin API for year {year}: {e}")
            except KeyError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for year {year} (missing key): {e}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for year {year}: {e}")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Data update process completed.")
