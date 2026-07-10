import { LegalPageLayout } from "@/components/legal/LegalPageLayout";
import { buildLegalRelatedLinks } from "@/lib/legal";
import { buildMetadata } from "@/lib/metadata";

const PATH = "/politica-cookies";

export const metadata = buildMetadata({
  title: "Política de cookies | MetalWolft",
  description:
    "Consulta qué cookies puede utilizar MetalWolft, para qué sirven y cómo puedes gestionar tus preferencias de navegación.",
  path: PATH
});

export default function CookiesPolicyPage() {
  return (
    <LegalPageLayout
      path={PATH}
      title="Política de cookies"
      eyebrow="Información legal"
      description="Este sitio puede utilizar cookies para mejorar la experiencia de navegación, recordar preferencias y comprender mejor cómo se usa la web. Aquí resumimos qué son, qué tipos pueden emplearse y cómo gestionarlas."
      summaryTitle="Puntos principales sobre las cookies"
      summaryItems={[
        "Qué son las cookies y cómo ayudan al funcionamiento del sitio.",
        "Tipos de cookies relacionadas con funcionalidad, análisis y personalización.",
        "Opciones para gestionar o desactivar cookies desde el navegador.",
        "Cómo se publican futuras actualizaciones de esta política."
      ]}
      relatedLinks={buildLegalRelatedLinks(PATH)}
    >
      <section className="mw-section">
        <h2>Qué son las cookies</h2>
        <p>
          Las cookies son pequeños archivos de texto que se almacenan en tu
          dispositivo al visitar determinados sitios web. Su función es recordar
          información útil para la navegación, como preferencias, sesiones o
          datos agregados sobre el uso del sitio.
        </p>
      </section>

      <section className="mw-section">
        <h2>Tipos de cookies que pueden utilizarse</h2>
        <ul className="mw-list">
          <li>
            <strong>Cookies esenciales:</strong> necesarias para funciones
            básicas del sitio y para mantener determinados procesos de navegación.
          </li>
          <li>
            <strong>Cookies de rendimiento:</strong> ayudan a entender cómo se
            utiliza la web de forma agregada para mejorar contenidos y estructura.
          </li>
          <li>
            <strong>Cookies de funcionalidad:</strong> recuerdan ciertas
            preferencias para ofrecer una experiencia más cómoda.
          </li>
          <li>
            <strong>Cookies de publicidad o medición:</strong> pueden utilizarse
            para mostrar mensajes más relevantes y evaluar campañas.
          </li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Cómo gestionar las cookies</h2>
        <p>
          Puedes revisar, limitar o eliminar cookies desde la configuración de tu
          navegador. Ten en cuenta que desactivar determinadas cookies puede
          afectar al funcionamiento de algunas partes de la web o reducir la
          personalización de la experiencia.
        </p>
      </section>

      <section className="mw-section">
        <h2>Cambios en la política de cookies</h2>
        <p>
          Esta política puede actualizarse cuando haya cambios legales,
          funcionales o de servicio. Publicaremos las revisiones en esta página
          para que puedas consultarlas cuando lo necesites.
        </p>
      </section>
    </LegalPageLayout>
  );
}
