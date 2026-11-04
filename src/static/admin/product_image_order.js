(() => {
  const list = document.getElementById('product-image-order');
  if (!list) return;
  let dragging = null;
  const refresh = () => {
    [...list.children].forEach((item, index) => {
      item.querySelector('.mw-image-order__position').textContent = String(index + 1);
      item.querySelector('.mw-image-order__label').textContent = index === 0 ? 'Imagen principal' : 'Imagen adicional';
      item.querySelector('.mw-image-order__card').textContent = index < 4 ? 'ProductCard' : 'Solo ficha';
      item.querySelector('[data-move="up"]').disabled = index === 0;
      item.querySelector('[data-move="down"]').disabled = index === list.children.length - 1;
    });
  };
  list.addEventListener('click', (event) => {
    const button = event.target.closest('[data-move]');
    if (!button) return;
    const item = button.closest('li');
    if (button.dataset.move === 'up' && item.previousElementSibling) list.insertBefore(item, item.previousElementSibling);
    if (button.dataset.move === 'down' && item.nextElementSibling) list.insertBefore(item.nextElementSibling, item);
    refresh();
  });
  list.addEventListener('dragstart', (event) => {
    dragging = event.target.closest('li');
    if (!dragging) return;
    event.dataTransfer.effectAllowed = 'move';
    dragging.classList.add('is-dragging');
  });
  list.addEventListener('dragover', (event) => {
    const target = event.target.closest('li');
    if (!dragging || !target || target === dragging) return;
    event.preventDefault();
    target.classList.add('is-over');
  });
  list.addEventListener('dragleave', (event) => {
    const target = event.target.closest('li');
    if (target) target.classList.remove('is-over');
  });
  list.addEventListener('drop', (event) => {
    const target = event.target.closest('li');
    if (!dragging || !target || target === dragging) return;
    event.preventDefault();
    const before = target.compareDocumentPosition(dragging) & Node.DOCUMENT_POSITION_FOLLOWING;
    list.insertBefore(dragging, before ? target : target.nextSibling);
    target.classList.remove('is-over');
    refresh();
  });
  list.addEventListener('dragend', () => {
    [...list.children].forEach((item) => item.classList.remove('is-dragging', 'is-over'));
    dragging = null;
  });
  refresh();
})();
