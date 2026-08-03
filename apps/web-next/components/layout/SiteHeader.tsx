import Image from "next/image";
import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";
import { SiteHeaderNavigation } from "@/components/layout/SiteHeaderNavigation";

export function SiteHeader() {
  return (
    <header className="mw-header">
      <PageContainer>
        <div className="mw-header__inner">
          <Link className="mw-brand" href="/" aria-label="MetalWolft, inicio">
            <Image
              className="mw-brand__icon"
              src="/metalwolft-isotipo.webp"
              alt=""
              width={48}
              height={48}
            />
            <span className="mw-brand__text">
              <span className="mw-brand__name">
                Metal<span>Wolft</span>
              </span>
              <span className="mw-brand__tagline">Rejas para ventanas a medida</span>
            </span>
          </Link>
          <SiteHeaderNavigation />
        </div>
      </PageContainer>
    </header>
  );
}
