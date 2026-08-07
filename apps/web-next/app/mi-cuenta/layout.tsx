import Link from "next/link";
import type { ReactNode } from "react";
import { AccountShell } from "@/components/account/AccountShell";
import { PageContainer } from "@/components/layout/PageContainer";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mw-page">
      <PageContainer>
        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">Mi cuenta</span>
        </nav>

        <AccountShell>{children}</AccountShell>
      </PageContainer>
    </div>
  );
}
