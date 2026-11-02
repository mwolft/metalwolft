(() => {
    const select = document.getElementById('config-measure');
    if (!select) return;
    const panels = document.querySelectorAll('.admin-dashboard__config-measures');
    select.addEventListener('change', () => {
        panels.forEach((panel) => { panel.hidden = panel.dataset.measure !== select.value; });
    });
})();
