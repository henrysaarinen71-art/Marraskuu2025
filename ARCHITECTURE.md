# Marraskuu2025: Arkkitehtuuri

Tämä dokumentti kuvaa Marraskuu2025-projektin arkkitehtuurin ja datavirran.

## Yleiskatsaus

Projekti on rakennettu monorepo-tyylisesti, jossa on eroteltu `backend`- ja `frontend`-osiot. Tavoitteena on kerätä, prosessoida ja esittää Suomen pääkaupunkiseudun työttömyysdataa.

## Komponentit

### 1. Backend

*   **Kieli:** Python
*   **Sijainti:** `/backend`
*   **Pääohjelma:** `main.py`

**Toiminnallisuus:**

*   **Orkestroija (`orchestrator/`):** Vastaa datan keräämisen ja prosessoinnin työnkulusta. Tulevaisuudessa tämä komponentti tulee sisältämään älykkäämpiä agentteja, jotka voivat päättää, mitä dataa haetaan ja milloin.
*   **Työkalut (`orchestrator/tools/`):**
    *   `statfin_tool.py`: Hakee työttömyysdataa Tilastokeskuksen (StatFin) PX-Web API -rajapinnasta.
    *   `google_news_tool.py`: Hakee työmarkkinoihin liittyviä uutisia Google News -rajapinnasta (SerpAPI:n kautta).
*   **Agentit (`orchestrator/agents/`):**
    *   `monthly_report_agent.py`: Käyttää Google Gemini API:a luodakseen luonnollisen kielen kuukausiraportin kerätystä datasta.

### 2. Frontend

*   **Teknologiat:** HTML, CSS, JavaScript
*   **Sijainti:** `/frontend`

**Toiminnallisuus:**

*   Esittää Firebasesta haetun datan käyttäjälle.
*   Lukee dataa suoraan Firestoresta käyttäen Firebase Web SDK:ta.

### 3. Tietokanta

*   **Palvelu:** Google Firestore
*   **Rakenne:**
    *   `unemployment_general_summary`: Sisältää yleiset kuukausittaiset työttömyystilastot.
    *   `unemployment_by_education_summary`: Sisältää kuukausittaiset työttömyystilastot koulutustason mukaan.
    *   `unemployment_by_occupation_summary`: Sisältää kuukausittaiset työttömyystilastot ammattiryhmän mukaan.
    *   `monthly_reports`: Sisältää Gemini API:n generoimat kuukausiraportit.
    *   `news_articles`: Sisältää Google Newsista haetut uutisartikkelit.

## Datavirta

1.  **Datan keräys:**
    *   `backend/main.py` käynnistää orkestroijan.
    *   Orkestroija kutsuu `statfin_tool.py`:tä ja `google_news_tool.py`:tä.
    *   `statfin_tool.py` tekee API-kutsun StatFin-rajapintaan ja hakee työttömyysdatat.
    *   `google_news_tool.py` tekee API-kutsun SerpAPI-rajapintaan ja hakee uutisdatan.

2.  **Datan tallennus:**
    *   Kerätty data tallennetaan jäsennellyssä muodossa Firestoreen yllä mainittuihin kokoelmiin.

3.  **Raportin generointi:**
    *   `monthly_report_agent.py` hakee viimeisimmän datan Firestoresta.
    *   Data muotoillaan promptiksi ja lähetetään Gemini API:lle.
    *   Gemini API palauttaa luonnollisen kielen raportin, joka tallennetaan `monthly_reports`-kokoelmaan.

4.  **Datan esittäminen:**
    *   `frontend/index.html` ja `frontend/scripts.js` käyttävät Firebase Web SDK:ta.
    *   Frontend hakee datan suoraan Firestoresta ja näyttää sen käyttäjälle.

## Kommunikaatio

*   **Backend <-> Frontend:** Kommunikaatio on epäsuoraa ja tapahtuu Firebasen kautta. Backend kirjoittaa dataa Firestoreen, ja frontend lukee sitä sieltä. Tämä erottaa komponentit toisistaan ja mahdollistaa niiden itsenäisen kehityksen.
