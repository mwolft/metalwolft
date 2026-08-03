import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import { ModernGrilleViewerLoader } from "@/components/visualization/ModernGrilleViewerLoader";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("rejas-para-ventanas-modernas");

  if (!article) {
    throw new Error("Missing static blog article: rejas-para-ventanas-modernas");
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default function ModernWindowBarsPage() {
  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Qué define una reja moderna en diseño y proporciones.",
        "Qué acabados encajan mejor con fachadas actuales.",
        "Modelos fijos y abatibles que mantienen una línea limpia.",
        "Por qué la fabricación a medida mejora el resultado final."
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
        <h2>Seguridad con una estética actual</h2>
        <p>
          Una reja moderna no renuncia a proteger. Lo que cambia es la manera de
          resolver perfiles, ritmos y proporciones para que el conjunto se integre
          mejor en una vivienda actual o en una rehabilitación con lenguaje limpio.
        </p>
        <p>
          En muchos casos funcionan especialmente bien las líneas rectas, los paños
          equilibrados y los acabados sobrios que no saturan la fachada.
        </p>
      </section>

      <section className="mw-section">
        <h2>Diseños que suelen funcionar mejor</h2>
        <ul className="mw-list">
          <li>Rejas fijas de líneas rectas y lectura ordenada.</li>
          <li>Diseños horizontales para ventanas anchas y fachadas modernas.</li>
          <li>Modelos con bastidor limpio y barrotes proporcionados.</li>
          <li>Opciones abatibles cuando hace falta acceso sin romper la estética.</li>
        </ul>
        <blockquote className="mw-quote">
          Una reja moderna destaca cuando se ve proporcionada al hueco y coherente
          con la carpintería, no cuando intenta llamar la atención a toda costa.
        </blockquote>
      </section>

      <section className="mw-section mw-modern-grille-section">
        <h2>Vista 3D de una reja Albany</h2>
        <p>Gira el modelo para ver su estructura desde distintos ángulos.</p>
        <ModernGrilleViewerLoader />
      </section>

      <section className="mw-section">
        <h2>Materiales, color y acabado</h2>
        <p>
          El acabado influye tanto como el diseño. Negro mate, blanco, grafito o
          tonos coordinados con la fachada suelen ser los más demandados cuando se
          busca una reja metálica discreta y elegante.
        </p>
        <p>
          Si además necesitas un montaje rápido, puedes cruzar esta lectura con la
          guía de{" "}
          <Link className="mw-inline-link" href="/rejas-para-ventanas-sin-obra">rejas para ventanas sin obra</Link>.
        </p>
      </section>

      <section className="mw-section">
        <h2>Modelos para inspirarte</h2>
        <p>
          Estas fichas ya funcionan en SSR dentro de Next y sirven como ejemplos
          reales de rejas para ventanas con un enfoque más limpio y contemporáneo.
        </p>
        <ul className="mw-list">
          <li>
            <Link className="mw-inline-link" href="/rejas-para-ventanas/reja-fija-pittsburgh">
              Reja fija Pittsburgh
            </Link>
          </li>
          <li>
            <Link className="mw-inline-link" href="/rejas-para-ventanas/reja-fija-idaho">
              Reja fija Idaho
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
        <h2>Por qué conviene hacerlas a medida</h2>
        <p>
          La fabricación a medida permite ajustar proporción, apoyo, anclaje y
          acabado al hueco real. Ese ajuste es el que evita improvisaciones y hace
          que la reja parezca parte natural de la vivienda.
        </p>
        <p>
          Antes de decidir modelo, revisa{" "}
          <Link className="mw-inline-link" href="/medir-hueco-rejas-para-ventanas">cómo medir el hueco</Link>{" "}
          y después vuelve al catálogo principal para comparar opciones reales.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
            Ver catálogo de rejas
          </Link>
          <Link className="mw-button mw-button--secondary" href="/medir-hueco-rejas-para-ventanas">
            Revisar medición
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
