import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { SiteHeaderNavigation } from "@/components/layout/SiteHeaderNavigation";

export function SiteHeader() {
  return (
    <header className="mw-header">
      <PageContainer>
        <div className="mw-header__inner">
          <Link className="mw-brand" href="/" aria-label="MetalWolft, inicio">
            <span className="mw-brand__name">
              Metal<span>Wolft</span>
            </span>
            <span className="mw-brand__tagline">Rejas para ventanas a medida</span>
          </Link>
          <SiteHeaderNavigation />
        </div>
      </PageContainer>
    </header>
  );
}
