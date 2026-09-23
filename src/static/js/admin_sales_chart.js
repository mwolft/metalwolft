document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.querySelector("canvas[id^='salesChart']");
    if (!canvas) return;

    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const values = JSON.parse(canvas.dataset.values || "[]");
    const adsValues = JSON.parse(canvas.dataset.adsValues || "[]");

    const ctx = canvas.getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Ventas',
                    data: values,
                    yAxisID: 'y',
                    borderColor: '#337ab7',
                    backgroundColor: 'rgba(51,122,183,0.15)',
                    borderWidth: 3,
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    fill: true
                },
                {
                    label: 'Google Ads',
                    data: adsValues,
                    yAxisID: 'yAds',
                    borderColor: '#cf1c35',
                    backgroundColor: '#cf1c35',
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    spanGaps: false,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    position: 'left',
                    title: { display: true, text: 'Ventas (€)' }
                },
                yAds: {
                    beginAtZero: true,
                    position: 'right',
                    title: { display: true, text: 'Google Ads (€)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
});
