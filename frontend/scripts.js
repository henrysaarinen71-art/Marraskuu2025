// Your web app's Firebase configuration
// IMPORTANT: Replace with your actual Firebase project configuration
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_AUTH_DOMAIN",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_STORAGE_BUCKET",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();

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
    const latestData = {};

    for (const region of regions) {
        latestData[region] = {};
        for (const dataType in dataTypes) {
            const query = db.collection('unemployment_data')
                .where('region_name', '==', region)
                .where('data_type_code', '==', dataType)
                .orderBy('year_month', 'desc')
                .limit(13); // Fetch last 13 months to get previous year and month

            const snapshot = await query.get();
            const docs = snapshot.docs.map(doc => doc.data());

            if (docs.length > 0) {
                const currentMonthData = docs[0];
                const prevMonthData = docs[1];
                const prevYearData = docs[12];

                let monthTrend = 'neutral';
                if (prevMonthData) {
                    if (currentMonthData.value > prevMonthData.value) {
                        monthTrend = 'down';
                    } else if (currentMonthData.value < prevMonthData.value) {
                        monthTrend = 'up';
                    }
                }

                let yearTrend = 'neutral';
                if (prevYearData) {
                    if (currentMonthData.value > prevYearData.value) {
                        yearTrend = 'down';
                    } else if (currentMonthData.value < prevYearData.value) {
                        yearTrend = 'up';
                    }
                }

                latestData[region][dataType] = {
                    value: currentMonthData.value,
                    monthTrend: monthTrend,
                    yearTrend: yearTrend
                };
            }
        }
    }

    renderData(latestData);
}

function renderData(data) {
    dataContainer.innerHTML = '';

    for (const region of regions) {
        const regionCard = document.createElement('div');
        regionCard.className = 'col-md-6 col-lg-3 mb-4';

        let cardHtml = `<div class="card">
                            <div class="card-header">
                                <h3>${region}</h3>
                            </div>
                            <ul class="list-group list-group-flush">`;

        for (const dataType in data[region]) {
            const item = data[region][dataType];
            cardHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                            ${dataTypes[dataType]}: ${item.value}
                            <span>
                                ${getArrow(item.monthTrend)}
                                ${getArrow(item.yearTrend)}
                            </span>
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
