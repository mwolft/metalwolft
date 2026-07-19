import Link from "next/link";
import type { Metadata } from "next";
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm";
import { PageContainer } from "@/components/layout/PageContainer";

type ResetPasswordPageProps = {
  searchParams?: {
    token?: string | string[];
  };
};

export const metadata: Metadata = {
  title: "Restablecer contraseña | MetalWolft",
  description: "Define una nueva contraseña para volver a acceder a tu cuenta MetalWolft.",
  alternates: {
    canonical: "/reset-password"
  },
  robots: {
    index: false,
    follow: false
  }
};

function getToken(searchParams?: ResetPasswordPageProps["searchParams"]) {
  const rawToken = searchParams?.token;
  const token = Array.isArray(rawToken) ? rawToken[0] : rawToken;
  return token?.trim() || undefined;
}

export default function ResetPasswordPage({ searchParams }: ResetPasswordPageProps) {
  const token = getToken(searchParams);

  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <Link href="/login">Iniciar sesión</Link>
          <span>/</span>
          <span aria-current="page">Restablecer contraseña</span>
        </nav>

        <section className="mw-auth-layout">
          <div className="mw-auth-card">
            <p className="mw-eyebrow">Cuenta MetalWolft</p>
            <h1 className="mw-title mw-title--compact">Restablece tu contraseña</h1>
            <p className="mw-lead">
              Introduce una nueva contraseña para volver a entrar. Flask comprobará
              que el enlace sea válido y no haya caducado.
            </p>
            <ResetPasswordForm token={token} />
          </div>

          <aside className="mw-auth-aside" aria-label="Información del enlace de recuperación">
            <p className="mw-note">Enlace temporal</p>
            <h2>El token no se guarda en el navegador</h2>
            <ul className="mw-list">
              <li>El enlace llega desde el email de recuperación.</li>
              <li>El backend valida el token y actualiza la contraseña.</li>
              <li>Si el enlace ha caducado, solicita uno nuevo.</li>
            </ul>
          </aside>
        </section>
      </PageContainer>
    </div>
  );
}
