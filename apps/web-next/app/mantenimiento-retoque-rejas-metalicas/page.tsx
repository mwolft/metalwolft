import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("mantenimiento-retoque-rejas-metalicas");

  if (!article) {
    throw new Error("Missing static blog article: mantenimiento-retoque-rejas-metalicas");
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default function MaintenanceAndTouchUpGuidePage() {
  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Cómo limpiar el acabado sin utilizar productos agresivos.",
        "Qué revisar después de roces, golpes u obras cercanas.",
        "Cuándo puede hacerse un retoque localizado.",
        "Cuándo conviene parar y valorar el estado de la reja."
      ]}
      heroMedia={
        <figure className="mw-media-frame">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="mw-article-hero-image" src={article.image} alt={article.imageAlt} />
        </figure>
      }
    >
      <section className="mw-section mw-maintenance-toc" aria-labelledby="maintenance-toc-title">
        <p className="mw-note">Guía práctica</p>
        <h2 id="maintenance-toc-title">Índice de mantenimiento</h2>
        <nav aria-label="Índice de la guía de mantenimiento y retoque">
          <ol>
            <li><a href="#antes-de-intervenir">Antes de intervenir</a></li>
            <li><a href="#limpieza">Limpieza ordinaria</a></li>
            <li><a href="#revision">Revisión periódica</a></li>
            <li><a href="#retoque">Retoque localizado</a></li>
            <li><a href="#corrosion">Acero expuesto y corrosión</a></li>
            <li><a href="#obras-posteriores">Obras posteriores</a></li>
            <li><a href="#preguntas">Preguntas frecuentes</a></li>
          </ol>
        </nav>
      </section>

      <section className="mw-section" id="antes-de-intervenir">
        <h2>Antes de intervenir</h2>
        <p>
          Para pequeños retoques recomendamos utilizar el esmalte de retoque correspondiente al color y acabado
          original de la reja. Las rejas MetalWolft utilizan un sistema de esmalte sintético antioxidante TITAN
          Oxirón.
        </p>
        <p>Antes de limpiar o retocar, identifica cuándo y cómo apareció el daño.</p>
        <aside className="mw-maintenance-callout" aria-label="No intervenir todavía">
          <p className="mw-maintenance-callout__title">No intervenir todavía</p>
          <p>
            Si el daño, desconchado o posible defecto ya estaba presente antes de instalar, no lo retoques.
            Haz fotografías claras y comunícalo mediante el{" "}
            <Link className="mw-inline-link" href="/formulario-incidencias">formulario de incidencias</Link>.
          </p>
          <p>
            Consulta también la{" "}
            <Link className="mw-inline-link" href="/recepcion-pedidos-revisar-antes-firmar">guía de recepción</Link>{" "}
            y la <Link className="mw-inline-link" href="/politica-devolucion">política vigente</Link>.
          </p>
        </aside>
        <p>
          Si el roce se produjo después, durante la manipulación, la instalación o el uso, y es pequeño y
          localizado, puedes seguir el procedimiento de esta guía.
        </p>
      </section>

      <section className="mw-section" id="limpieza">
        <h2>Limpieza ordinaria</h2>
        <p>Para la limpieza habitual basta con métodos suaves:</p>
        <ol className="mw-steps">
          <li>Retira el polvo o la suciedad superficial con agua.</li>
          <li>Limpia con jabón neutro y un paño o esponja suave.</li>
          <li>Aclara cuando proceda.</li>
          <li>Seca la superficie si queda humedad acumulada.</li>
        </ol>
        <aside className="mw-maintenance-callout" aria-label="Productos que conviene evitar">
          <p>
            <strong>Evita disolventes, abrasivos, estropajos y productos agresivos</strong> como método de limpieza
            ordinaria. Los productos usados para limpiar herramientas no son una recomendación para limpiar una
            reja terminada.
          </p>
        </aside>
      </section>

      <section className="mw-section" id="revision">
        <h2>Revisión periódica</h2>
        <p>
          La frecuencia de revisión dependerá de la exposición, el entorno y el uso de la reja. Conviene revisar
          también el acabado después de golpes, roces o trabajos realizados cerca de ella.
        </p>
        <ul className="mw-list">
          <li>Cantos y aristas.</li>
          <li>Uniones y puntos de fijación.</li>
          <li>Tornillería y remates, cuando existan.</li>
          <li>Zonas que hayan sufrido golpes o roces.</li>
          <li>Puntos donde el acero pueda haber quedado expuesto.</li>
        </ul>
      </section>

      <section className="mw-section" id="retoque">
        <h2>Retoque de un pequeño roce o desconchado</h2>
        <p>
          Este procedimiento es adecuado para un daño puntual, pequeño y localizado. Si la pintura presenta una
          degradación amplia, recurrente o difícil de valorar, no lo trates como un simple retoque.
        </p>
        <ol className="mw-steps">
          <li><strong>Inspecciona la zona.</strong> Comprueba si existe acero expuesto, pintura levantada o material suelto.</li>
          <li>
            <strong>Prepara solo el punto afectado.</strong> Lija suavemente únicamente la zona dañada con lija fina
            P320–P400. Elimina la pintura suelta y suaviza el borde del desconchado, sin lijar innecesariamente la
            pintura sana alrededor.
          </li>
          <li><strong>Retira el polvo.</strong> Elimina completamente el polvo de lijado.</li>
          <li><strong>Limpia y seca.</strong> La superficie debe quedar limpia y seca antes de aplicar el esmalte.</li>
          <li>
            <strong>Aplica el esmalte.</strong> Aplica una capa fina del esmalte de retoque correspondiente al color y
            acabado original, preferiblemente con un pincel pequeño. Cubre bien el acero expuesto, especialmente en
            cantos y aristas.
          </li>
          <li>
            <strong>Deja secar.</strong> No manipules la zona durante el secado. Si requiere otra aplicación, respeta el
            tiempo de repintado indicado por el producto utilizado.
          </li>
        </ol>
        <p>
          Oxirón es un esmalte sintético antioxidante directo sobre acero u óxido. Este protocolo localizado no
          incorpora una imprimación previa como requisito general.
        </p>
        <aside className="mw-maintenance-callout" aria-label="Por qué conviene retocar un pequeño desconchado">
          <p className="mw-maintenance-callout__title">¿Por qué conviene retocar un pequeño desconchado?</p>
          <p>
            El esmalte, además del acabado, protege el acero frente a la exposición ambiental. Restaurar un punto
            donde haya quedado metal expuesto ayuda a mantener esa protección y evitar que el daño localizado evolucione.
          </p>
        </aside>
      </section>

      <section className="mw-section" id="corrosion">
        <h2>Acero expuesto y corrosión localizada</h2>
        <h3>Pequeño punto localizado</h3>
        <p>
          Si aparece un punto pequeño y localizado, revisa la zona, elimina el material o la pintura suelta,
          prepara solo ese punto, retira el polvo y retoca con el esmalte adecuado una vez la superficie esté limpia
          y seca.
        </p>
        <h3>Corrosión extensa o difícil de valorar</h3>
        <p>
          Si la corrosión es extensa, recurrente, se encuentra bajo una zona amplia de pintura o presenta una
          degradación importante, no la trates como un pequeño retoque doméstico. Contacta con MetalWolft para
          valorar el estado antes de intervenir.
        </p>
      </section>

      <section className="mw-section" id="obras-posteriores">
        <h2>Protección durante obras posteriores</h2>
        <p>
          Antes de realizar albañilería, sellados, pintura de fachada, cortes o trabajos alrededor de una reja ya
          instalada, protégela para evitar daños innecesarios.
        </p>
        <ul className="mw-list">
          <li>Protege la reja frente a polvo, salpicaduras e impactos.</li>
          <li>Evita la abrasión sobre cantos y aristas.</li>
          <li>No apoyes herramientas o materiales sobre el bastidor.</li>
          <li>Limpia los residuos con medios no agresivos.</li>
        </ul>
        <p>
          Si todavía vas a montar la reja, consulta primero la{" "}
          <Link className="mw-inline-link" href="/instalation-rejas-para-ventanas">guía de instalación y manipulación</Link>.
        </p>
      </section>

      <section className="mw-section" id="preguntas">
        <h2>Preguntas frecuentes</h2>
        <div className="mw-maintenance-faq-list">
          <details className="mw-maintenance-faq-item">
            <summary>¿Necesito imprimación para un pequeño retoque?</summary>
            <p>No como paso general en este protocolo localizado con TITAN Oxirón.</p>
          </details>
          <details className="mw-maintenance-faq-item">
            <summary>¿Puedo limpiar la reja con disolvente?</summary>
            <p>No como método de limpieza ordinaria.</p>
          </details>
          <details className="mw-maintenance-faq-item">
            <summary>¿El acabado efecto forja es rugoso?</summary>
            <p>No. Es un acabado liso.</p>
          </details>
          <details className="mw-maintenance-faq-item">
            <summary>¿Qué hago si el acero queda expuesto?</summary>
            <p>Revisa la zona y restaura la protección con el procedimiento localizado cuando sea un daño pequeño y posterior.</p>
          </details>
          <details className="mw-maintenance-faq-item">
            <summary>¿Qué hago si el daño estaba antes de instalar?</summary>
            <p>No retoques; fotografía la zona y utiliza el formulario de incidencias.</p>
          </details>
        </div>
      </section>

      <section className="mw-section">
        <h2>Consulta nuestros modelos</h2>
        <p>
          Si necesitas revisar un modelo, anclaje o acabado antes de realizar un pedido, puedes volver al catálogo de
          rejas para ventanas.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
            Ver rejas para ventanas
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
