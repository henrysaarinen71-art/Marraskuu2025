import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64

from orchestrator.tools.statfin_tool import get_statfi_data, get_unemployment_by_education_data, get_unemployment_by_occupation_data
from orchestrator.tools.google_news_tool import get_google_news_data

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
            cred_path = os.path.join(os.path.dirname(__file__), 'botti-23428-firebase-adminsdk-fbsvc-d404b9f76d.json')
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

from orchestrator.agents.monthly_report_agent import generate_monthly_report

def main():
    """
    Main function to run the application.
    """
    print("Starting the application...")
    db = initialize_firebase()

    if db:
        print("Successfully connected to Firestore.")
        # In the future, the orchestrator will decide which tools to run.
        # For now, we run them sequentially.
        get_statfi_data(db)
        # get_google_news_data(db) # Temporarily disabled to stop SerpAPI calls
        get_unemployment_by_education_data(db) # Fetch unemployment by education data
        get_unemployment_by_occupation_data(db) # Fetch unemployment by occupation data

        # Generate and print the monthly report
        monthly_report = generate_monthly_report(db)
        print("\n--- Monthly Report ---")
        print(monthly_report)
        print("--- End of Report ---\n")

        print("Application finished.")
    else:
        print("Failed to connect to Firestore. Please check the error messages above.")

if __name__ == '__main__':
    main()
