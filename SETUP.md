# Marraskuu2025: Asennusohjeet

Tämä tiedosto sisältää ohjeet projektin paikalliseen asentamiseen ja ajamiseen.

## Edellytykset

*   Python 3.9 tai uudempi
*   Git
*   Firebase-projekti

## Asennus

1.  **Kloonaa projekti:**

    ```bash
    git clone <repository-url>
    cd marraskuu2025
    ```

2.  **Asenna riippuvuudet:**

    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Konfiguroi Firebase:**

    *   Luo Firebase-projekti [Firebase-konsolissa](https://console.firebase.google.com/).
    *   Luo palvelutilin avain:
        *   Mene projektiisi -> Project settings -> Service accounts.
        *   Valitse "Python" ja klikkaa "Generate new private key".
        *   Tämä lataa JSON-tiedoston. Nimeä se `firebase-credentials.json` ja sijoita se `backend`-kansioon.
    *   **TÄRKEÄÄ:** `firebase-credentials.json` on lisätty `.gitignore`-tiedostoon, jotta se ei päädy versionhallintaan.

4.  **Konfiguroi Gemini API:**

    *   Hanki Gemini API-avain [Google AI Studion](https://aistudio.google.com/app/apikey) kautta.
    *   Luo `backend`-kansioon tiedosto nimeltä `GEMINI_API_KEY.txt`.
    *   Liitä API-avaimesi tähän tiedostoon.
    *   **TÄRKEÄÄ:** `GEMINI_API_KEY.txt` on lisätty `.gitignore`-tiedostoon.

## Paikallinen ajaminen

Kun olet suorittanut asennusvaiheet, voit ajaa sovelluksen:

```bash
python backend/main.py
```

Sovellus hakee datan StatFin- ja Google News -rajapinnoista, prosessoi sen ja tallentaa sen Firestoreen. Lisäksi se generoi kuukausiraportin Gemini API:n avulla.
