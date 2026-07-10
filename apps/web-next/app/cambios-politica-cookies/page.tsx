import { LegalPageLayout } from "@/components/legal/LegalPageLayout";
import { buildLegalRelatedLinks } from "@/lib/legal";
import { buildMetadata } from "@/lib/metadata";

const PATH = "/cambios-politica-cookies";

export const metadata = buildMetadata({
  title: "Cambios en la política de cookies | MetalWolft",
  description:
    "Consulta cómo MetalWolft puede actualizar su política de cookies y dónde se publican los cambios relevantes para los usuarios.",
  path: PATH
});

export default function ChangesPolicyPage() {
  return (
    <LegalPageLayout
      path={PATH}
      title="Cambios en la política de cookies"
      eyebrow="Información legal"
      description="Podemos actualizar la política de cookies para reflejar cambios legales, funcionales o de servicio. En esta página indicamos cómo comunicamos esas revisiones y por qué conviene consultarla periódicamente."
      summaryTitle="Qué debes tener en cuenta"
      summaryItems={[
        "La política puede cambiar para adaptarse a normativa o mejoras del servicio.",
        "Las revisiones relevantes se publicarán en esta misma página.",
        "Conviene revisar esta información de forma periódica.",
        "Si tienes dudas, puedes contactarnos por nuestros canales habituales."
      ]}
      relatedLinks={buildLegalRelatedLinks(PATH)}
    >
      <section className="mw-section">
        <h2>Actualizaciones de la política</h2>
        <p>
          Nos reservamos el derecho de realizar cambios en la política de
          cookies cuando resulte necesario por motivos legales, técnicos o de
          funcionamiento del servicio. La versión actualizada se publicará en
          esta página para que puedas consultarla siempre que lo desees.
        </p>
      </section>

      <section className="mw-section">
        <h2>Cómo se comunicarán los cambios</h2>
        <p>
          Cuando una modificación afecte de forma relevante a la experiencia de
          navegación o al tratamiento de datos relacionado con cookies,
          procuraremos destacarla de forma visible en la web para que puedas
          revisarla con facilidad.
        </p>
      </section>

      <section className="mw-section">
        <h2>Revisión periódica</h2>
        <p>
          Te recomendamos consultar esta política de vez en cuando para conocer
          la versión vigente y comprender mejor cualquier ajuste realizado en el
          uso de cookies dentro del sitio.
        </p>
      </section>
    </LegalPageLayout>
  );
}
