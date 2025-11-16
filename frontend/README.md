# Frontend

This directory contains the frontend of the application. It is a simple web page that displays the unemployment data from the Firestore database.

## How to use

1.  **Configure Firebase:** The frontend needs to be connected to your Firebase project. Open the `scripts.js` file and replace the placeholder `firebaseConfig` object with your actual Firebase project configuration. You can find this in your Firebase project settings under "Your apps" -> "Web app".

2.  **Update `.firebaserc`:** Open the `.firebaserc` file in the root of the project and replace the placeholder `YOUR_FIREBASE_PROJECT_ID` with your actual Firebase project ID.

3.  **Deploy to Firebase:** After the configuration is done, you can deploy the frontend to Firebase Hosting by running the following command in your terminal:

    ```bash
    firebase deploy --only hosting
    ```

## Data Source

The frontend fetches data from the `unemployment_data` collection in your Firestore database. It does not connect directly to the StatFin API. This is to avoid overloading the StatFin API and to ensure that the data is consistent with the data in our database.
