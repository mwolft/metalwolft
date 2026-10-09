import type { Metadata } from "next";
import Link from "next/link";
import { LegalPageLayout } from "@/components/legal/LegalPageLayout";
import { buildLegalRelatedLinks } from "@/lib/legal";
import { buildMetadata } from "@/lib/metadata";

const PATH = "/condiciones-promocion-fotos";

export const metadata: Metadata = {
  ...buildMetadata({
    title: "Condiciones de la promoción de fotografías | MetalWolft",
    description: "Borrador de las condiciones de participación en la promoción de fotografías de rejas instaladas.",
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
      description="Información sobre la invitación a compartir fotografías de rejas instaladas y la posible oferta de 20 € por pedido. Estas condiciones son un borrador pendiente de aprobación."
      summaryTitle="Antes de participar"
      summaryItems={[
        "La participación es voluntaria y requiere una invitación individual tras la entrega.",
        "El incentivo previsto es de 20 € por pedido elegible, no por fotografía.",
        "Las fotografías se revisan antes de aprobarse; el reembolso no es automático.",
        "La autorización de uso comercial se decide por separado al enviar las fotos."
      ]}
      relatedLinks={buildLegalRelatedLinks(PATH)}
    >
      <section className="mw-section">
        <h2>Borrador pendiente de aprobación</h2>
        <p>
          Esta página aún no establece una promoción vigente ni genera derecho a un reembolso.
          Antes de ofrecer la modalidad incentivada fuera de una prueba se deben aprobar y
          publicar las condiciones completas. Las invitaciones de simulación se identifican
          expresamente como <strong>SIMULACIÓN — SIN REEMBOLSO</strong>.
        </p>
      </section>

      <section className="mw-section">
        <h2>Organizador y participación</h2>
        <p>
          MetalWolft organizaría esta iniciativa para recibir fotografías reales de sus rejas
          una vez instaladas. La participación sería voluntaria y solo mediante una invitación
          individual enviada tras la entrega de un pedido elegible. El enlace de cada invitación
          permite enviar hasta cinco fotografías; no es una convocatoria abierta.
        </p>
      </section>

      <section className="mw-section">
        <h2>Fotografías y revisión</h2>
        <p>
          Se solicitan imágenes de las rejas instaladas: una vista general, una en la que se
          aprecie el diseño y, opcionalmente, detalles o perspectivas. No se exige calidad
          profesional. Conviene evitar personas identificables, matrículas e información privada.
          MetalWolft revisaría las fotografías antes de decidir si las aprueba.
        </p>
        <p>
          <strong>Criterios propuestos, pendientes de aprobación:</strong> que las imágenes
          permitan reconocer las rejas del pedido instaladas, que sean legibles y que la persona
          participante pueda compartirlas. Se propone rechazar imágenes que no muestren el
          producto, estén dañadas o duplicadas, o incluyan personas identificables u otros datos
          privados sin autorización adecuada. Estos criterios y la forma de comunicar un rechazo
          deben cerrarse antes de activar la promoción. Ninguna fotografía se aprueba por el mero
          hecho de enviarla.
        </p>
      </section>

      <section className="mw-section">
        <h2>Incentivo previsto y reembolso</h2>
        <p>
          La modalidad incentivada prevé <strong>20 € por pedido elegible</strong>, no por
          fotografía. La aprobación de las imágenes no ejecuta por sí sola un pago: cualquier
          reembolso requeriría una revisión administrativa independiente.
        </p>
        <p>
          Cuando proceda y sea técnicamente posible, se estudiaría realizarlo por el método de
          pago original. <strong>Pendiente de aprobación:</strong> elegibilidad definitiva,
          supuestos en que ese método no esté disponible, procedimiento alternativo si lo
          hubiera y condiciones económicas y fiscales aplicables. No se promete aquí una fecha
          ni un método alternativo de pago.
        </p>
      </section>

      <section className="mw-section">
        <h2>Plazos y comunicación</h2>
        <p>
          <strong>Pendiente de aprobación:</strong> plazo para participar desde la invitación y
          plazo para comunicar la decisión tras recibir las fotografías. Se deberán indicar de
          forma clara en la versión definitiva antes de ofrecer la promoción.
        </p>
      </section>

      <section className="mw-section">
        <h2>Uso comercial y privacidad</h2>
        <p>
          Enviar fotografías y autorizar su utilización comercial son decisiones distintas.
          Puedes participar sin autorizar su publicación. Si autorizas el uso comercial de forma
          expresa, el alcance de esa autorización se mostrará en el formulario antes del envío;
          las fotografías no se publican automáticamente.
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
