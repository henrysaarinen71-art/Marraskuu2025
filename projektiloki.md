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

*   **Tehtävä:** Google News -integraation toteutus.

    *   **Status:** **Valmis.**

    *   **Kuvaus:** Lisätty toiminnallisuus, joka hakee SerpAPI:n avulla työmarkkinoihin liittyviä uutisia ja tallentaa ne Firestoreen `news_articles`-kokoelmaan. Vanhat uutiset poistetaan automaattisesti ennen uusien hakua.



*   **Tehtävä:** Projektin refaktorointi orkestrointimallia varten.

    *   **Status:** **Valmis.**

    *   **Kuvaus:** Projektin rakenne on uudistettu modulaarisemmaksi. Datanhakulogiikka on siirretty omiin "työkaluihin" (`orchestrator/tools`), ja agenttien ja orkestroijan toteutukselle on luotu paikkamerkit.



*   **Tehtävä:** Lisätty uusia tilastoja datankeräykseen.

    *   **Status:** **Valmis.**

    *   **Kuvaus:** Päivitetty `statfin_tool.py` hakemaan myös alle 20-vuotiaiden, alle 25-vuotiaiden, yli 50-vuotiaiden, ulkomaalaisten ja pitkäaikaistyöttömien työttömyystilastot.



*   **Tehtävä:** Ensimmäisen ala-agentin (kuukausikatsausagentti) pohjan luominen.
    *   **Status:** **Valmis.**
    *   **Kuvaus:** Luotu `monthly_report_agent.py`, joka hakee viimeisimmän kuukauden datan Firebasesta ja muodostaa siitä raportin. Tällä hetkellä agentti tulostaa datan ja Gemini-promptin, mutta tulevaisuudessa se tulee käyttämään Geminiä luonnollisen kielen raportin luomiseen.

*   **Tehtävä:** Gemini API -integraatio kuukausikatsausagenttiin.
    *   **Status:** **Valmis.**
    *   **Kuvaus:** `monthly_report_agent.py`-tiedostoa on päivitetty käyttämään Google Gemini API:a luonnollisen kielen raporttien luomiseen. `google-generativeai` -kirjasto on lisätty `requirements.txt`-tiedostoon ja Gemini API-avain ladataan ympäristömuuttujasta (`GEMINI_API_KEY`).

*   **Tehtävä:** Koulutusdatan tallennusrakenteen ja vanhan datan poistomekanismin toteutus.
    *   **Status:** **Valmis.**
    *   **Kuvaus:** `statfin_tool.py`-tiedostoa on muutettu tallentamaan koulutusdata Firestoreen uuteen, tiiviimpään ja helpommin käsiteltävään nested map -rakenteeseen (`unemployment_by_education_summary`-kokoelmaan). Lisäksi on toteutettu mekanismi, joka poistaa automaattisesti yli 10 vuotta vanhan koulutusdatan tietokannasta tilan säästämiseksi. Samalla korjattiin virhe, jossa StatFin API palautti 400-virheen, kun yritettiin hakea koko vuoden dataa, jos osa kuukausista ei ollut vielä saatavilla. Nyt haku tehdään kuukausittain kuluvan vuoden osalta.

## 16. marraskuuta 2025

*   **Tehtävä:** Datan tallennusrakenteen korjaus ja vanhan datan siivous.
*   **Status:** **Valmis.**
*   **Kuvaus:**
    *   **ONGELMA:** Firebasen `unemployment_data`-kokoelman tietorakenne oli litteä ja epälooginen, mikä aiheutti sekaannusta. Koulutustason mukaiset työttömyystiedot olivat tarkoitus tallentaa jäsennellysti.
    *   **KORJAUS:**
        1.  Korjattu `SyntaxError` `orchestrator/tools/statfin_tool.py`-tiedostossa, joka esti sovelluksen suorittamisen.
        2.  Tehostettu historiallisen datan hakua `get_unemployment_by_education_data`-funktiossa poistamalla tarpeettomat kuukausittaiset API-kutsut ja korvaamalla ne yhdellä vuosittaisella kutsulla.
        3.  Poistettu vanhentunut `get_statfi_data`-funktio käytöstä, joka loi sekavaa ja litteää dataa `unemployment_data`-kokoelmaan.
        4.  Poistettu vanha `unemployment_data`-kokoelma Firebasesta erillisellä siivousskriptillä.
    *   **TULOS:** Datan haku on nyt tehokkaampaa ja vain jäsenneltyä, koulutustason mukaista työttömyysdataa tallennetaan `unemployment_by_education_summary`-kokoelmaan. Tämä selkeyttää tietokannan rakennetta ja vastaa projektin tavoitteita.