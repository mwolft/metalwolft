"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type PropsWithChildren } from "react";
import { useAuthSession } from "@/hooks/useAuthSession";

const accountLinks = [
  { href: "/mi-cuenta", label: "Resumen" },
  { href: "/mi-cuenta/pedidos", label: "Mis pedidos" }
];

function loginHref(nextPath: string) {
  return `/login?next=${encodeURIComponent(nextPath)}`;
}

function isCurrentPath(pathname: string, href: string) {
  if (href === "/mi-cuenta") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AccountShell({ children }: PropsWithChildren) {
  const pathname = usePathname() || "/mi-cuenta";
  const router = useRouter();
  const { isAuthenticated, isReady, logout } = useAuthSession();

  useEffect(() => {
    if (isReady && !isAuthenticated) {
      router.replace(loginHref(pathname));
    }
  }, [isAuthenticated, isReady, pathname, router]);

  const handleLogout = () => {
    logout();
    router.replace(loginHref("/mi-cuenta"));
  };

  if (!isReady) {
    return (
      <section className="mw-account-state" aria-live="polite">
        <h1>Mi cuenta</h1>
        <p>Comprobando tu sesión...</p>
      </section>
    );
  }

  if (!isAuthenticated) {
    return (
      <section className="mw-account-state" aria-live="polite">
        <h1>Mi cuenta</h1>
        <p>Para acceder a tu área privada necesitas iniciar sesión.</p>
        <Link className="mw-button mw-button--primary" href={loginHref(pathname)}>
          Iniciar sesión
        </Link>
      </section>
    );
  }

  return (
    <section className="mw-account-area" aria-labelledby="account-title">
      <div className="mw-account-area__header">
        <p className="mw-eyebrow">Área privada</p>
        <h1 className="mw-title mw-title--compact" id="account-title">
          Mi cuenta
        </h1>
        <p className="mw-lead">
          Consulta tus pedidos y vuelve al catálogo cuando quieras preparar una nueva compra.
        </p>
      </div>

      <div className="mw-account-shell">
        <aside className="mw-account-sidebar" aria-label="Navegación de cuenta">
          <nav className="mw-account-nav">
            {accountLinks.map((link) => {
              const isCurrent = isCurrentPath(pathname, link.href);

              return (
                <Link
                  aria-current={isCurrent ? "page" : undefined}
                  className="mw-account-nav__link"
                  href={link.href}
                  key={link.href}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
          <button className="mw-account-logout" type="button" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </aside>

        <div className="mw-account-content">{children}</div>
      </div>
    </section>
  );
}
