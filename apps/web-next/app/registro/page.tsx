import Link from "next/link";
import type { Metadata } from "next";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { PageContainer } from "@/components/layout/PageContainer";

type RegisterSearchParams = {
  next?: string | string[];
};

type RegisterPageProps = {
  searchParams?: Promise<RegisterSearchParams>;
};

export const metadata: Metadata = {
  title: "Crear cuenta | MetalWolft",
  description: "Crea tu cuenta de MetalWolft para guardar tu carrito y continuar con tu compra.",
  alternates: {
    canonical: "/registro"
  },
  robots: {
    index: false,
    follow: true
  }
};

function getNextPath(searchParams?: RegisterSearchParams) {
  const rawNext = searchParams?.next;
  return Array.isArray(rawNext) ? rawNext[0] : rawNext;
}

function buildLoginHref(nextPath?: string) {
  return nextPath ? `/login?next=${encodeURIComponent(nextPath)}` : "/login";
}

export default async function RegisterPage({ searchParams }: RegisterPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const nextPath = getNextPath(resolvedSearchParams);

  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">Crear cuenta</span>
        </nav>

        <section className="mw-auth-layout">
          <div className="mw-auth-card">
            <p className="mw-eyebrow">Cuenta MetalWolft</p>
            <h1 className="mw-title mw-title--compact">Crear cuenta</h1>
            <p className="mw-lead">
              Regístrate para guardar tu sesión, añadir productos al carrito y continuar
              con la compra de tus rejas para ventanas a medida.
            </p>
            <RegisterForm nextPath={nextPath} />
            <p className="mw-auth-footnote">
              ¿Ya tienes cuenta? <Link href={buildLoginHref(nextPath)}>Inicia sesión</Link>.
            </p>
          </div>

          <aside className="mw-auth-aside" aria-label="Ventajas de crear cuenta">
            <p className="mw-note">Compra más cómoda</p>
            <h2>Tu cuenta usa el acceso existente de MetalWolft</h2>
            <ul className="mw-list">
              <li>Podrás volver al carrito y continuar el pedido.</li>
              <li>El backend crea la sesión con el mismo contrato que la web actual.</li>
              <li>La contraseña nunca se almacena en el frontend.</li>
            </ul>
            <p className="mw-auth-footnote">
              Tras crear la cuenta volverás a la página solicitada si la ruta es segura.
            </p>
          </aside>
        </section>
      </PageContainer>
    </div>
  );
}
