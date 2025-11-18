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
    "PITKAAIKAISTYOTTOMAT": "Pitkäaikaistyöttömät",
    "TYOTTOMATSAIR": "Vamm./pitkäaik.sair. työttömät työnhakijat (lkm.)"
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
UNEMPLOYMENT_GENERAL_COLLECTION = 'unemployment_general_summary'
UNEMPLOYMENT_BY_OCCUPATION_COLLECTION = 'unemployment_by_occupation_summary'
DATA_RETENTION_MONTHS = 120 # Keep data for the last 10 years (120 months)
DATA_FETCH_DELAY_MONTHS = 2 # Assume data is available up to 2 months prior to current month

# Occupation codes
OCCUPATION_CODES = [
    "SSS", "1111", "1112", "1114", "1120", "1211", "1212", "1213", "1219", "1221", "1222", "1223", "1311",
    "1312", "1321", "1322", "1323", "1324", "1330", "1341", "1342", "1343", "1344", "1345", "1346", "1349",
    "1411", "1412", "1420", "1431", "1439", "2111", "2112", "2113", "2114", "2120", "2131", "2132", "2133",
    "2141", "2142", "2143", "2144", "2145", "2146", "2149", "2151", "2152", "2153", "2161", "2162", "2163",
    "2164", "2165", "2166", "2211", "2212", "2221", "2250", "2261", "2262", "2263", "2265", "2266", "2269",
    "2310", "2320", "2330", "2341", "2342", "2351", "2352", "2353", "2354", "2355", "2356", "2359", "2411",
    "2412", "2413", "2421", "2422", "2423", "2424", "2431", "2432", "2433", "2434", "2511", "2512", "2513",
    "2514", "2519", "2521", "2522", "2523", "2529", "2611", "2612", "2619", "2621", "2622", "2631", "2632",
    "2633", "2634", "2635", "2636", "2641", "2642", "2643", "2651", "2652", "2653", "2654", "2655", "2656",
    "2659", "3111", "3112", "3113", "3114", "3115", "3116", "3117", "3118", "3119", "3121", "3122", "3123",
    "3131", "3132", "3133", "3134", "3135", "3139", "3141", "3142", "3143", "3151", "3152", "3153", "3154",
    "3155", "3211", "3212", "3213", "3214", "3221", "3222", "3230", "3240", "3251", "3254", "3255", "3256",
    "3257", "3258", "3259", "3311", "3312", "3313", "3314", "3315", "3321", "3322", "3323", "3324", "3331",
    "3332", "3333", "3334", "3339", "3341", "3342", "3343", "3344", "3351", "3352", "3353", "3354", "3355",
    "3359", "3411", "3412", "3413", "3421", "3422", "3423", "3431", "3432", "3433", "3434", "3435", "3511",
    "3512", "3513", "3514", "3521", "3522", "4110", "4120", "4131", "4132", "4211", "4212", "4213", "4214",
    "4221", "4222", "4223", "4224", "4225", "4226", "4227", "4229", "4311", "4312", "4313", "4321", "4322",
    "4323", "4411", "4412", "4413", "4415", "4416", "4419", "5111", "5112", "5113", "5120", "5131", "5132",
    "5141", "5142", "5151", "5152", "5153", "5161", "5163", "5164", "5165", "5169", "5211", "5212", "5221",
    "5222", "5223", "5230", "5241", "5242", "5243", "5244", "5245", "5246", "5249", "5311", "5312", "5321",
    "5322", "5329", "5411", "5412", "5413", "5414", "5419", "6111", "6112", "6113", "6114", "6121", "6122",
    "6123", "6129", "6130", "6210", "6221", "6222", "6224", "7111", "7112", "7113", "7114", "7115", "7119",
    "7121", "7122", "7123", "7124", "7125", "7126", "7127", "7131", "7132", "7133", "7211", "7212", "7213",
    "7214", "7215", "7221", "7222", "7223", "7224", "7231", "7232", "7233", "7234", "7311", "7312", "7313",
    "7314", "7315", "7316", "7317", "7318", "7319", "7321", "7322", "7323", "7411", "7412", "7413", "7421",
    "7422", "7511", "7512", "7513", "7514", "7515", "7516", "7521", "7522", "7523", "7531", "7532", "7533",
    "7534", "7535", "7536", "7541", "7542", "7543", "7544", "7549", "8111", "8112", "8113", "8114", "8121",
    "8122", "8131", "8132", "8141", "8142", "8143", "8151", "8152", "8153", "8154", "8155", "8156", "8157",
    "8159", "8160", "8171", "8172", "8181", "8182", "8183", "8189", "8211", "8212", "8219", "8311", "8312",
    "8321", "8322", "8331", "8332", "8341", "8342", "8343", "8344", "8350", "9111", "9112", "9122", "9123",
    "9129", "9211", "9212", "9213", "9214", "9215", "9216", "9311", "9312", "9313", "9321", "9329", "9332",
    "9333", "9334", "9411", "9412", "9510", "9520", "9611", "9612", "9613", "9621", "9622", "9623", "9629",
    "0110", "0210", "0310", "X011", "X111", "X121", "X131", "X211", "X212", "X311", "X411", "X511", "X521",
    "X531", "X541", "X611", "X621", "X999"
]


def save_education_summary_to_firestore(db, year_month, summary_data):
    """
    Saves an aggregated monthly education unemployment summary to Firestore.
    """
    try:
        doc_ref = db.collection(UNEMPLOYMENT_EDUCATION_COLLECTION).document(year_month)
        doc_ref.set(summary_data)
        print(f"Monthly education unemployment summary for {year_month} saved to Firestore.")
    except Exception as e:
        print(f"Error saving education summary to Firestore for {year_month}: {e}")

def save_general_summary_to_firestore(db, year_month, summary_data):
    """
    Saves an aggregated monthly general unemployment summary to Firestore.
    """
    try:
        doc_ref = db.collection(UNEMPLOYMENT_GENERAL_COLLECTION).document(year_month)
        doc_ref.set(summary_data)
        print(f"Monthly general unemployment summary for {year_month} saved to Firestore.")
    except Exception as e:
        print(f"Error saving general summary to Firestore for {year_month}: {e}")

def save_occupation_summary_to_firestore(db, year_month, summary_data):
    """
    Saves an aggregated monthly unemployment by occupation summary to Firestore.
    """
    try:
        doc_ref = db.collection(UNEMPLOYMENT_BY_OCCUPATION_COLLECTION).document(year_month)
        doc_ref.set(summary_data)
        print(f"Monthly unemployment by occupation summary for {year_month} saved to Firestore.")
    except Exception as e:
        print(f"Error saving occupation summary to Firestore for {year_month}: {e}")

def get_latest_occupation_month_from_firestore(db):
    """
    Queries Firestore to find the latest month for which unemployment by occupation summary data has been stored.
    """
    try:
        query = db.collection(UNEMPLOYMENT_BY_OCCUPATION_COLLECTION).order_by('year_month', direction=firestore.Query.DESCENDING).limit(1)
        results = query.get()
        if results:
            latest_month_str = results[0].id
            print(f"Latest unemployment by occupation summary month found in Firestore: {latest_month_str}")
            year = int(latest_month_str[:4])
            month = int(latest_month_str[5:])
            return year, month
    except Exception as e:
        print(f"Could not determine latest occupation summary month from Firestore: {e}. Assuming no data exists.")
    return None, None

def get_unemployment_by_occupation_data(db):
    """
    Fetches unemployment data by occupation from StatFin API and saves it to Firestore.
    """
    statfi_api_url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/tyonv/statfin_tyonv_pxt_12ti.px"
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data fetch for unemployment by occupation...")

    latest_year, latest_month = get_latest_occupation_month_from_firestore(db)
    
    start_year = 2025
    start_month = 8

    if latest_year and latest_month:
        start_month = latest_month + 1
        start_year = latest_year
        if start_month > 12:
            start_month = 1
            start_year += 1
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting occupation data fetch from {start_year}M{start_month:02d} onwards.")

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Calculate the latest month for which data is likely to be available
    # Assuming a delay of DATA_FETCH_DELAY_MONTHS (e.g., 2 months)
    latest_available_month = current_month - DATA_FETCH_DELAY_MONTHS
    latest_available_year = current_year

    while latest_available_month <= 0:
        latest_available_month += 12
        latest_available_year -= 1

    if start_year > latest_available_year or (start_year == latest_available_year and start_month > latest_available_month):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Unemployment by occupation data is already up-to-date.")
        return

    for year in range(start_year, latest_available_year + 1):
        fetch_start_month = start_month if year == start_year else 1
        fetch_end_month = latest_available_month if year == latest_available_year else 12

        month_values = generate_month_codes(year, fetch_start_month, year, fetch_end_month)
        if not month_values:
            continue

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching occupation data for year {year} ({len(month_values)} months)...")

        query_payload = {
            "query": [
                {"code": "Alue", "selection": {"filter": "item", "values": list(REGION_MAPPING.keys())}},
                {"code": "Ammattiryhmä", "selection": {"filter": "item", "values": OCCUPATION_CODES}},
                {"code": "Kuukausi", "selection": {"filter": "item", "values": month_values}}
            ],
            "response": {"format": "json-stat2"}
        }

        try:
            response = requests.post(statfi_api_url, json=query_payload)
            response.raise_for_status()
            data = response.json()
            if not data.get('value'):
                continue

            dimensions = data['dimension']
            region_ids = dimensions['Alue']['category']['index']
            occupation_ids = dimensions['Ammattiryhmä']['category']['index']
            month_ids = dimensions['Kuukausi']['category']['index']
            # The "Tiedot" dimension is implicitly returned, we don't need to get it from the query
            # data_type_ids = dimensions['Tiedot']['category']['index']
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
                    monthly_summary["regions"][region_name] = {"occupations": {}}

                    for occupation_id in occupation_ids:
                        occupation_code = dimensions['Ammattiryhmä']['category']['label'][occupation_id]
                        
                        unemployed = values[value_index]
                        value_index += 1
                        vacancies = values[value_index]
                        value_index += 1

                        if (unemployed is not None and unemployed > 0) or (vacancies is not None and vacancies > 0):
                            monthly_summary["regions"][region_name]["occupations"][occupation_code] = {
                                "unemployed": unemployed,
                                "vacancies": vacancies
                            }
                
                save_occupation_summary_to_firestore(db, month_code, monthly_summary)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Unemployment by occupation data for year {year} fetched and saved.")

        except requests.exceptions.HTTPError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching occupation data from StatFin API for year {year}: {e}")
        except KeyError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for occupation data for year {year} (missing key): {e}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for occupation data for year {year}: {e}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Unemployment by occupation data update process completed.")


def get_latest_education_month_from_firestore(db):
    """
    Queries Firestore to find the latest month for which education summary data has been stored.
    """
    try:
        query = db.collection(UNEMPLOYMENT_EDUCATION_COLLECTION).order_by('year_month', direction=firestore.Query.DESCENDING).limit(1)
        results = query.get()
        if results:
            latest_month_str = results[0].id
            print(f"Latest education summary month found in Firestore: {latest_month_str}")
            year = int(latest_month_str[:4])
            month = int(latest_month_str[5:])
            return year, month
    except Exception as e:
        print(f"Could not determine latest education summary month from Firestore: {e}. Assuming no data exists.")
    return None, None

def get_latest_general_month_from_firestore(db):
    """
    Queries Firestore to find the latest month for which general summary data has been stored.
    """
    try:
        query = db.collection(UNEMPLOYMENT_GENERAL_COLLECTION).order_by('year_month', direction=firestore.Query.DESCENDING).limit(1)
        results = query.get()
        if results:
            latest_month_str = results[0].id
            print(f"Latest general summary month found in Firestore: {latest_month_str}")
            year = int(latest_month_str[:4])
            month = int(latest_month_str[5:])
            return year, month
    except Exception as e:
        print(f"Could not determine latest general summary month from Firestore: {e}. Assuming no data exists.")
    return None, None

def delete_oldest_education_summaries(db):
    """
    Deletes education summary documents older than DATA_RETENTION_MONTHS.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for old education summary data to delete...")
    today = datetime.now()
    
    target_month_num = today.year * 12 + today.month - DATA_RETENTION_MONTHS
    cutoff_year = target_month_num // 12
    cutoff_month = target_month_num % 12
    if cutoff_month == 0:
        cutoff_month = 12
        cutoff_year -= 1
    
    cutoff_month_str = f"{cutoff_year}M{cutoff_month:02d}"

    try:
        # Get references to all documents that are older than the cutoff
        query = db.collection(UNEMPLOYMENT_EDUCATION_COLLECTION).where(firestore.DOCUMENT_ID, '<', cutoff_month_str)
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

    latest_year, latest_month = get_latest_education_month_from_firestore(db)
    
    start_year = 2010
    start_month = 1

    if latest_year and latest_month:
        start_month = latest_month + 1
        start_year = latest_year
        if start_month > 12:
            start_month = 1
            start_year += 1
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting education data fetch from {start_year}M{start_month:02d} onwards.")

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Calculate the latest month for which data is likely to be available
    # Assuming a delay of DATA_FETCH_DELAY_MONTHS (e.g., 2 months)
    latest_available_month = current_month - DATA_FETCH_DELAY_MONTHS
    latest_available_year = current_year

    while latest_available_month <= 0:
        latest_available_month += 12
        latest_available_year -= 1

    if start_year > latest_available_year or (start_year == latest_available_year and start_month > latest_available_month):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Education data is already up-to-date. No new data to fetch.")
        return

    for year in range(start_year, latest_available_year + 1):
        fetch_start_month = start_month if year == start_year else 1
        fetch_end_month = latest_available_month if year == latest_available_year else 12

        if year == latest_available_year:
            for month in range(fetch_start_month, fetch_end_month + 1):
                month_values = [f"{year}M{month:02d}"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching education data for {year}M{month:02d}...")
                
                query_payload = {
                    "query": [
                        {"code": "Alue", "selection": {"filter": "item", "values": list(REGION_MAPPING.keys())}},
                        {"code": "Sukupuoli", "selection": {"filter": "item", "values": list(GENDER_MAPPING.keys())}},
                        {"code": "Koulutusaste", "selection": {"filter": "item", "values": list(EDUCATION_LEVEL_MAPPING.keys())}},
                        {"code": "Kuukausi", "selection": {"filter": "item", "values": month_values}}
                    ],
                    "response": {"format": "json-stat2"}
                }

                try:
                    response = requests.post(statfi_api_url, json=query_payload)
                    response.raise_for_status()
                    data = response.json()

                    if not data.get('value'):
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no new education data for {year}M{month:02d}.")
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
                            monthly_summary["regions"][region_name] = {"genders": {}}

                            for gender_id in gender_ids:
                                gender_code = dimensions['Sukupuoli']['category']['label'][gender_id]
                                gender_name = GENDER_MAPPING.get(gender_code, gender_code)
                                monthly_summary["regions"][region_name]["genders"][gender_name] = {"education_levels": {}}

                                for education_id in education_ids:
                                    education_code = dimensions['Koulutusaste']['category']['label'][education_id]
                                    education_name = EDUCATION_LEVEL_MAPPING.get(education_code, education_code)
                                    
                                    value = values[value_index]
                                    value_index += 1
                                    monthly_summary["regions"][region_name]["genders"][gender_name]["education_levels"][education_name] = value
                            
                            save_education_summary_to_firestore(db, month_code, monthly_summary)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Education data for {year}M{month:02d} fetched and saved.")

                except requests.exceptions.HTTPError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching education data from StatFin API for {year}M{month:02d}: {e}")
                except KeyError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for education data for {year}M{month:02d} (missing key): {e}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for education data for {year}M{month:02d}: {e}")
        else:
            month_values = generate_month_codes(year, fetch_start_month, year, fetch_end_month)
            if not month_values:
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching education data for year {year} ({len(month_values)} months)...")

            query_payload = {
                "query": [
                    {"code": "Alue", "selection": {"filter": "item", "values": list(REGION_MAPPING.keys())}},
                    {"code": "Sukupuoli", "selection": {"filter": "item", "values": list(GENDER_MAPPING.keys())}},
                    {"code": "Koulutusaste", "selection": {"filter": "item", "values": list(EDUCATION_LEVEL_MAPPING.keys())}},
                    {"code": "Kuukausi", "selection": {"filter": "item", "values": month_values}}
                ],
                "response": {"format": "json-stat2"}
            }

            try:
                response = requests.post(statfi_api_url, json=query_payload)
                response.raise_for_status()
                data = response.json()

                if not data.get('value'):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no new education data for year {year}.")
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
                        monthly_summary["regions"][region_name] = {"genders": {}}

                        for gender_id in gender_ids:
                            gender_code = dimensions['Sukupuoli']['category']['label'][gender_id]
                            gender_name = GENDER_MAPPING.get(gender_code, gender_code)
                            monthly_summary["regions"][region_name]["genders"][gender_name] = {"education_levels": {}}

                            for education_id in education_ids:
                                education_code = dimensions['Koulutusaste']['category']['label'][education_id]
                                education_name = EDUCATION_LEVEL_MAPPING.get(education_code, education_code)
                                
                                value = values[value_index]
                                value_index += 1
                                monthly_summary["regions"][region_name]["genders"][gender_name]["education_levels"][education_name] = value
                        
                        save_education_summary_to_firestore(db, month_code, monthly_summary)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Education data for year {year} fetched and saved.")

            except requests.exceptions.HTTPError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching education data from StatFin API for year {year}: {e}")
            except KeyError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for education data for year {year} (missing key): {e}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for education data for year {year}: {e}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Unemployment by education level data update process completed.")
    # delete_oldest_education_summaries(db)

def get_statfi_data(db):
    """
    Fetches new general unemployment data from StatFin API since the last update and saves it to Firestore.
    """
    statfi_api_url = "https://pxdata.stat.fi/PxWeb/api/v1/fi/StatFin/tyonv/statfin_tyonv_pxt_12r5.px"
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data fetch for general unemployment...")

    latest_year, latest_month = get_latest_general_month_from_firestore(db)
    
    start_year = 2010
    start_month = 1

    if latest_year and latest_month:
        start_month = latest_month + 1
        start_year = latest_year
        if start_month > 12:
            start_month = 1
            start_year += 1
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting general data fetch from {start_year}M{start_month:02d} onwards.")

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Calculate the latest month for which data is likely to be available
    # Assuming a delay of DATA_FETCH_DELAY_MONTHS (e.g., 2 months)
    latest_available_month = current_month - DATA_FETCH_DELAY_MONTHS
    latest_available_year = current_year

    while latest_available_month <= 0:
        latest_available_month += 12
        latest_available_year -= 1

    if start_year > latest_available_year or (start_year == latest_available_year and start_month > latest_available_month):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] General unemployment data is already up-to-date.")
        return

    for year in range(start_year, latest_available_year + 1):
        fetch_start_month = start_month if year == start_year else 1
        fetch_end_month = latest_available_month if year == latest_available_year else 12

        # Handle the latest available year by fetching month by month
        if year == latest_available_year:
            for month in range(fetch_start_month, fetch_end_month + 1):
                month_values = [f"{year}M{month:02d}"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching general data for {year}M{month:02d}...")
                
                query_payload = {
                    "query": [
                        {"code": "Alue", "selection": {"filter": "item", "values": list(REGION_MAPPING.keys())}},
                        {"code": "Kuukausi", "selection": {"filter": "item", "values": month_values}},
                        {"code": "Tiedot", "selection": {"filter": "item", "values": list(DATA_TYPE_MAPPING.keys())}}
                    ],
                    "response": {"format": "json-stat2"}
                }

                try:
                    response = requests.post(statfi_api_url, json=query_payload)
                    response.raise_for_status()
                    data = response.json()

                    if not data.get('value'):
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no new general data for {year}M{month:02d}.")
                        continue

                    dimensions = data['dimension']
                    region_ids = dimensions['Alue']['category']['index']
                    month_ids = dimensions['Kuukausi']['category']['index']
                    data_type_ids = dimensions['Tiedot']['category']['index']
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

                            for data_type_id in data_type_ids:
                                data_type_code = dimensions['Tiedot']['category']['label'][data_type_id]
                                data_type_name = DATA_TYPE_MAPPING.get(data_type_code, data_type_code)
                                
                                value = values[value_index]
                                value_index += 1
                                monthly_summary["regions"][region_name][data_type_name] = value
                        
                        save_general_summary_to_firestore(db, month_code, monthly_summary)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] General unemployment data for {year}M{month:02d} fetched and saved.")

                except requests.exceptions.HTTPError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching general data from StatFin API for {year}M{month:02d}: {e}")
                except KeyError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for general data for {year}M{month:02d} (missing key): {e}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for general data for {year}M{month:02d}: {e}")

        # Handle the latest available year by fetching month by month
        if year == latest_available_year:
            for month in range(fetch_start_month, fetch_end_month + 1):
                month_values = [f"{year}M{month:02d}"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching general data for {year}M{month:02d}...")
                
                query_payload = {
                    "query": [
                        {"code": "Alue", "selection": {"filter": "item", "values": list(REGION_MAPPING.keys())}},
                        {"code": "Kuukausi", "selection": {"filter": "item", "values": month_values}},
                        {"code": "Tiedot", "selection": {"filter": "item", "values": list(DATA_TYPE_MAPPING.keys())}}
                    ],
                    "response": {"format": "json-stat2"}
                }

                try:
                    response = requests.post(statfi_api_url, json=query_payload)
                    response.raise_for_status()
                    data = response.json()

                    if not data.get('value'):
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no new general data for {year}M{month:02d}.")
                        continue

                    dimensions = data['dimension']
                    region_ids = dimensions['Alue']['category']['index']
                    month_ids = dimensions['Kuukausi']['category']['index']
                    data_type_ids = dimensions['Tiedot']['category']['index']
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

                            for data_type_id in data_type_ids:
                                data_type_code = dimensions['Tiedot']['category']['label'][data_type_id]
                                data_type_name = DATA_TYPE_MAPPING.get(data_type_code, data_type_code)
                                
                                value = values[value_index]
                                value_index += 1
                                monthly_summary["regions"][region_name][data_type_name] = value
                        
                        save_general_summary_to_firestore(db, month_code, monthly_summary)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] General unemployment data for {year}M{month:02d} fetched and saved.")

                except requests.exceptions.HTTPError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching general data from StatFin API for {year}M{month:02d}: {e}")
                except KeyError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for general data for {year}M{month:02d} (missing key): {e}")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for general data for {year}M{month:02d}: {e}")
        else:
            month_values = generate_month_codes(year, fetch_start_month, year, fetch_end_month)
            if not month_values:
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching general data for year {year} ({len(month_values)} months)...")

            query_payload = {
                "query": [
                    {"code": "Alue", "selection": {"filter": "item", "values": list(REGION_MAPPING.keys())}},
                    {"code": "Kuukausi", "selection": {"filter": "item", "values": month_values}},
                    {"code": "Tiedot", "selection": {"filter": "item", "values": list(DATA_TYPE_MAPPING.keys())}}
                ],
                "response": {"format": "json-stat2"}
            }

            try:
                response = requests.post(statfi_api_url, json=query_payload)
                response.raise_for_status()
                data = response.json()

                if not data.get('value'):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] API returned no new general data for year {year}.")
                    continue

                dimensions = data['dimension']
                region_ids = dimensions['Alue']['category']['index']
                month_ids = dimensions['Kuukausi']['category']['index']
                data_type_ids = dimensions['Tiedot']['category']['index']
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

                        for data_type_id in data_type_ids:
                            data_type_code = dimensions['Tiedot']['category']['label'][data_type_id]
                            data_type_name = DATA_TYPE_MAPPING.get(data_type_code, data_type_code)
                            
                            value = values[value_index]
                            value_index += 1
                            monthly_summary["regions"][region_name][data_type_name] = value
                    
                    save_general_summary_to_firestore(db, month_code, monthly_summary)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] General unemployment data for year {year} fetched and saved.")

            except requests.exceptions.HTTPError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching general data from StatFin API for year {year}: {e}")
            except KeyError as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error parsing StatFin API response for general data for year {year} (missing key): {e}")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] An unexpected error occurred for general data for year {year}: {e}")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] General unemployment data update process completed.")