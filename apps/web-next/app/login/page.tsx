import Link from "next/link";
import type { Metadata } from "next";
import { LoginForm } from "@/components/auth/LoginForm";
import { PageContainer } from "@/components/layout/PageContainer";

type LoginSearchParams = {
  next?: string | string[];
};

type LoginPageProps = {
  searchParams?: Promise<LoginSearchParams>;
};

export const metadata: Metadata = {
  title: "Iniciar sesión | MetalWolft",
  description: "Accede a tu cuenta de MetalWolft para continuar con tu compra de rejas para ventanas a medida.",
  alternates: {
    canonical: "/login"
  },
  robots: {
    index: false,
    follow: true
  }
};

function getNextPath(searchParams?: LoginSearchParams) {
  const rawNext = searchParams?.next;
  return Array.isArray(rawNext) ? rawNext[0] : rawNext;
}

function buildRegisterHref(nextPath?: string) {
  return nextPath ? `/registro?next=${encodeURIComponent(nextPath)}` : "/registro";
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const nextPath = getNextPath(resolvedSearchParams);

  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">Iniciar sesión</span>
        </nav>

        <section className="mw-auth-layout">
          <div className="mw-auth-card">
            <p className="mw-eyebrow">Cuenta MetalWolft</p>
            <h1 className="mw-title mw-title--compact">Iniciar sesión</h1>
            <p className="mw-lead">
              Accede para continuar tu sesión en MetalWolft y seguir preparando
              tu compra de rejas para ventanas a medida.
            </p>
            <LoginForm nextPath={nextPath} />
            <p className="mw-auth-footnote">
              ¿No tienes cuenta? <Link href={buildRegisterHref(nextPath)}>Crear cuenta</Link>.
            </p>
          </div>

          <aside className="mw-auth-aside" aria-label="Información de acceso">
            <p className="mw-note">Compra segura</p>
            <h2>Tu sesión conecta con el acceso existente</h2>
            <ul className="mw-list">
              <li>Usamos el mismo acceso que ya existe en MetalWolft.</li>
              <li>El token se guarda en tu navegador como en la web actual.</li>
              <li>La contraseña nunca se almacena en el frontend.</li>
            </ul>
            <p className="mw-auth-footnote">
              Tras iniciar sesión volverás a la página solicitada si la ruta es segura.
            </p>
          </aside>
        </section>
      </PageContainer>
    </div>
  );
}
