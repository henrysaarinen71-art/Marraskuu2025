import os
import google.generativeai as genai
from firebase_admin import firestore
from orchestrator.tools.statfin_tool import get_latest_general_month_from_firestore, DATA_TYPE_MAPPING, REGION_MAPPING

# Construct the absolute path to GEMINI_API_KEY.txt
gemini_api_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'GEMINI_API_KEY.txt')

# Read the API key from the file
try:
    with open(gemini_api_key_path, 'r') as f:
        gemini_api_key = f.read().strip()
    genai.configure(api_key=gemini_api_key)
except FileNotFoundError:
    print(f"Error: GEMINI_API_KEY.txt not found at {gemini_api_key_path}")
    genai.configure(api_key=None) # Configure with None to allow error to propagate
except Exception as e:
    print(f"Error reading GEMINI_API_KEY.txt: {e}")
    genai.configure(api_key=None) # Configure with None to allow error to propagate

def get_latest_monthly_data(db, year, month):
    """
    Fetches the general unemployment data summary for a specific month from Firestore.
    """
    try:
        month_str = f"{year}M{month:02d}"
        doc_ref = db.collection('unemployment_general_summary').document(month_str)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None
    except Exception as e:
        print(f"Error fetching latest monthly data: {e}")
        return None

def save_report_to_firestore(db, report, year, month):
    """
    Saves the monthly report to the 'monthly_reports' collection in Firestore.
    """
    try:
        month_str = f"{year}M{month:02d}"
        doc_ref = db.collection('monthly_reports').document(month_str)
        doc_ref.set({
            "report": report,
            "year_month": month_str,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print(f"Monthly report for {month_str} saved to Firestore.")
    except Exception as e:
        print(f"Error saving report to Firestore: {e}")

def generate_monthly_report(db):
    """
    Generates a monthly report on the employment situation in the Helsinki metropolitan area.
    """
    print("Generating monthly report...")

    latest_year, latest_month = get_latest_general_month_from_firestore(db)

    if not latest_year or not latest_month:
        return "Could not generate monthly report because no data was found in Firestore."

    monthly_data = get_latest_monthly_data(db, latest_year, latest_month)

    if not monthly_data:
        return f"Could not generate monthly report because no data was found for {latest_year}-{latest_month}."

    # Format the data for the Gemini prompt
    report_data = ""
    regions = monthly_data.get("regions", {})
    for region_name, data in sorted(regions.items()):
        report_data += f"## {region_name}\n\n"
        # Sort the data by the keys (data type names)
        for data_type_name, value in sorted(data.items()):
            report_data += f"- {data_type_name}: {value}\n"
        report_data += "\n"

    gemini_prompt = f"""
    Tehtäväsi on luoda kuukausikatsaus pääkaupunkiseudun työllisyystilanteesta.
    Käytä vain alla olevaa dataa. Älä käytä mitään ulkoisia lähteitä tai verkkohakua.
    Analysoi data ja luo ytimekäs yhteenveto kunkin kaupungin osalta.
    
    Data:
    {report_data}
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-pro-preview-03-25")
        response = model.generate_content(gemini_prompt)
        report_content = response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        report_content = f"Error generating report with Gemini: {e}\n\n{gemini_prompt}"

    save_report_to_firestore(db, report_content, latest_year, latest_month)
    
    print("Monthly report generated and saved.")
    return report_content