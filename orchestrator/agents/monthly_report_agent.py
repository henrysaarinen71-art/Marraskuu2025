import os
import google.generativeai as genai
from firebase_admin import firestore
from orchestrator.tools.statfin_tool import get_latest_month_from_firestore, DATA_TYPE_MAPPING, REGION_MAPPING

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_latest_monthly_data(db, year, month):
    """
    Fetches all unemployment data for a specific month from Firestore.
    """
    try:
        month_str = f"{year}M{month:02d}"
        query = db.collection('unemployment_data').where('year_month', '==', month_str)
        results = query.get()
        return [doc.to_dict() for doc in results]
    except Exception as e:
        print(f"Error fetching latest monthly data: {e}")
        return []

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

    latest_year, latest_month = get_latest_month_from_firestore(db)

    if not latest_year or not latest_month:
        return "Could not generate monthly report because no data was found in Firestore."

    monthly_data = get_latest_monthly_data(db, latest_year, latest_month)

    if not monthly_data:
        return f"Could not generate monthly report because no data was found for {latest_year}-{latest_month}."

    # Group data by region
    data_by_region = {region: [] for region in REGION_MAPPING.values()}
    for item in monthly_data:
        region_name = item.get("region_name")
        if region_name in data_by_region:
            data_by_region[region_name].append(item)

    # Format the data for the Gemini prompt
    report_data = ""
    for region, data in data_by_region.items():
        report_data += f"## {region}\n\n"
        for item in sorted(data, key=lambda x: x['data_type_name']):
            report_data += f"- {item['data_type_name']}: {item['value']}\n"
        report_data += "\n"

    # Placeholder for Gemini AI call
    # In the future, we will send this data to Gemini to generate a natural language report.
    gemini_prompt = f"""
    Tehtäväsi on luoda kuukausikatsaus pääkaupunkiseudun työllisyystilanteesta.
    Käytä vain alla olevaa dataa. Älä käytä mitään ulkoisia lähteitä tai verkkohakua.
    Analysoi data ja luo ytimekäs yhteenveto kunkin kaupungin osalta.
    
    Data:
    {report_data}
    """

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(gemini_prompt)
        report_content = response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        report_content = f"Error generating report with Gemini: {e}\n\n{gemini_prompt}"

    save_report_to_firestore(db, report_content, latest_year, latest_month)
    
    print("Monthly report generated and saved.")
    return report_content
