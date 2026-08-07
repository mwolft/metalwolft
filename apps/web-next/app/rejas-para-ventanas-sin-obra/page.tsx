import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("rejas-para-ventanas-sin-obra");

  if (!article) {
    throw new Error("Missing static blog article: rejas-para-ventanas-sin-obra");
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default function WindowBarsWithoutConstructionPage() {
  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Qué es una reja sin obra y cómo se monta.",
        "Ventajas frente a soluciones empotradas.",
        "Tipo de fijación y tornillería de seguridad.",
        "Cuándo conviene elegir este sistema."
      ]}
      heroMedia={
        <figure className="mw-media-frame">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className="mw-article-hero-image"
            src={article.image}
            alt={article.imageAlt}
          />
        </figure>
      }
    >
      <section className="mw-section">
        <h2>Qué son las rejas para ventanas sin obra</h2>
        <p>
          Las rejas sin obra están pensadas para fijarse directamente al soporte
          sin necesidad de rozas ni albañilería. Son una opción muy cómoda cuando
          la fachada ya está acabada y quieres proteger la ventana sin meterte en
          una reforma.
        </p>
        <p>
          En la práctica, se apoyan sobre el hueco real y se fijan con tornillos
          de seguridad preparados para un montaje rápido, limpio y discreto.
        </p>
      </section>

      <section className="mw-section">
        <h2>Ventajas frente a una reja con obra</h2>
        <ul className="mw-list">
          <li>Instalación más limpia y normalmente más rápida.</li>
          <li>Menor dependencia de trabajos de albañilería y remates posteriores.</li>
          <li>Muy buena opción para fachadas ya terminadas o viviendas habitadas.</li>
          <li>Acabado visual cuidado sin renunciar a seguridad y rigidez.</li>
        </ul>
        <blockquote className="mw-quote">
          Una reja sin obra bien medida y bien fijada ofrece una solución práctica,
          duradera y muy agradecida en montaje.
        </blockquote>
      </section>

      <section className="mw-section">
        <h2>Cómo se fijan y qué seguridad ofrecen</h2>
        <p>
          El sistema suele basarse en tornillería de seguridad inviolable y puntos
          de anclaje preparados en el propio bastidor. Esto permite sujetar la reja
          con firmeza y proteger la fijación frente a manipulaciones sencillas desde el exterior.
        </p>
        <p>
          Para que el resultado sea bueno, la medición previa importa mucho. Si aún
          no lo has hecho, revisa{" "}
          <Link className="mw-inline-link" href="/medir-hueco-rejas-para-ventanas">cómo medir el hueco</Link>{" "}
          antes de pedir fabricación.
        </p>
      </section>

      <section className="mw-section">
        <h2>Cuándo conviene elegir este sistema</h2>
        <p>
          Es especialmente útil cuando no quieres tocar enfoscados, azulejos o
          acabados existentes. También funciona muy bien en viviendas donde se
          valora un montaje rápido y con poca intervención sobre la fachada.
        </p>
        <p>
          Si buscas un equilibrio entre seguridad, limpieza visual y facilidad de
          instalación, este sistema suele ser el más práctico.
        </p>
      </section>

      <section className="mw-section">
        <h2>Modelos que encajan bien con un montaje sin obra</h2>
        <p>
          Muchos clientes que buscan un montaje limpio terminan comparando modelos
          fijos sencillos, diseños actuales y alguna opción abatible si necesitan
          acceso de limpieza.
        </p>
        <ul className="mw-list">
          <li>
            <Link className="mw-inline-link" href="/rejas-para-ventanas/reja-fija-pittsburgh">
              Reja fija Pittsburgh
            </Link>
          </li>
          <li>
            <Link className="mw-inline-link" href="/rejas-para-ventanas/reja-fija-albany">
              Reja fija Albany
            </Link>
          </li>
          <li>
            <Link className="mw-inline-link" href="/rejas-para-ventanas/reja-abatible-cortland">
              Reja abatible Cortland
            </Link>
          </li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Siguiente paso recomendado</h2>
        <p>
          Si quieres cerrar la decisión con buen criterio, combina esta lectura con
          la <Link className="mw-inline-link" href="/instalation-rejas-para-ventanas">guía de instalación</Link>{" "}
          y la landing de{" "}
          <Link className="mw-inline-link" href="/rejas-para-ventanas-modernas">rejas para ventanas modernas</Link>.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
            Ver rejas a medida
          </Link>
          <Link className="mw-button mw-button--secondary" href="/instalation-rejas-para-ventanas">
            Ver instalación
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
