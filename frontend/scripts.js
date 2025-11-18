// Firebase app and db are now initialized in index.html and made globally available
// const app = window.app;
// const db = window.db;

const regions = ["Helsinki", "Espoo", "Vantaa", "Kauniainen"];
const dataTypes = {
    "TYOTTOMATLOPUSSA": "Työttömät työnhakijat yhteensä",
    "TYOTTOMATMIEHET": "Työttömät työnhakijat, miehet",
    "TYOTTOMATNAISET": "Työttömät työnhakijat, naiset",
    "TYOTTOMAT20": "Alle 20-v. työttömät työnhakijat",
    "TYOTTOMAT25": "Alle 25-v. työttömät työnhakijat",
    "TYOTTOMAT50": "Yli 50-v. työttömät työnhakijat",
    "TYOTTOMATULK": "Ulkomaalaisia työttömiä työnhakijat",
    "PITKAAIKAISTYOTTOMAT": "Pitkäaikaistyöttömät"
};

const dataContainer = document.getElementById('data-container');

async function fetchData() {
    try {
        const query = db.collection('unemployment_general_summary').orderBy('year_month', 'desc').limit(1);
        const snapshot = await query.get();

        if (snapshot.empty) {
            dataContainer.innerHTML = '<p>Dataa ei löytynyt.</p>';
            return;
        }

        const latestData = snapshot.docs[0].data();
        renderData(latestData);
    } catch (e) {
        console.error("Error fetching data:", e);
        dataContainer.innerHTML = '<p>Datan lataus epäonnistui.</p>';
    }
}

function renderData(data) {
    dataContainer.innerHTML = '';

    const regionsData = data.regions;

    for (const region of regions) {
        const regionData = regionsData[region];
        if (!regionData) continue;

        const regionCard = document.createElement('div');
        regionCard.className = 'col-md-6 col-lg-3 mb-4';

        let cardHtml = `<div class="card">
                            <div class="card-header">
                                <h3>${region}</h3>
                            </div>
                            <ul class="list-group list-group-flush">`;

        for (const dataType in regionData) {
            const value = regionData[dataType];
            cardHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                            ${dataType}: ${value}
                         </li>`;
        }

        cardHtml += `</ul></div>`;
        regionCard.innerHTML = cardHtml;
        dataContainer.appendChild(regionCard);
    }
}

function getArrow(trend) {
    if (trend === 'up') {
        return '<span class="arrow-up">▲</span>';
    } else if (trend === 'down') {
        return '<span class="arrow-down">▼</span>';
    } else {
        return '';
    }
}

const reportModal = document.getElementById('reportModal');
const reportContent = document.getElementById('report-content');

reportModal.addEventListener('show.bs.modal', async function () {
    const report = await getLatestReport();
    if (report) {
        reportContent.innerHTML = report.report.replace(/\n/g, '<br>');
    } else {
        reportContent.innerHTML = "Raporttia ei löytynyt.";
    }
});

async function getLatestReport() {
    try {
        const query = db.collection('monthly_reports').orderBy('year_month', 'desc').limit(1);
        const snapshot = await query.get();
        if (snapshot.empty) {
            return null;
        }
        return snapshot.docs[0].data();
    } catch (e) {
        console.error("Error fetching latest report:", e);
        return null;
    }
}

fetchData();
