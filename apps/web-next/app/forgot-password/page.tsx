import Link from "next/link";
import type { Metadata } from "next";
import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm";
import { PageContainer } from "@/components/layout/PageContainer";

export const metadata: Metadata = {
  title: "Recuperar contraseña | MetalWolft",
  description: "Solicita un enlace seguro para restablecer la contraseña de tu cuenta MetalWolft.",
  alternates: {
    canonical: "/forgot-password"
  },
  robots: {
    index: false,
    follow: true
  }
};

export default function ForgotPasswordPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <Link href="/login">Iniciar sesión</Link>
          <span>/</span>
          <span aria-current="page">Recuperar contraseña</span>
        </nav>

        <section className="mw-auth-layout">
          <div className="mw-auth-card">
            <p className="mw-eyebrow">Cuenta MetalWolft</p>
            <h1 className="mw-title mw-title--compact">Recupera tu acceso</h1>
            <p className="mw-lead">
              Te enviaremos un correo para que puedas restablecer tu contraseña
              de forma segura. El enlace caduca a los 15 minutos.
            </p>
            <ForgotPasswordForm />
          </div>

          <aside className="mw-auth-aside" aria-label="Ayuda para recuperar el acceso">
            <p className="mw-note">Acceso seguro</p>
            <h2>Usamos el flujo existente de MetalWolft</h2>
            <ul className="mw-list">
              <li>Flask genera y valida el token de recuperación.</li>
              <li>Next no guarda el token ni decide si es válido.</li>
              <li>Si el correo existe, recibirás las instrucciones por email.</li>
            </ul>
          </aside>
        </section>
      </PageContainer>
    </div>
  );
}
