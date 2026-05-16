import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";

export function SiteHeader() {
  return (
    <header className="mw-header">
      <PageContainer>
        <div className="mw-header__inner">
          <Link className="mw-brand" href="/">
            Metal<span>Wolft</span>
          </Link>
          <nav className="mw-nav" aria-label="Navegación principal">
            <Link href="/">Inicio</Link>
            <Link href="/rejas-para-ventanas">Rejas para ventanas</Link>
          </nav>
        </div>
      </PageContainer>
    </header>
  );
}
