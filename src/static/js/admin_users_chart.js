document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.querySelector("canvas[id^='usersChart']");
    if (!canvas) return;

    const labels = JSON.parse(canvas.dataset.labels || "[]");
    const values = JSON.parse(canvas.dataset.values || "[]");

    const ctx = canvas.getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Usuarios nuevos',
                data: values,
                borderColor: '#5cb85c',
                backgroundColor: 'rgba(92,184,92,0.15)',
                borderWidth: 3,
                tension: 0.3,
                pointRadius: 5,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            legend: { display: false },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});
