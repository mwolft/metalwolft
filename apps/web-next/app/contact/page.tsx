import Link from "next/link";
import { ContactForm } from "@/components/contact/ContactForm";
import { PageContainer } from "@/components/layout/PageContainer";
import { BreadcrumbJsonLd } from "@/components/seo/BreadcrumbJsonLd";
import { JsonLd } from "@/components/seo/JsonLd";
import { contactDetails, contactLinks } from "@/lib/contact";
import { absoluteUrl, buildMetadata, siteConfig } from "@/lib/metadata";

const PAGE_PATH = "/contact";
const PAGE_TITLE = "Contacto para rejas para ventanas a medida | MetalWolft";
const PAGE_DESCRIPTION =
  "Contacta con MetalWolft para resolver dudas sobre medidas, instalación o presupuesto de rejas para ventanas a medida por teléfono, WhatsApp o email.";

type ContactAction = {
  title: string;
  description: string;
  href: string;
  cta: string;
  external?: boolean;
};

const contactActions: ContactAction[] = [
  {
    title: "Solicitar presupuesto",
    description:
      "Accede al catálogo principal para revisar modelos y preparar tu presupuesto a medida.",
    href: contactLinks.quote,
    cta: "Ir a rejas para ventanas"
  },
  {
    title: "Llamar por teléfono",
    description:
      "Habla con nosotros si prefieres resolver tus dudas directamente antes de decidir el modelo.",
    href: contactLinks.phone,
    cta: contactDetails.phoneDisplay
  },
  {
    title: "Escribir por WhatsApp",
    description:
      "Envíanos fotos, medidas o preguntas rápidas y te orientamos sobre instalación y acabados.",
    href: contactLinks.whatsapp,
    cta: "Abrir WhatsApp",
    external: true
  },
  {
    title: "Enviar un email",
    description:
      "Si necesitas dejar la consulta por escrito, puedes enviarnos tu mensaje y te responderemos cuanto antes.",
    href: contactLinks.email,
    cta: contactDetails.email
  }
];

export const metadata = buildMetadata({
  title: PAGE_TITLE,
  description: PAGE_DESCRIPTION,
  path: PAGE_PATH
});

function buildOrganizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: siteConfig.name,
    url: absoluteUrl("/"),
    logo: siteConfig.defaultOgImage,
    email: contactDetails.email,
    telephone: contactDetails.phoneDisplay,
    contactPoint: [
      {
        "@type": "ContactPoint",
        contactType: "sales",
        areaServed: contactDetails.supportArea,
        availableLanguage: ["es"],
        telephone: contactDetails.phoneDisplay,
        email: contactDetails.email
      }
    ]
  };
}

function buildContactPageJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "ContactPage",
    name: PAGE_TITLE,
    url: absoluteUrl(PAGE_PATH),
    description: PAGE_DESCRIPTION,
    isPartOf: {
      "@type": "WebSite",
      name: siteConfig.name,
      url: absoluteUrl("/")
    },
    about: {
      "@type": "Organization",
      name: siteConfig.name
    }
  };
}

export default function ContactPage() {
  return (
    <div className="mw-page">
      <PageContainer>
        <BreadcrumbJsonLd
          items={[
            { name: "Inicio", path: "/" },
            { name: "Contacto", path: PAGE_PATH }
          ]}
        />
        <JsonLd data={[buildOrganizationJsonLd(), buildContactPageJsonLd()]} />

        <nav className="mw-breadcrumbs" aria-label="Breadcrumb">
          <Link href="/">Inicio</Link>
          <span>/</span>
          <span aria-current="page">Contacto</span>
        </nav>

        <section className="mw-hero">
          <div className="mw-hero__copy">
            <p className="mw-eyebrow">Atención directa</p>
            <h1 className="mw-title mw-title--compact">Contacto para resolver tu proyecto</h1>
            <p className="mw-lead">
              Estamos listos para resolver tus dudas y atender tus necesidades.
              Si necesitas ayuda con medidas, instalación o presupuesto para unas
              rejas para ventanas a medida, te responderemos rápidamente para
              ofrecerte la mejor solución.
            </p>
            <div className="mw-actions">
              <a
                className="mw-button mw-button--primary"
                href={contactLinks.whatsapp}
                rel="noopener noreferrer"
                target="_blank"
              >
                Hablar por WhatsApp
              </a>
              <Link className="mw-button mw-button--secondary" href={contactLinks.quote}>
                Solicitar presupuesto
              </Link>
            </div>
          </div>

          <aside className="mw-panel" aria-label="Canales de contacto disponibles">
            <p className="mw-note">Canales disponibles</p>
            <h2>Elige la vía que te resulte más cómoda</h2>
            <ul className="mw-list">
              <li>Teléfono directo para dudas rápidas antes de comprar.</li>
              <li>WhatsApp para consultas, medidas o fotos del hueco.</li>
              <li>Email para explicaciones más detalladas o seguimiento.</li>
              <li>Acceso al catálogo para preparar presupuesto orientativo.</li>
            </ul>
          </aside>
        </section>

        <section className="mw-section">
          <h2>Cómo podemos ayudarte</h2>
          <p>
            Esta página concentra las vías principales de contacto para quien
            todavía está comparando modelos, necesita confirmar cómo medir el
            hueco o quiere validar si una instalación sin obra encaja en su caso.
          </p>
          <p>
            Si ya sabes qué tipo de reja buscas, puedes ir directamente al
            catálogo principal y revisar modelos reales antes de escribirnos.
          </p>
        </section>

        <section className="mw-section">
          <h2>Canales de contacto y presupuesto</h2>
          <div className="mw-contact-grid">
            {contactActions.map((action) => (
              <article className="mw-contact-card" key={action.title}>
                <p className="mw-note">{action.title}</p>
                <p>{action.description}</p>
                {action.href.startsWith("/") ? (
                  <Link className="mw-inline-link" href={action.href}>
                    {action.cta}
                  </Link>
                ) : (
                  <a
                    className="mw-inline-link"
                    href={action.href}
                    rel={action.external ? "noopener noreferrer" : undefined}
                    target={action.external ? "_blank" : undefined}
                  >
                    {action.cta}
                  </a>
                )}
              </article>
            ))}
          </div>
        </section>

        <section className="mw-section">
          <h2>Escríbenos tu consulta</h2>
          <p>
            Si prefieres dejar todos los datos por escrito, puedes usar este
            formulario para contarnos tu caso y explicarnos qué necesitas en
            medidas, instalación o presupuesto.
          </p>
          <ContactForm />
        </section>

        <section className="mw-section">
          <h2>Siguientes pasos recomendados</h2>
          <p>
            Antes de contactar, muchas dudas se resuelven más rápido revisando
            la guía de medición o la guía de instalación. Si ya las has visto,
            escríbenos con medidas o una foto del hueco y podremos orientarte
            mejor desde el primer mensaje.
          </p>
          <div className="mw-actions">
            <Link className="mw-button mw-button--secondary" href="/medir-hueco-rejas-para-ventanas">
              Ver guía de medición
            </Link>
            <Link className="mw-button mw-button--secondary" href="/instalation-rejas-para-ventanas">
              Ver guía de instalación
            </Link>
          </div>
        </section>
      </PageContainer>
    </div>
  );
}
