# Projektiloki: Marraskuu2025

Tämä tiedosto dokumentoi Marraskuu2025-projektin suunnittelun ja toteutuksen.

## 15. marraskuuta 2025

*   **Tehtävä:** Projektin alustus.
*   **Toimenpiteet:**
    *   Luotiin paikallinen kansio `C:\Users\henry\marraskuu2025`.
    *   Kloonattiin tyhjä GitHub-arkisto osoitteesta `https://github.com/henrysaarinen71-art/Marraskuu2025.git` paikalliseen kansioon.
    *   Luotiin tämä lokitiedosto (`projektiloki.md`) seuraamaan projektin edistymistä.

*   **Tehtävä:** Firebase-yhteyden muodostaminen.
*   **Status:** **Valmis.** Yhteys Firebaseen ja Firestoreen on onnistuneesti muodostettu.

*   **Tehtävä:** Projektin perustiedostojen ja turvallisuusasetusten vienti GitHubiin.
*   **Toimenpiteet:**
    *   Luotiin `README.md`-tiedosto, joka sisältää projektin kuvauksen ja turvallisuusohjeistuksen.
    *   Varmistettiin, että `.gitignore` estää arkaluontoisten tiedostojen versionhallinnan.
    *   Kaikki tiedostot (paitsi `firebase-credentials.json`) on lisätty, committoitu ja pushattu GitHub-arkistoon.
*   **Status:** **Valmis.**

*   **Tehtävä:** Datan haku ulkoisesta API-rajapinnasta (StatFin) ja tallennus Firestoreen.
*   **Toimenpiteet:**
    *   Päivitettiin `main.py`-tiedosto sisältämään funktiot kuukausikoodien generointiin (tammikuusta 2008 nykyiseen kuukauteen), StatFin API -kyselyn rakentamiseen, API-pyynnön tekemiseen ja JSON-vastauksen jäsentämiseen.
    *   Korjattiin JSON-vastauksen jäsentämislogiikkaa (`data['dataset']['dimension']` -> `data['dimension']`).
    *   Implementoitiin sivutusstrategia, jossa data haetaan vuosittain erillisillä API-kutsuilla, jotta vältetään API:n pyyntökoon rajoitukset.
    *   Lisättiin robusti virheenkäsittely `400 Client Error` -virheelle nykyisen vuoden datan haussa. Skripti haki onnistuneesti datan vuoteen 2024 asti ja vuoden 2025 osalta syyskuuhun (2025M09) asti.
    *   Lisättiin logiikka datan tallentamiseksi Firestoren `unemployment_data`-kokoelmaan.
    *   Poistettiin virheenkorjaustulosteet.
*   **Status:** **Valmis.** Kaikki saatavilla oleva historiallinen data on haettu ja tallennettu Firestoreen.

*   **Seuraava tehtävä:** Automatisoidun kuukausittaisen päivityksen suunnittelu ja toteutus.
*   **Status:** Odottaa käyttäjän vahvistusta.