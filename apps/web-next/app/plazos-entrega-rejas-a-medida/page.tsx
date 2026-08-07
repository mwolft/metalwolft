import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import { DeliveryEstimate } from "@/components/product/DeliveryEstimate";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";
import { fetchDeliveryEstimate } from "@/lib/delivery-estimate";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("plazos-entrega-rejas-a-medida");

  if (!article) {
    throw new Error("Missing static blog article: plazos-entrega-rejas-a-medida");
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default async function DeliveryTimesPage() {
  const deliveryEstimate = await fetchDeliveryEstimate();

  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Cada reja se fabrica bajo pedido.",
        "La web muestra una previsión orientativa de entrega.",
        "El intervalo puede actualizarse cuando cambia la planificación.",
        "La fecha estimada no constituye una fecha contractual."
      ]}
      heroMedia={
        <figure className="mw-media-frame">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className="mw-article-hero-image"
            src={article.image}
            alt={article.imageAlt}
            width="825"
            height="550"
          />
        </figure>
      }
    >
      <section className="mw-section">
        <h2>Consulta la previsión actual de entrega</h2>
        <p>
          Cada reja se fabrica bajo pedido. Para ayudarte a planificar la compra,
          MetalWolft mantiene una previsión global de entrega y puede ajustarla cuando
          cambia la planificación del taller.
        </p>
        <DeliveryEstimate estimate={deliveryEstimate} variant="banner" />
        <p>
          El intervalo mostrado es orientativo y representa una previsión general para
          los pedidos realizados en ese momento. No es una fecha contractual ni una
          promesa específica para un producto o un destino concretos.
        </p>
      </section>

      <section className="mw-section">
        <h2>¿Por qué mostramos un intervalo de fechas?</h2>
        <p>
          La fabricación bajo pedido requiere producir la reja con la configuración
          elegida, prepararla y dejarla lista para el transporte. Por eso, un intervalo
          permite comunicar la previsión con más claridad que un único día cerrado.
        </p>
        <p>
          Cuando cambia la planificación, MetalWolft puede actualizar esa previsión para
          que la información publicada siga siendo útil antes de comprar.
        </p>
      </section>

      <section className="mw-section">
        <h2>¿Qué puede influir en la entrega?</h2>
        <p>
          La previsión publicada es global y no calcula de forma individual las
          circunstancias de cada pedido. Como orientación general, la entrega puede verse
          condicionada por:
        </p>
        <ul className="mw-list">
          <li>El volumen general de trabajo del taller.</li>
          <li>Las características concretas del pedido.</li>
          <li>La preparación de la reja y su transporte.</li>
          <li>Posibles incidencias logísticas ajenas a la fabricación.</li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Antes de realizar tu pedido</h2>
        <p>
          Antes de elegir un modelo, conviene revisar estos pasos para que la fabricación
          pueda partir de una configuración correcta:
        </p>
        <ul className="mw-list">
          <li>
            <Link className="mw-inline-link" href="/medir-hueco-rejas-para-ventanas">
              Mide correctamente el hueco
            </Link>
            .
          </li>
          <li>Comprueba el soporte y el tipo de anclaje que necesitas.</li>
          <li>
            Consulta la{" "}
            <Link className="mw-inline-link" href="/instalation-rejas-para-ventanas">
              guía de instalación
            </Link>
            .
          </li>
          <li>Revisa la previsión orientativa mostrada en la web.</li>
        </ul>
        <div className="mw-actions">
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
            Ver modelos de rejas
          </Link>
        </div>
      </section>

      <section className="mw-section">
        <h2>¿Cómo puedo consultar el estado de mi pedido?</h2>
        <p>
          Una vez realizado el pedido, puedes consultar la información disponible desde
          tu área privada. Si necesitas ayuda adicional, también puedes contactar con
          MetalWolft sin que ello implique fijar una fecha de entrega concreta.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--secondary" href="/mi-cuenta/pedidos">
            Ver mis pedidos
          </Link>
          <Link className="mw-button mw-button--secondary" href="/contact">
            Contactar con MetalWolft
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
