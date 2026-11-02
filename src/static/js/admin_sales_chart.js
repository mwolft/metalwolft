document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.querySelector("canvas[id^='salesChart']");
    const metric = document.getElementById('sales-metric');
    const compare = document.getElementById('sales-compare');
    const summary = document.getElementById('sales-summary');
    if (!canvas || !metric || !compare || !summary || typeof Chart === 'undefined') return;

    const labels = JSON.parse(canvas.dataset.labels || '[]');
    const selected = JSON.parse(canvas.dataset.selected || '{}');
    const previous = JSON.parse(canvas.dataset.previous || '{}');
    const summaries = JSON.parse(canvas.dataset.summaries || '{}');
    const selectedYear = Number(canvas.id.split('-')[1]);
    const previousYear = Number(canvas.dataset.previousYear);
    const metricLabels = {
        amount: 'Importe registrado (€)', orders: 'Pedidos registrados',
        units: 'Rejas vendidas', tickets: 'Ticket medio (€)'
    };
    const metricKeys = { amount: 'amounts', orders: 'counts', units: 'units', tickets: 'tickets' };
    const format = (value, key) => new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: key === 'amount' || key === 'tickets' ? 2 : 0,
        maximumFractionDigits: key === 'amount' || key === 'tickets' ? 2 : 0
    }).format(value);
    const series = (activity, key) => activity[metricKeys[key]].map(
        (value, index) => selected.future[index] ? null : value
    );
    const chart = new Chart(canvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels.map((label, index) => {
                if (selected.future[index]) return label + ' (futuro)';
                return index + 1 === selected.current_month ? label + ' (en curso)' : label;
            }),
            datasets: [{
                label: String(selectedYear),
                data: series(selected, 'amount'),
                backgroundColor: '#337ab7',
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

    function updateChart() {
        const key = metric.value;
        const label = metricLabels[key];
        chart.data.datasets[0].data = series(selected, key);
        chart.data.datasets = chart.data.datasets.slice(0, 1);
        if (compare.checked) {
            chart.data.datasets.push({
                label: String(previousYear),
                data: series(previous, key),
                backgroundColor: '#b52538',
                borderRadius: 3
            });
        }
        chart.options.plugins.legend.display = compare.checked;
        chart.options.scales.y.title.text = label;
        chart.options.scales.y.ticks.precision = key === 'orders' || key === 'units' ? 0 : undefined;
        canvas.setAttribute('aria-label', label + ' por mes en ' + selectedYear +
            (compare.checked ? ' y ' + previousYear : ''));
        const values = summaries[metricKeys[key]];
        summary.hidden = !compare.checked;
        if (compare.checked) {
            const unit = key === 'amount' || key === 'tickets' ? ' €' : '';
            const interval = canvas.dataset.partial === 'true' ? 'Hasta la fecha comparable' : 'Años completos';
            const percentage = values.percent === null ? 'Sin base comparable' : format(values.percent, 'tickets') + ' %';
            summary.textContent = interval + ' · ' + selectedYear + ': ' + format(values.current, key) + unit +
                ' · ' + previousYear + ': ' + format(values.previous, key) + unit +
                ' · Variación: ' + format(values.delta, key) + unit + ' (' + percentage + ')';
        } else {
            summary.textContent = '';
        }
        chart.update();
    }
    metric.addEventListener('change', updateChart);
    compare.addEventListener('change', updateChart);
});
