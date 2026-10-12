import Link from "next/link";
import type { Metadata } from "next";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { GoogleIdentityButton } from "@/components/auth/GoogleIdentityButton";
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

        <section className="mw-auth-layout" aria-label="Crear cuenta">
          <div className="mw-auth-card">
            <h1 className="mw-title mw-title--compact">Crear cuenta</h1>
            <p className="mw-lead">
              Crea tu cuenta para consultar tus pedidos y comprar con más facilidad.
            </p>
            <GoogleIdentityButton mode="login" nextPath={nextPath} />
            <div className="mw-auth-divider"><span>o con tu correo</span></div>
            <RegisterForm nextPath={nextPath} />
            <p className="mw-auth-footnote">
              ¿Ya tienes cuenta? <Link href={buildLoginHref(nextPath)}>Inicia sesión</Link>.
            </p>
          </div>
        </section>
      </PageContainer>
    </div>
  );
}
