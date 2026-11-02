document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.querySelector("canvas[id^='salesChart']");
    const metrics = document.getElementById('sales-metrics');
    const mode = document.getElementById('sales-mode');
    const compare = document.getElementById('sales-compare');
    const summary = document.getElementById('sales-summary');
    const empty = document.getElementById('sales-empty');
    const realCharts = document.getElementById('sales-real-charts');
    if (!canvas || !metrics || !mode || !compare || !summary || !empty || !realCharts || typeof Chart === 'undefined') return;

    const labels = JSON.parse(canvas.dataset.labels || '[]');
    const selected = JSON.parse(canvas.dataset.selected || '{}');
    const previous = JSON.parse(canvas.dataset.previous || '{}');
    const summaries = JSON.parse(canvas.dataset.summaries || '{}');
    const selectedYear = Number(canvas.id.split('-')[1]);
    const previousYear = Number(canvas.dataset.previousYear);
    const definitions = {
        amount: { key: 'amounts', label: 'Importe registrado (€)', color: '#2665a8', money: true },
        orders: { key: 'counts', label: 'Pedidos registrados', color: '#ad6630', money: false },
        units: { key: 'units', label: 'Rejas vendidas', color: '#13806e', money: false },
        tickets: { key: 'tickets', label: 'Ticket medio (€)', color: '#8053a2', money: true }
    };
    const format = (value, money) => new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: money ? 2 : 0, maximumFractionDigits: money ? 2 : 0
    }).format(value) + (money ? ' €' : '');
    const monthLabels = labels.map((label, index) => {
        if (selected.future[index]) return label + ' (futuro)';
        return index + 1 === selected.current_month ? label + ' (en curso)' : label;
    });
    const original = (activity, key) => activity[definitions[key].key].map(
        (value, index) => selected.future[index] ? null : value
    );
    function reference(key) {
        const values = original(selected, key).concat(original(previous, key));
        return values.find(value => value !== null && value !== 0) ?? null;
    }
    function dataset(key, activity, year, normalized) {
        const definition = definitions[key];
        const raw = original(activity, key);
        const base = normalized ? reference(key) : null;
        return {
            label: definition.label + ' · ' + year,
            data: normalized ? raw.map(value => value === null || base === null ? null : value / Math.abs(base) * 100) : raw,
            rawValues: raw,
            metricKey: key,
            borderColor: definition.color,
            backgroundColor: definition.color,
            borderDash: year === previousYear ? [6, 4] : [],
            tension: 0,
            pointRadius: 3,
            pointHoverRadius: 5,
            spanGaps: false,
            fill: false
        };
    }
    const tooltip = {
        callbacks: {
            label: context => {
                const data = context.dataset;
                const value = data.rawValues[context.dataIndex];
                return data.label + ': ' + format(value, definitions[data.metricKey].money);
            }
        }
    };
    function options(normalized, key) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true, labels: { boxWidth: 18 } }, tooltip },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: normalized ? 0 : (key === 'orders' || key === 'units' ? 0 : undefined) },
                    title: { display: true, text: normalized ? 'Índice (base = 100)' : definitions[key].label }
                }
            }
        };
    }
    const trend = new Chart(canvas.getContext('2d'), {
        type: 'line', data: { labels: monthLabels, datasets: [] }, options: options(true, 'amount')
    });
    const realInstances = new Map();
    const realPanels = Array.from(realCharts.querySelectorAll('[data-metric]'));

    function update() {
        const chosen = Array.from(metrics.querySelectorAll('input:checked')).map(input => input.value);
        const isTrend = mode.value === 'trend';
        const hasMetrics = chosen.length > 0;
        const hasReference = chosen.some(key => reference(key) !== null);
        canvas.parentElement.hidden = !hasMetrics || !isTrend || !hasReference;
        realCharts.hidden = !hasMetrics || isTrend;
        empty.hidden = hasMetrics && (!isTrend || hasReference);
        empty.textContent = hasMetrics ? 'No hay valores distintos de cero para normalizar las tendencias seleccionadas.' :
            'Selecciona al menos un indicador para ver la evolución.';

        if (hasMetrics && isTrend && hasReference) {
            trend.data.datasets = chosen.flatMap(key => [
                dataset(key, selected, selectedYear, true),
                ...(compare.checked ? [dataset(key, previous, previousYear, true)] : [])
            ]);
            canvas.setAttribute('aria-label', 'Tendencias mensuales de ' + chosen.map(key => definitions[key].label).join(', '));
            trend.resize();
            trend.update();
        }
        for (const panel of realPanels) {
            const key = panel.dataset.metric;
            panel.hidden = !hasMetrics || isTrend || !chosen.includes(key);
            if (panel.hidden) continue;
            const plot = panel.querySelector('canvas');
            const datasets = [dataset(key, selected, selectedYear, false),
                ...(compare.checked ? [dataset(key, previous, previousYear, false)] : [])];
            if (!realInstances.has(key)) {
                realInstances.set(key, new Chart(plot.getContext('2d'), {
                    type: 'line', data: { labels: monthLabels, datasets }, options: options(false, key)
                }));
            } else {
                const chart = realInstances.get(key);
                chart.data.datasets = datasets;
                chart.resize();
                chart.update();
            }
            plot.setAttribute('aria-label', definitions[key].label + ' por mes en ' + selectedYear +
                (compare.checked ? ' y ' + previousYear : ''));
        }

        summary.hidden = !compare.checked || !hasMetrics;
        summary.replaceChildren();
        if (!summary.hidden) {
            const interval = canvas.dataset.partial === 'true' ? 'Hasta la fecha comparable' : 'Años completos';
            const heading = document.createElement('strong');
            heading.textContent = interval + ':';
            summary.appendChild(heading);
            for (const key of chosen) {
                const definition = definitions[key];
                const values = summaries[definition.key];
                const item = document.createElement('span');
                const percentage = values.percent === null ? 'Sin base comparable' :
                    new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 }).format(values.percent) + ' %';
                item.textContent = definition.label + ' · ' + selectedYear + ': ' + format(values.current, definition.money) +
                    ' · ' + previousYear + ': ' + format(values.previous, definition.money) +
                    ' · Variación: ' + format(values.delta, definition.money) + ' (' + percentage + ')';
                summary.appendChild(item);
            }
        }
    }
    metrics.addEventListener('change', update);
    mode.addEventListener('change', update);
    compare.addEventListener('change', update);
    update();
});
