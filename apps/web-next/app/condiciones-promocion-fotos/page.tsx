import type { Metadata } from "next";
import Link from "next/link";
import { LegalPageLayout } from "@/components/legal/LegalPageLayout";
import { buildLegalRelatedLinks } from "@/lib/legal";
import { buildMetadata } from "@/lib/metadata";

const PATH = "/condiciones-promocion-fotos";

export const metadata: Metadata = {
  ...buildMetadata({
    title: "Condiciones de la promoción de fotografías | MetalWolft",
    description: "Borrador de las condiciones de la promoción de fotografías de rejas instaladas de MetalWolft.",
    path: PATH
  }),
  robots: { index: false, follow: false, noarchive: true }
};

export default function CustomerPhotoPromotionTermsPage() {
  return (
    <LegalPageLayout
      path={PATH}
      title="Condiciones de la promoción de fotografías"
      eyebrow="Información de la promoción"
      description="Condiciones comerciales aprobadas para la invitación a compartir fotografías de rejas instaladas. Borrador pendiente de revisión jurídica y activación."
      summaryTitle="Antes de participar"
      summaryItems={[
        "La participación es voluntaria y requiere una invitación individual tras la entrega.",
        "Basta fotografiar una reja instalada: una foto frontal y otra lateral o en perspectiva.",
        "El incentivo previsto es de 20 € una sola vez por pedido aprobado, no por fotografía.",
        "Hay 30 días desde la entrega para participar y la revisión se comunicará en un máximo de 7 días naturales.",
        "La autorización comercial se solicita por separado; el reembolso no es automático."
      ]}
      relatedLinks={buildLegalRelatedLinks(PATH)}
    >
      <section className="mw-section">
        <h2>Borrador pendiente de aprobación</h2>
        <p>
          Esta página documenta las condiciones comerciales previstas, pero todavía no constituye
          una promoción vigente ni genera derecho a un reembolso. Antes de activar la modalidad
          incentivada deben cerrarse los aspectos jurídicos y operativos indicados abajo, aprobarse
          el texto definitivo y publicarse. Las invitaciones de simulación se identifican
          expresamente como <strong>SIMULACIÓN — SIN REEMBOLSO</strong>.
        </p>
      </section>

      <section className="mw-section">
        <h2>Organizador y participación</h2>
        <p>
          MetalWolft prepara esta iniciativa para recibir fotografías reales de sus rejas una vez
          instaladas. La participación es voluntaria y solo mediante una invitación individual
          tras la entrega de un pedido físico elegible. No es una convocatoria abierta. Si el pedido
          incluye varias rejas, basta con fotografiar una sola.
        </p>
      </section>

      <section className="mw-section">
        <h2>Fotografías y revisión</h2>
        <p>
          Se requieren dos fotografías de la misma reja instalada: una frontal y otra lateral o en
          perspectiva. Puedes añadir hasta tres imágenes más de detalle u otras vistas. La reja debe
          aparecer completa, aproximadamente centrada, nítida y bien iluminada. Las fotos hechas
          con móvil son válidas; no se exige calidad profesional. Evita personas identificables,
          matrículas e información privada.
        </p>
        <p>
          MetalWolft revisará si las imágenes muestran la reja instalada, cumplen las dos
          perspectivas y tienen nitidez, iluminación y encuadre suficientes para apreciarla.
          Podrán rechazarse imágenes del producto sin instalar, borrosas, oscuras, incompletas,
          duplicadas o que incluyan datos de terceros sin autorización adecuada. Si es posible
          corregirlas, MetalWolft podrá pedir fotografías adicionales o corregidas por correo.
          El formulario de invitación no permite un segundo envío automático después de presentarlo.
        </p>
      </section>

      <section className="mw-section">
        <h2>Incentivo previsto y reembolso</h2>
        <p>
          La modalidad incentivada prevé <strong>20 € una sola vez por pedido aprobado</strong>,
          no por fotografía. La recompensa está destinada a fotografías que MetalWolft pueda usar
          comercialmente. La revisión de las imágenes no ejecuta por sí sola un pago: el reembolso
          se gestionaría manualmente después de una revisión administrativa independiente.
        </p>
        <p>
          Cuando proceda y sea posible, se intentará por el método de pago original.
          <strong> Pendiente de aprobación jurídica y fiscal:</strong> cómo opera la recompensa
          cuando no se autoriza el uso comercial, qué ocurre si el método original no admite
          reembolso y el tratamiento fiscal aplicable. No se promete aquí una fecha de abono
          ni un método alternativo.
        </p>
      </section>

      <section className="mw-section">
        <h2>Plazos y comunicación</h2>
        <p>
          La participación debe realizarse <strong>dentro de los 30 días posteriores a la entrega</strong>.
          MetalWolft comunicará la decisión de revisión en un máximo de <strong>7 días naturales</strong>
          desde la recepción de las fotografías. Si solicita imágenes adicionales o corregidas,
          deberá indicar al cliente cómo remitirlas y desde cuándo se contará ese plazo de revisión.
          El enlace individual también tiene una caducidad técnica: si caduca antes del plazo de
          participación, contacta con MetalWolft.
        </p>
      </section>

      <section className="mw-section">
        <h2>Uso comercial y privacidad</h2>
        <p>
          Enviar fotografías y autorizar su utilización comercial son decisiones distintas.
          El formulario permite enviar las fotos sin autorizar su publicación; la autorización
          comercial se solicita de forma expresa y no premarcada. La posible relación entre esa
          autorización y el incentivo de 20 € está pendiente de revisión jurídica antes de activar
          la promoción. Ninguna fotografía se publica automáticamente.
        </p>
        <p>
          La licencia o autorización de uso comercial no sustituye la información sobre el
          tratamiento de datos personales ni elimina los derechos reconocidos por la normativa
          de protección de datos. Las imágenes pueden contener datos de terceros; evita incluirlos
          si no tienes autorización adecuada.
        </p>
        <p>
          Puedes solicitar la retirada de la autorización o la supresión de las fotografías
          escribiendo a <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>. Son
          solicitudes distintas: retirar el permiso de uso comercial no elimina por sí solo
          los adjuntos recibidos por correo. Consulta también la{" "}
          <Link className="mw-inline-link" href="/politica-privacidad">política de privacidad</Link>.
        </p>
      </section>
    </LegalPageLayout>
  );
}
