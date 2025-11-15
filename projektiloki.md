# Projektiloki: Marraskuu2025

Tämä tiedosto dokumentoi Marraskuu2025-projektin suunnittelun ja toteutuksen.

## 15. marraskuuta 2025

*   **Tehtävä:** Projektin alustus.
*   **Status:** **Valmis.**

*   **Tehtävä:** Firebase-yhteyden muodostaminen.
*   **Status:** **Valmis.**

*   **Tehtävä:** Projektin perustiedostojen ja turvallisuusasetusten vienti GitHubiin.
*   **Status:** **Valmis.**

*   **Tehtävä:** Datan haku ulkoisesta API-rajapinnasta (StatFin) ja tallennus Firestoreen.
*   **Status:** **Valmis.** Kaikki saatavilla oleva historiallinen data on haettu ja tallennettu Firestoreen.

*   **Tehtävä:** Automatisoidun kuukausittaisen päivityksen toteutus.
*   **Suunnitelma:**
    1.  Muokattiin `main.py`-skriptiä hakemaan vain uutta dataa vertaamalla Firebasen viimeisimpään tallennettuun kuukauteen.
    2.  Muokattiin `initialize_firebase`-funktiota tukemaan sekä paikallista kehitystä (`firebase-credentials.json`-tiedosto) että automaatiota GitHub Actionsissa (ympäristömuuttuja).
    3.  Luotiin GitHub Actions -työnkulku (`.github/workflows/monthly_update.yml`), joka suorittaa päivitysskriptin automaattisesti jokaisen kuukauden 10., 15. ja 20. päivä.
*   **Status:** Koodi ja työnkulku valmiina. Odottaa, että käyttäjä asettaa `FIREBASE_CREDENTIALS_BASE64`-salaisuuden GitHub-arkistoon.
