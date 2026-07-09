import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("instalation-rejas-para-ventanas");

  if (!article) {
    throw new Error("Missing static blog article: instalation-rejas-para-ventanas");
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default function InstallationGuidePage() {
  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Herramientas necesarias antes del montaje.",
        "Orden correcto para presentar, marcar y fijar.",
        "Ajustes finales para mejorar el acabado.",
        "Recomendaciones de mantenimiento y seguridad."
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
        <h2>Herramientas y preparación previa</h2>
        <p>
          Antes de empezar conviene tener el hueco ya medido y la posición de la
          reja clara. Si aún no has revisado medidas, puedes hacerlo en nuestra{" "}
          <Link className="mw-inline-link" href="/medir-hueco-rejas-para-ventanas">guía para medir el hueco</Link>.
        </p>
        <ul className="mw-list">
          <li>Taladro y broca de pared adecuada al anclaje.</li>
          <li>Llave o punta TORX para tornillos de seguridad.</li>
          <li>Nivel para comprobar verticalidad y apoyo.</li>
          <li>Rotulador para marcar puntos de fijación.</li>
          <li>Cuñas o listones si necesitas pequeños ajustes de presentación.</li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Pasos para una instalación limpia y segura</h2>
        <ol className="mw-steps">
          <li>Presenta la reja en su hueco y comprueba que la posición final es la prevista.</li>
          <li>Nivela la pieza antes de marcar cualquier punto de anclaje.</li>
          <li>Marca cada agujero con precisión y retira la reja para taladrar cómodo.</li>
          <li>Limpia la zona de polvo antes de colocar tacos y tornillería.</li>
          <li>Vuelve a presentar la reja, atornilla y revisa el aplomo final.</li>
          <li>Coloca tapas o remates de seguridad si el sistema lo incorpora.</li>
        </ol>

        <div className="mw-split-media">
          <figure className="mw-media-frame">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562842/rejas-para-ventanas-modernas-2023_mambli.avif"
              alt="Reja para ventanas moderna preparada para instalar"
            />
          </figure>
          <figure className="mw-media-frame">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562850/rejas-para-ventanas-sin-obra-precio_bps3ec.avif"
              alt="Detalle de reja para ventanas sin obra"
            />
          </figure>
        </div>
      </section>

      <section className="mw-section">
        <h2>Consejos para evitar errores durante el montaje</h2>
        <p>
          En la práctica, muchas incidencias no vienen de la reja sino de un
          replanteo pobre o de querer taladrar con la pieza mal presentada.
          Toma tu tiempo en la fase de marcado y, si la reja es grande, monta con ayuda.
        </p>
        <blockquote className="mw-quote">
          Una buena instalación empieza antes del primer tornillo: medir, presentar y
          nivelar bien ahorra problemas de ajuste y de acabado.
        </blockquote>
        <p>
          Si buscas un sistema cómodo para fachada terminada, revisa también nuestras{" "}
          <Link className="mw-inline-link" href="/rejas-para-ventanas-sin-obra">rejas para ventanas sin obra</Link>.
        </p>
      </section>

      <section className="mw-section">
        <h2>Mantenimiento y remate final</h2>
        <p>
          Después del montaje conviene revisar el apriete, limpiar restos de polvo
          y proteger cualquier roce si el acabado lo necesita. Un mantenimiento básico
          ayuda a conservar el aspecto y la durabilidad de la reja durante años.
        </p>
        <ul className="mw-list">
          <li>Comprueba que no queden holguras en los puntos de fijación.</li>
          <li>Limpia el entorno y retira restos de obra o sellado.</li>
          <li>Revisa la pintura si la reja ha rozado en la instalación.</li>
          <li>Inspecciona periódicamente tornillos y remates en exteriores expuestos.</li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Vídeo de apoyo para la instalación</h2>
        <p>
          Este vídeo resume la secuencia general de montaje para una reja de ventana.
        </p>
        <video className="mw-video" controls>
          <source
            src="https://res.cloudinary.com/dewanllxn/video/upload/v1733563618/instalacion-rejas-para-ventanas_kcno5b.webm"
            type="video/webm"
          />
        </video>
      </section>

      <section className="mw-section">
        <h2>Después del montaje</h2>
        <p>
          Si ya tienes claro el sistema de fijación, vuelve al{" "}
          <Link className="mw-inline-link" href="/rejas-para-ventanas">catálogo de rejas para ventanas</Link>{" "}
          para comparar modelos y acabados. Si aún valoras opciones, también puedes revisar
          la guía sobre <Link className="mw-inline-link" href="/rejas-para-ventanas-modernas">rejas modernas</Link>.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
            Ver catálogo
          </Link>
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas-modernas">
            Ver diseños modernos
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
