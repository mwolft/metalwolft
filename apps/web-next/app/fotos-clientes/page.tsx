import type { Metadata } from "next";
import { PageContainer } from "@/components/layout/PageContainer";
import { CustomerPhotoForm } from "@/components/contact/CustomerPhotoForm";

export const metadata: Metadata = {
  title: "Comparte tus fotografías | MetalWolft",
  robots: { index: false, follow: false, noarchive: true }
};

export default function CustomerPhotoPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <section className="mw-hero mw-hero--compact">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">MetalWolft</p>
            <h1 className="mw-title mw-title--compact">Comparte tus rejas instaladas</h1>
            <p className="mw-lead">Nos ayudará ver cómo han quedado. No necesitas crear una cuenta.</p>
          </div>
        </section>
        <section className="mw-section" aria-labelledby="photo-form-title">
          <h2 id="photo-form-title">Tus fotografías</h2>
          <CustomerPhotoForm />
        </section>
      </PageContainer>
    </div>
  );
}
