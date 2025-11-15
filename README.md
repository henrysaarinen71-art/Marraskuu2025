# Marraskuu2025-projekti

Tämä on kehitysympäristö sovellukselle, joka kerää, analysoi ja tallentaa tilastotietoa Firebaseen.

## Kuvaus

Projektin tavoitteena on rakentaa järjestelmä, joka:
1.  Hakee dataa ulkoisista API-rajapinnoista.
2.  Tallentaa ja hallinnoi kerättyä dataa Google Firebasessa.
3.  Suorittaa säännöllisiä, automaattisia datanpäivityksiä.

## Turvallisuusohjeistus

**ÄLÄ KOSKAAN TALLENNA SALAISUUKSIA TAI PALVELUTUNNUKSIA GITHUBIIN.**

Tämä projekti käyttää `.gitignore`-tiedostoa estääkseen arkaluontoisten tiedostojen, kuten `firebase-credentials.json` ja `.env`, versionhallintaan päätymisen. Varmista, että kaikki avaimet ja salaisuudet pysyvät paikallisessa ympäristössäsi.
