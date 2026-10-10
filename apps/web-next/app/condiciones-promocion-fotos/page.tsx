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
        "La participación es voluntaria y exclusiva para clientes con pedidos elegibles e invitación individual.",
        "Basta fotografiar una reja instalada: una foto frontal y otra lateral o en perspectiva.",
        "El incentivo previsto es de 20 € una sola vez por pedido aprobado, no por fotografía.",
        "Hay 30 días desde la entrega para participar y la revisión se comunicará en un máximo de 7 días naturales.",
        "La promoción de 20 € requiere aceptar expresamente una licencia comercial; el reembolso no es automático."
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
          incluye varias rejas, basta con fotografiar una sola. Participar o no participar no altera
          los derechos ni las garantías de la compra.
        </p>
      </section>

      <section className="mw-section">
        <h2>Fotografías y revisión</h2>
        <p>
          Se requieren dos fotografías de la misma reja instalada: una frontal y otra lateral o en
          perspectiva. Puedes añadir hasta tres imágenes más de detalle u otras vistas. La reja debe
          aparecer completa, aproximadamente centrada, nítida y bien iluminada. Las fotos hechas
          con móvil son válidas; no se exige calidad profesional. Evita personas identificables,
          matrículas, números de vivienda u otros datos que permitan identificar domicilios o terceros.
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
          comercialmente. Para participar en esta modalidad es necesario aceptar expresamente la
          licencia de uso comercial aplicable a las fotografías. Sin esa aceptación no se participa
          en la promoción remunerada. La revisión de las imágenes no ejecuta por sí sola un pago:
          el reembolso se gestionaría manualmente después de una revisión administrativa independiente.
        </p>
        <p>
          El abono de 20 € por pedido aprobado se gestionará manualmente, preferentemente mediante
          el método de pago original. Si no es posible, MetalWolft contactará con el cliente para
          acordar una alternativa segura. No existe abono automático.
          <strong> Pendiente de aprobación jurídica y fiscal:</strong> el tratamiento concreto
          de la recompensa y el procedimiento de pago alternativo antes de activar la promoción real.
        </p>
      </section>

      <section className="mw-section">
        <h2>Plazos y comunicación</h2>
        <p>
          La participación debe realizarse dentro de los <strong>30 días naturales desde la fecha
          real de entrega</strong>. MetalWolft comunicará la decisión de revisión en un máximo de
          <strong> 7 días naturales desde la recepción acreditada</strong> de las fotografías. Si
          solicita imágenes adicionales o corregidas, indicará cómo remitirlas por correo. No existe
          un segundo formulario de envío; la recepción acreditada de fotografías corregidas inicia
          de nuevo el plazo de revisión. El enlace individual caduca al terminar el plazo de participación.
        </p>
      </section>

      <section className="mw-section">
        <h2>Licencia de uso comercial</h2>
        <p>
          La licencia es una decisión expresa y no premarcada, separada de la información sobre
          protección de datos. La promoción remunerada exige su aceptación; una invitación a enviar
          fotografías voluntarias permite no concederla. La mera recepción de imágenes no concede
          derechos de publicación. Ninguna fotografía se publica automáticamente.
        </p>
        <p>
          El cliente conserva la titularidad y los derechos sobre sus fotografías y debe disponer
          de los derechos necesarios sobre las imágenes que envía. La licencia concedida a
          MetalWolft es <strong>no exclusiva</strong>, tiene alcance <strong>mundial</strong> y dura
          <strong> cinco años desde su aceptación</strong>. Permite reproducir y utilizar las
          fotografías en la web y fichas de productos de MetalWolft, redes sociales, publicidad
          y catálogos y materiales promocionales digitales o impresos.
        </p>
        <p>
          MetalWolft puede recortar las fotografías, ajustar su iluminación y color y cambiar
          su tamaño o formato, pero no alterar engañosamente las características del producto.
          Los proveedores técnicos o publicitarios solo pueden trabajar con las imágenes para
          prestar servicios a MetalWolft, sin explotación comercial independiente. No se presume
          autorización de las personas o titulares de derechos ajenos que aparezcan en las imágenes.
        </p>
      </section>

      <section className="mw-section">
        <h2>Fotografías voluntarias y datos personales</h2>
        <p>
          Las fotografías pueden enviarse sin participar en la promoción de 20 € cuando la invitación
          sea voluntaria. En ese caso no es obligatorio conceder licencia comercial ni existe derecho
          al incentivo. El tratamiento de datos personales y los derechos correspondientes son
          independientes de la licencia; esta no sustituye las obligaciones de privacidad ni
          supone renunciar a derechos reconocidos por el RGPD. Evita incluir personas o elementos
          que permitan identificar domicilios o terceros.
        </p>
        <p>
          Puedes contactar con <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a>
          para plantear solicitudes relativas a la licencia o pedir la retirada de fotografías.
          Cada solicitud se valorará conforme a los derechos y obligaciones aplicables. Cuando
          proceda la retirada, MetalWolft cesará los nuevos usos y gestionará la retirada de los
          canales bajo su control; no puede garantizar la eliminación inmediata de todas las
          publicaciones o copias anteriores en Internet. Retirar la licencia y solicitar la
          supresión de los adjuntos recibidos por correo son trámites distintos. Consulta también la{" "}
          <Link className="mw-inline-link" href="/politica-privacidad">política de privacidad</Link>.
        </p>
      </section>
    </LegalPageLayout>
  );
}
