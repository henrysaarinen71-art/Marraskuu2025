import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using the service account key.
    """
    try:
        # The name of the credentials file is hardcoded for simplicity as requested.
        cred_path = 'firebase-credentials.json'

        if not os.path.exists(cred_path):
            print(f"Error: The Firebase credentials file was not found.")
            print(f"Please make sure a file named '{cred_path}' is in the same directory as this script.")
            return None

        # Initialize the app with a service account, granting admin privileges
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        print("Firebase connection initialized successfully.")
        
        # Return the Firestore client
        return firestore.client()

    except Exception as e:
        print(f"An error occurred during Firebase initialization: {e}")
        return None

def main():
    """
    Main function to run the application.
    """
    print("Starting the application...")
    db = initialize_firebase()

    if db:
        print("Successfully connected to Firestore.")
        # Here we will later add logic to fetch data and write to Firestore.
        # For now, we just test the connection.
        print("Application finished.")
    else:
        print("Failed to connect to Firestore. Please check the error messages above.")

if __name__ == '__main__':
    main()
