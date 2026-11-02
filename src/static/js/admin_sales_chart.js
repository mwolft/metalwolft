document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.querySelector("canvas[id^='salesChart']");
    const metric = document.getElementById('sales-metric');
    if (!canvas || !metric || typeof Chart === 'undefined') return;

    const labels = JSON.parse(canvas.dataset.labels || '[]');
    const amounts = JSON.parse(canvas.dataset.amounts || '[]');
    const orders = JSON.parse(canvas.dataset.orders || '[]');
    const future = JSON.parse(canvas.dataset.future || '[]');
    const currentMonth = Number(canvas.dataset.currentMonth);
    const chart = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels.map((label, index) => {
                if (future[index]) return label + ' (futuro)';
                return index + 1 === currentMonth ? label + ' (en curso)' : label;
            }),
            datasets: [{
                label: 'Importe registrado (€)',
                data: amounts.map((value, index) => future[index] ? null : value),
                backgroundColor: labels.map((_, index) => index + 1 === currentMonth ? '#b52538' : '#337ab7'),
                borderRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: {}, title: { display: true, text: 'Importe registrado (€)' } } }
        }
    });

    metric.addEventListener('change', function () {
        const showOrders = metric.value === 'orders';
        const label = showOrders ? 'Pedidos registrados' : 'Importe registrado (€)';
        chart.data.datasets[0].label = label;
        chart.data.datasets[0].data = (showOrders ? orders : amounts).map(
            (value, index) => future[index] ? null : value
        );
        chart.options.scales.y.title.text = label;
        chart.options.scales.y.ticks.precision = showOrders ? 0 : undefined;
        canvas.setAttribute('aria-label', label + ' por mes en ' + canvas.id.split('-')[1]);
        chart.update();
    });
});
