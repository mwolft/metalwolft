export function HeaderCartLink() {
  return (
    <a className="mw-header-cart" href="/cart" aria-label="Ver carrito" title="Ver carrito">
      <svg className="mw-header-cart__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path
          d="M3.5 5h2.1l1.6 8.1a1 1 0 0 0 1 .8h8.5a1 1 0 0 0 1-.7l1.6-5.7H7.1"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="10" cy="18.3" r="1.3" fill="currentColor" />
        <circle cx="17" cy="18.3" r="1.3" fill="currentColor" />
      </svg>
    </a>
  );
}
