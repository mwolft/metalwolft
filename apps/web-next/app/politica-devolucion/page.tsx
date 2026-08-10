import Link from "next/link";
import { LegalPageLayout } from "@/components/legal/LegalPageLayout";
import { buildLegalRelatedLinks } from "@/lib/legal";
import { buildMetadata } from "@/lib/metadata";

const PATH = "/politica-devolucion";

export const metadata = buildMetadata({
  title: "Política de devoluciones y garantías | MetalWolft",
  description:
    "Consulta las condiciones de devoluciones, garantías, incidencias de transporte y revisiones para productos metálicos fabricados a medida.",
  path: PATH
});

export default function ReturnsPolicyPage() {
  return (
    <LegalPageLayout
      path={PATH}
      title="Política de devoluciones y garantías"
      eyebrow="Información legal"
      description="En MetalWolft fabricamos cada reja a medida según las especificaciones del cliente. Esta política distingue con claridad entre desistimiento, garantía legal, incidencias visibles de transporte o pintura y reclamaciones tras la instalación."
      summaryTitle="Aspectos clave antes de comprar"
      summaryItems={[
        "Los productos personalizados no admiten desistimiento salvo defecto o error comprobado.",
        "Las incidencias visibles de pintura o transporte deben revisarse y comunicarse en 48 horas.",
        "El formulario de incidencias es el canal preferente para revisar defectos o discrepancias.",
        "La garantía legal no cubre daños causados por una instalación incorrecta o manipulación posterior."
      ]}
      relatedLinks={buildLegalRelatedLinks(PATH)}
    >
      <section className="mw-section">
        <h2>1. Productos personalizados y derecho de desistimiento</h2>
        <p>
          En MetalWolft fabricamos cada reja de forma individual según las
          medidas, acabados y especificaciones seleccionadas por el cliente. Por
          este motivo, los productos confeccionados a medida se rigen por la
          normativa aplicable a bienes personalizados, incluida la excepción del
          artículo 103.c del Real Decreto Legislativo 1/2007.
        </p>
        <p>
          De acuerdo con esta normativa, los productos fabricados conforme a las
          especificaciones del consumidor no admiten desistimiento ni devolución,
          salvo en caso de defecto, error comprobado de fabricación o incidencia
          acreditada en el acabado recibido.
        </p>
      </section>

      <section className="mw-section">
        <h2>2. Tolerancias de fabricación</h2>
        <p>
          Al tratarse de productos fabricados a medida, pueden existir pequeñas
          variaciones entre las medidas solicitadas y las medidas finales de la
          reja. Estas variaciones, dentro de los márgenes indicados, forman parte
          de las tolerancias normales del proceso de fabricación y no constituyen
          por sí mismas un defecto.
        </p>
        <p>
          <strong>Tolerancia máxima en altura y ancho: ±5 mm.</strong>
        </p>
      </section>

      <section className="mw-section">
        <h2>3. Incidencias visibles, pintura y transporte</h2>
        <p>
          Cada reja se pinta de forma individual, por lo que pueden aparecer
          pequeñas marcas de proceso o ligeras variaciones de tono. Si el
          producto presenta defectos visibles de pintura, desconchados, manchas,
          golpes o daños que puedan haberse producido en transporte, debes
          revisarlo antes de instalarlo y comunicar la incidencia en un plazo
          máximo de 48 horas desde la recepción.
        </p>
        <p>
          El canal preferente para esta revisión es el{" "}
          <Link className="mw-inline-link" href="/formulario-incidencias">formulario de incidencias</Link>{" "}
          del sitio. Si necesitas asistencia adicional, también puedes escribirnos
          desde la página de <Link href="/contact">contacto</Link> indicando tu
          número de pedido y adjuntando fotografías claras.
        </p>
        <p>Según el caso, podremos ofrecer alguna de estas soluciones:</p>
        <ul className="mw-list">
          <li>Envío de un kit de retoque con pintura original y material de apoyo.</li>
          <li>Compensación parcial si el cliente decide conservar el producto.</li>
          <li>Reparación, ajuste o reposición parcial o total cuando proceda.</li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>4. Diseños, proporciones y revisiones previas a la instalación</h2>
        <p>
          Los modelos mostrados en la web representan diseños base que se adaptan
          proporcionalmente a las medidas seleccionadas. Según la relación entre
          ancho y alto, pueden variar la disposición de barrotes, refuerzos u
          otros elementos necesarios para mantener estabilidad, seguridad y
          coherencia visual.
        </p>
        <p>
          Estas adaptaciones forman parte del proceso de fabricación a medida y
          no se consideran un defecto. Si detectas una diferencia relevante
          respecto a lo solicitado, debes comunicarla mediante el{" "}
          <Link className="mw-inline-link" href="/formulario-incidencias">formulario de incidencias</Link>{" "}
          antes de la instalación para que podamos revisar el caso y proponer la
          solución adecuada.
        </p>
      </section>

      <section className="mw-section">
        <h2>5. Instalación, manipulación y aceptación del producto</h2>
        <p>
          Las rejas, puertas y cerramientos fabricados a medida no admiten
          devolución una vez instalados o manipulados. Si observas cualquier
          incidencia en medidas, acabado o estado del producto, debes comunicarlo
          antes de la instalación y conservar el embalaje original hasta que la
          revisión quede resuelta.
        </p>
        <p>
          Una vez instalado el producto, se entenderá que el cliente acepta su
          conformidad con las medidas, el color, el tipo de anclaje y el acabado
          recibido, salvo que se acredite un defecto de fabricación existente en
          el momento de la entrega.
        </p>
      </section>

      <section className="mw-section">
        <h2>6. Procedimiento de revisión e incidencias</h2>
        <p>
          Si detectas un defecto o error de fabricación, debes comunicarlo
          mediante el formulario de incidencias, adjuntando fotografías claras
          del producto y una descripción precisa del problema. También puedes
          aportar tu número de pedido y cualquier dato útil para agilizar la
          comprobación técnica.
        </p>
      </section>

      <section className="mw-section">
        <h2>7. Costes, garantía legal y alcance de la cobertura</h2>
        <p>
          Cuando se confirme una incidencia imputable a fabricación o un daño
          acreditado del transporte en plazo, MetalWolft asumirá los costes
          razonables asociados a la solución propuesta. En otros supuestos, los
          gastos de devolución o revisión podrán corresponder al cliente.
        </p>
        <p>
          Todos los productos cuentan con la garantía legal de conformidad
          aplicable. Esta garantía cubre defectos de fabricación o materiales,
          pero no daños derivados de un uso inadecuado, instalación incorrecta,
          manipulación posterior o falta de mantenimiento.
        </p>
      </section>

      <section className="mw-section">
        <h2>8. Cancelación de pedidos</h2>
        <p>
          Los pedidos solo pueden cancelarse antes de iniciar la fabricación.
          Una vez comenzado el proceso, no es posible anular el pedido debido al
          carácter personalizado del producto.
        </p>
      </section>
    </LegalPageLayout>
  );
}
