import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("medir-hueco-rejas-para-ventanas");

  if (!article) {
    throw new Error("Missing static blog article: medir-hueco-rejas-para-ventanas");
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default function MeasureWindowOpeningPage() {
  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Cómo detectar el ancho real del hueco.",
        "Qué margen dejar para un montaje limpio.",
        "Cómo resolver pequeñas diferencias entre puntos.",
        "Qué revisar antes de pedir la fabricación."
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
        <h2>Por qué medir bien el hueco es tan importante</h2>
        <p>
          Cuando hablamos de <Link className="mw-inline-link" href="/rejas-para-ventanas">rejas para ventanas a medida</Link>,
          la medida correcta no es un detalle menor. El hueco real casi nunca es
          un rectángulo perfecto y suele presentar pequeñas diferencias entre la
          parte superior, la zona central y la inferior.
        </p>
        <p>
          Medir bien evita rehacer el trabajo, mejora el ajuste visual y ayuda a
          que la reja se monte con un apoyo estable. Un error de pocos milímetros
          en el ancho puede ser más problemático que una pequeña variación en el alto.
        </p>
      </section>

      <section className="mw-section">
        <h2>Cómo medir el ancho del hueco</h2>
        <p>
          La referencia principal debe ser siempre la medida más estrecha. Toma
          el ancho en tres puntos: abajo, en el centro y arriba. Después, conserva
          el valor menor como base para fabricar la reja.
        </p>
        <ul className="mw-list">
          <li>Mide con cinta metálica, no con metro textil.</li>
          <li>Anota cada valor por separado antes de comparar.</li>
          <li>Repite la medición una segunda vez para confirmar.</li>
          <li>Si hay desniveles, da prioridad al punto más cerrado del hueco.</li>
        </ul>

        <div className="mw-split-media">
          <figure className="mw-media-frame">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562857/rejas-para-ventanas-modernas_y9ti5y.jpg"
              alt="Ejemplo de hueco con reja moderna"
            />
          </figure>
          <figure className="mw-media-frame">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://res.cloudinary.com/dewanllxn/image/upload/v1757842246/rejas-para-ventanas-sin-obra_-_2__jsnqjx.avif"
              alt="Reja para ventanas sin obra instalada"
            />
          </figure>
        </div>
      </section>

      <section className="mw-section">
        <h2>Qué margen dejar en alto y en la base</h2>
        <p>
          En muchos montajes conviene dejar un pequeño margen en la parte inferior,
          normalmente de unos pocos milímetros, para evitar acumulación de suciedad,
          facilitar la limpieza y reducir el contacto directo con el apoyo.
        </p>
        <blockquote className="mw-quote">
          El ancho manda la fabricación; el alto suele admitir un pequeño margen
          controlado para mejorar montaje y mantenimiento.
        </blockquote>
        <p>
          Si después vas a montar una <Link className="mw-inline-link" href="/rejas-para-ventanas-sin-obra">reja sin obra</Link>,
          este margen ayuda también a nivelar mejor la pieza y a corregir ligeras
          diferencias propias de la albañilería.
        </p>
      </section>

      <section className="mw-section">
        <h2>Qué hacer si el hueco no es perfecto</h2>
        <p>
          Es normal encontrar paredes con leves panzas o cantos no del todo rectos.
          Si la diferencia es pequeña, la solución suele pasar por un ajuste de montaje
          y un remate posterior con silicona o material de sellado adecuado.
        </p>
        <p>
          Lo importante es no fabricar tomando una media inventada. La medida válida
          debe responder al punto más estrecho y al apoyo real donde se asentará la reja.
        </p>
      </section>

      <section className="mw-section">
        <h2>Vídeo de apoyo para revisar el proceso</h2>
        <p>
          Si prefieres revisar el proceso de forma visual, este vídeo resume la
          lógica de medición antes de pasar a fabricación.
        </p>
        <video className="mw-video" controls>
          <source
            src="https://res.cloudinary.com/dewanllxn/video/upload/v1733563614/medicion-rejas-para-ventanas_t2lbbe.webm"
            type="video/webm"
          />
        </video>
      </section>

      <section className="mw-section">
        <h2>Siguiente paso recomendado</h2>
        <p>
          Con la medida clara, el siguiente paso es revisar la{" "}
          <Link className="mw-inline-link" href="/instalation-rejas-para-ventanas">guía de instalación</Link>{" "}
          y después volver al catálogo para comparar modelos reales de rejas para ventanas.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--secondary" href="/instalation-rejas-para-ventanas">
            Ver instalación
          </Link>
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
            Ir al catálogo
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
