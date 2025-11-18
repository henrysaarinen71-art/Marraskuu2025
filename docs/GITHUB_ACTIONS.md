# Marraskuu2025: GitHub Actions

Tämä dokumentti kuvaa projektin GitHub Actions -työnkulut.

## Kuukausittainen datan päivitys (`monthly_update.yml`)

Tämä työnkulku vastaa projektin datan automaattisesta päivittämisestä.

### Tavoite

Varmistaa, että Firestore-tietokannassa on aina tuorein saatavilla oleva työttömyys- ja uutisdata.

### Käynnistimet (Triggers)

Työnkulku käynnistyy automaattisesti:

*   **Ajastetusti:** Joka kuukauden 10., 15. ja 20. päivä klo 08:00 UTC. Tämä varmistaa, että uusi data haetaan pian sen jälkeen, kun se on todennäköisesti julkaistu.
*   **Manuaalisesti:** Voit käynnistää työnkulun myös manuaalisesti GitHubin "Actions"-välilehdeltä (`workflow_dispatch`).

### Työnkulun vaiheet

1.  **Checkout repository:** Kloonaa projektin koodin.
2.  **Set up Python:** Asettaa käyttöön Python-version 3.11.
3.  **Install dependencies:** Asentaa tarvittavat Python-kirjastot `backend/requirements.txt`-tiedostosta.
4.  **Run data update script:** Suorittaa `backend/main.py`-skriptin, joka käynnistää datan haku- ja prosessointiprosessin.

### Salaisuuksien hallinta (Secrets)

Työnkulku vaatii seuraavat salaisuudet (GitHub Secrets), jotta se voi toimia oikein:

*   `FIREBASE_CREDENTIALS_BASE64`: Base64-enkoodattu versio `firebase-credentials.json`-palvelutilin avaimesta.
*   `GEMINI_API_KEY`: Google Gemini API -avain.

**Ohjeet salaisuuksien asettamiseen:**

1.  Mene GitHub-repositorion "Settings"-välilehdelle.
2.  Valitse "Secrets and variables" -> "Actions".
3.  Klikkaa "New repository secret" ja lisää yllä mainitut salaisuudet.

**`FIREBASE_CREDENTIALS_BASE64`-salaisuuden luominen:**

Voit luoda Base64-enkoodatun version `firebase-credentials.json`-tiedostosta paikallisesti seuraavalla komennolla:

```bash
# Linux/macOS
base64 -w 0 firebase-credentials.json

# Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("firebase-credentials.json"))
```

Kopioi tuloste ja liitä se `FIREBASE_CREDENTIALS_BASE64`-salaisuuden arvoksi GitHubiin.
