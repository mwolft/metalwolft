document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('ads-monthly-chart');
    if (!canvas || typeof Chart === 'undefined') return;
    const read = key => JSON.parse(canvas.dataset[key] || '[]');
    const future = read('future');
    const partial = read('partial');
    const labels = read('labels').map((month, index) => month + (future[index] ? ' (futuro)' :
        partial[index] ? ' (cobertura parcial)' : ''));
    const euro = value => new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: 2, maximumFractionDigits: 2
    }).format(value) + ' €';
    new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: { labels, datasets: [
            { label: 'Gasto Google Ads (€)', data: read('costs'), yAxisID: 'yAds',
                borderColor: '#b52538', backgroundColor: '#b52538', tension: 0, spanGaps: false },
            { label: 'Importe de pedidos registrados (€)', data: read('sales'), yAxisID: 'ySales',
                borderColor: '#2665a8', backgroundColor: '#2665a8', tension: 0, spanGaps: false },
            { label: 'Pedidos registrados', data: read('orders'), yAxisID: 'yOrders',
                borderColor: '#13806e', backgroundColor: '#13806e', tension: 0, spanGaps: false }
        ].map(dataset => ({ ...dataset, pointRadius: 3, pointHoverRadius: 5, fill: false })) },
        options: { responsive: true, maintainAspectRatio: false,
            plugins: { tooltip: { callbacks: { label: context => context.dataset.label + ': ' +
                (context.dataset.yAxisID === 'yOrders' ? context.parsed.y : euro(context.parsed.y)) } } },
            scales: {
                yAds: { type: 'linear', position: 'left', beginAtZero: true,
                    title: { display: true, text: 'Gasto (€)' } },
                ySales: { type: 'linear', position: 'right', beginAtZero: true,
                    title: { display: true, text: 'Pedidos (€)' }, grid: { drawOnChartArea: false } },
                yOrders: { type: 'linear', position: 'right', offset: true, beginAtZero: true,
                    ticks: { precision: 0 }, title: { display: true, text: 'N.º pedidos' },
                    grid: { drawOnChartArea: false } }
            }
        }
    });
});
