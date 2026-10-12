import Link from "next/link";
import type { Metadata } from "next";
import { LoginForm } from "@/components/auth/LoginForm";
import { GoogleIdentityButton } from "@/components/auth/GoogleIdentityButton";
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

        <section className="mw-auth-layout" aria-label="Acceso a tu cuenta">
          <div className="mw-auth-card">
            <h1 className="mw-title mw-title--compact">Iniciar sesión</h1>
            <p className="mw-lead">
              Accede a tu cuenta para consultar tus pedidos y realizar nuevas compras
            </p>
            <GoogleIdentityButton mode="login" nextPath={nextPath} />
            <div className="mw-auth-divider"><span>o con tu correo</span></div>
            <LoginForm nextPath={nextPath} />
            <p className="mw-auth-footnote">
              ¿No tienes cuenta? <Link href={buildRegisterHref(nextPath)}>Crear cuenta</Link>.
            </p>
          </div>
        </section>
      </PageContainer>
    </div>
  );
}
