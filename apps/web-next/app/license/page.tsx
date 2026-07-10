import Link from "next/link";
import { LegalPageLayout } from "@/components/legal/LegalPageLayout";
import { buildLegalRelatedLinks } from "@/lib/legal";
import { buildMetadata } from "@/lib/metadata";

const PATH = "/license";

export const metadata = buildMetadata({
  title: "Licencia de imágenes | MetalWolft",
  description:
    "Consulta las condiciones de uso de las imágenes publicadas por MetalWolft y cómo solicitar autorización para usos comerciales.",
  path: PATH
});

export default function LicensePage() {
  return (
    <LegalPageLayout
      path={PATH}
      title="Licencia de imágenes"
      eyebrow="Información legal"
      description="Las imágenes publicadas en este sitio están protegidas por derechos de autor. Aquí resumimos las condiciones generales de uso personal, las limitaciones para uso comercial y cómo solicitar autorización cuando sea necesaria."
      summaryTitle="Condiciones generales de uso"
      summaryItems={[
        "Las imágenes están protegidas por derechos de autor.",
        "El uso comercial requiere autorización o licencia específica.",
        "No se permite modificar imágenes sin permiso expreso.",
        "Si necesitas aclaraciones, puedes escribirnos directamente."
      ]}
      relatedLinks={buildLegalRelatedLinks(PATH)}
    >
      <section className="mw-section">
        <h2>Uso personal</h2>
        <p>
          Las imágenes del sitio pueden utilizarse con fines personales siempre
          que se respeten sus derechos de autor y no se altere el contexto de
          uso ni se vulnere la titularidad de los contenidos.
        </p>
      </section>

      <section className="mw-section">
        <h2>Uso comercial</h2>
        <p>
          Para cualquier uso comercial, promocional o redistribución fuera del
          ámbito estrictamente personal, es necesario contar con autorización
          previa o con una licencia específica. Si necesitas este permiso, puedes
          solicitarlo desde la página de <Link href="/contact">contacto</Link>.
        </p>
      </section>

      <section className="mw-section">
        <h2>Modificación y atribución</h2>
        <p>
          No está permitido modificar las imágenes sin autorización expresa.
          Cuando proceda utilizar una imagen con permiso, deberá respetarse la
          atribución y las condiciones concretas que acompañen a ese uso.
        </p>
      </section>

      <section className="mw-section">
        <h2>Solicitud de autorización</h2>
        <p>
          Si tienes dudas sobre el uso permitido de una imagen concreta o quieres
          solicitar autorización para un proyecto, escríbenos con el detalle del
          uso previsto y revisaremos tu solicitud.
        </p>
      </section>
    </LegalPageLayout>
  );
}
