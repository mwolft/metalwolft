import Link from "next/link";
import { PageContainer } from "@/components/layout/PageContainer";

export function SiteFooter() {
  return (
    <footer className="mw-footer">
      <PageContainer>
        <div className="mw-footer__inner">
          <div className="mw-footer__links">
            <Link href="/">Inicio</Link>
            <Link href="/rejas-para-ventanas">Rejas para ventanas</Link>
            <Link href="/blogs">Blog</Link>
          </div>
        </div>
      </PageContainer>
    </footer>
  );
}
