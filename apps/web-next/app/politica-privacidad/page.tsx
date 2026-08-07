import { LegalPageLayout } from "@/components/legal/LegalPageLayout";
import { buildLegalRelatedLinks } from "@/lib/legal";
import { buildMetadata } from "@/lib/metadata";

const PATH = "/politica-privacidad";

export const metadata = buildMetadata({
  title: "Política de privacidad | MetalWolft",
  description:
    "Consulta cómo MetalWolft recopila, utiliza y protege los datos personales relacionados con pedidos, contacto y navegación web.",
  path: PATH
});

export default function PrivacyPolicyPage() {
  return (
    <LegalPageLayout
      path={PATH}
      title="Política de privacidad"
      eyebrow="Información legal"
      description="Tu privacidad es importante para nosotros. Aquí explicamos qué datos personales podemos recopilar, para qué los utilizamos y cómo protegemos la información asociada a tus pedidos, consultas y navegación."
      summaryTitle="Qué encontrarás en esta política"
      summaryItems={[
        "Datos que pueden recopilarse al comprar, contactar o navegar por la web.",
        "Usos principales de la información para pedidos, atención y mejora del servicio.",
        "Medidas de protección y derechos del usuario sobre sus datos personales.",
        "Cómo contactar con nosotros si necesitas ejercer tus derechos."
      ]}
      relatedLinks={buildLegalRelatedLinks(PATH)}
    >
      <section className="mw-section">
        <h2>Información que podemos recopilar</h2>
        <p>
          Podemos recopilar datos personales cuando te registras, realizas una
          compra, nos envías una consulta o navegas por la web. Según el caso,
          esta información puede incluir nombre, correo electrónico, dirección
          postal, número de teléfono y los datos necesarios para gestionar tu
          pedido o responder a tu mensaje.
        </p>
      </section>

      <section className="mw-section">
        <h2>Uso de la información</h2>
        <p>
          Utilizamos la información personal para procesar pedidos, resolver
          consultas, enviarte comunicaciones relacionadas con tu compra y mejorar
          la experiencia general del sitio. También podemos usarla para ofrecer
          asistencia antes o después de la compra cuando nos contactas por los
          canales disponibles.
        </p>
      </section>

      <section className="mw-section">
        <h2>Protección de los datos personales</h2>
        <p>
          Aplicamos medidas de seguridad razonables para proteger la información
          personal frente a accesos no autorizados, pérdida o uso indebido. No
          compartiremos tus datos con terceros ajenos al servicio solicitado,
          salvo cuando sea necesario para gestionar el pedido, atender la
          consulta o cumplir obligaciones legales aplicables.
        </p>
      </section>

      <section className="mw-section">
        <h2>Derechos del usuario</h2>
        <p>
          Puedes solicitar acceso, rectificación o eliminación de tus datos
          personales, así como plantear dudas sobre el tratamiento de la
          información. Si quieres ejercer cualquiera de estos derechos, puedes
          escribirnos a través de nuestra página de contacto.
        </p>
      </section>

      <section className="mw-section">
        <h2>Cambios en esta política</h2>
        <p>
          Nos reservamos el derecho de actualizar esta política para reflejar
          cambios normativos, operativos o de servicio. Cuando la actualización
          sea relevante, publicaremos la versión revisada en esta misma página.
        </p>
      </section>
    </LegalPageLayout>
  );
}
