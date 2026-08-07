import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("recepcion-pedidos-revisar-antes-firmar");

  if (!article) {
    throw new Error(
      "Missing static blog article: recepcion-pedidos-revisar-antes-firmar"
    );
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default function OrderReceptionGuidePage() {
  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Revisa el embalaje antes de dar la entrega por correcta.",
        "Documenta cualquier daño con fotografías claras.",
        "Conserva la caja, las protecciones y las etiquetas.",
        "Comunica la incidencia dentro del plazo vigente."
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
        <h2>Qué revisar al recibir el pedido</h2>
        <p>
          Antes de abrir el paquete, dedica unos minutos a comprobar su estado
          exterior y el número de bultos recibidos.
        </p>
        <ul className="mw-list">
          <li>Golpes, perforaciones o deformaciones visibles en el embalaje.</li>
          <li>Zonas húmedas o mojadas.</li>
          <li>Precintos abiertos o manipulados.</li>
          <li>Etiquetas o bultos que no correspondan.</li>
          <li>Ruidos de piezas sueltas en el interior.</li>
          <li>Comprueba que recibes todos los bultos indicados.</li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Si observas daños en el embalaje</h2>
        <ol className="mw-list">
          <li>Haz fotografías del paquete antes de abrirlo.</li>
          <li>
            Si el transportista permite dejar observaciones en la entrega, indica que
            el embalaje presenta daños visibles.
          </li>
          <li>
            Abre el paquete con cuidado y documenta también cualquier daño del
            producto.
          </li>
          <li>Conserva el embalaje y las protecciones.</li>
          <li>
            Contacta con MetalWolft lo antes posible y, en todo caso, dentro del plazo
            máximo de 48 horas indicado en nuestra{" "}
            <Link className="mw-inline-link" href="/politica-devolucion">
              política de devoluciones y garantías
            </Link>
            .
          </li>
        </ol>
      </section>

      <section className="mw-section">
        <h2>Si el embalaje parece correcto</h2>
        <p>
          Aunque el paquete no presente daños exteriores, revisa el producto al
          desembalarlo y conserva las protecciones hasta comprobar que todo está
          correcto.
        </p>
      </section>

      <section className="mw-section">
        <h2>Qué necesitamos para revisar una incidencia</h2>
        <ul className="mw-list">
          <li>El número o localizador del pedido.</li>
          <li>Fotografías generales del embalaje.</li>
          <li>Fotografías de la etiqueta de transporte.</li>
          <li>Fotografías claras del daño.</li>
          <li>Un vídeo si ayuda a mostrar el problema.</li>
          <li>Una descripción breve de lo ocurrido.</li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Conserva el embalaje</h2>
        <p>
          No deseches la caja, protecciones ni etiquetas hasta que hayamos revisado la
          incidencia. La documentación y el embalaje pueden ser necesarios para
          estudiar el daño y gestionar la reclamación de transporte.
        </p>
      </section>

      <section className="mw-section">
        <h2>Contacta con nosotros</h2>
        <p>
          Si detectas cualquier problema al recibir el pedido, envíanos la información
          desde nuestros canales de contacto para que podamos revisar el caso.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--primary" href="/contact">
            Contactar con MetalWolft
          </Link>
          <Link className="mw-button mw-button--secondary" href="/politica-devolucion">
            Consultar la política vigente
          </Link>
        </div>
        <p>
          Si todavía estás preparando tu compra, consulta la{" "}
          <Link className="mw-inline-link" href="/plazos-entrega-rejas-a-medida">
            previsión de entrega
          </Link>{" "}
          y los{" "}
          <Link className="mw-inline-link" href="/rejas-para-ventanas">
            modelos de rejas para ventanas
          </Link>
          .
        </p>
      </section>
    </BlogArticleShell>
  );
}
