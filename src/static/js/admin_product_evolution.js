document.addEventListener('DOMContentLoaded', () => {
    const root = document.getElementById('product-evolution');
    if (!root || typeof Chart === 'undefined') return;
    const year = document.getElementById('product-year');
    const metric = document.getElementById('product-metric');
    const options = document.getElementById('product-options');
    const message = document.getElementById('product-message');
    const plot = document.getElementById('product-chart');
    const colors = ['#2665a8', '#b52538', '#13806e', '#8053a2', '#ad6630'];
    let chart;
    let data;
    let pending;

    const chosen = () => Array.from(options.querySelectorAll('input:checked')).map(input => Number(input.value));
    const format = (value) => new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: metric.value === 'amount' ? 2 : 0,
        maximumFractionDigits: metric.value === 'amount' ? 2 : 0
    }).format(value) + (metric.value === 'amount' ? ' €' : '');

    function draw() {
        const ids = chosen();
        const hasSales = data.options.length > 0;
        plot.hidden = !hasSales || ids.length === 0;
        message.hidden = !plot.hidden;
        message.textContent = hasSales ? 'Selecciona al menos un producto.' : 'No hay rejas físicas registradas en este año.';
        if (plot.hidden) return;
        const labels = data.months.map((month, index) => data.future[index] ? month + ' (futuro)' :
            index + 1 === data.current_month ? month + ' (en curso)' : month);
        const datasets = ids.map((id, index) => ({
            label: data.options.find(item => item.id === id).name,
            data: data.series[id][metric.value],
            borderColor: colors[index], backgroundColor: colors[index],
            tension: 0, pointRadius: 3, pointHoverRadius: 5, spanGaps: false, fill: false
        }));
        if (!chart) {
            chart = new Chart(plot.querySelector('canvas').getContext('2d'), {
                type: 'line', data: { labels, datasets },
                options: { responsive: true, maintainAspectRatio: false,
                    plugins: { tooltip: { callbacks: { label: context =>
                        context.dataset.label + ': ' + format(context.parsed.y) } } },
                    scales: { y: { beginAtZero: true, ticks: { precision: metric.value === 'amount' ? undefined : 0 } } } }
            });
        } else {
            chart.data.labels = labels;
            chart.data.datasets = datasets;
            chart.options.scales.y.ticks.precision = metric.value === 'amount' ? undefined : 0;
            chart.resize();
            chart.update();
        }
    }

    async function load(reset) {
        if (pending) pending.abort();
        pending = new AbortController();
        const url = new URL(root.dataset.url, window.location.href);
        url.searchParams.set('year', year.value);
        if (!reset) chosen().forEach(id => url.searchParams.append('product_id', id));
        message.hidden = false;
        message.textContent = 'Cargando ventas por producto…';
        try {
            const response = await fetch(url, { credentials: 'same-origin', signal: pending.signal });
            if (!response.ok) throw new Error('No se pudieron cargar las ventas por producto.');
            data = await response.json();
            options.replaceChildren();
            data.options.forEach(item => {
                const label = document.createElement('label');
                const input = document.createElement('input');
                input.type = 'checkbox';
                input.value = item.id;
                input.checked = data.selected.includes(item.id);
                label.append(input, ' ' + item.name);
                options.append(label);
            });
            draw();
        } catch (error) {
            if (error.name === 'AbortError') return;
            plot.hidden = true;
            message.hidden = false;
            message.textContent = 'No se pudieron cargar las ventas por producto.';
        }
    }

    options.addEventListener('change', event => {
        if (event.target.checked && chosen().length > 5) {
            event.target.checked = false;
            message.hidden = false;
            message.textContent = 'Puedes comparar un máximo de cinco productos.';
            return;
        }
        if (chosen().length) load(false);
        else draw();
    });
    year.addEventListener('change', () => load(true));
    metric.addEventListener('change', draw);
    load(true);
});
