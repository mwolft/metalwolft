import Link from "next/link";
import { BlogArticleShell } from "@/components/blog/BlogArticleShell";
import type { BlogArticle } from "@/lib/blog";
import { buildBlogArticleMetadata, getBlogArticle } from "@/lib/blog";

function getStaticArticle(): BlogArticle {
  const article = getBlogArticle("donde-comprar-rejas-leroy-ikea");

  if (!article) {
    throw new Error("Missing static blog article: donde-comprar-rejas-leroy-ikea");
  }

  return article;
}

const article = getStaticArticle();

export const metadata = buildBlogArticleMetadata(article);

export default function BuyingWindowGrillesGuidePage() {
  return (
    <BlogArticleShell
      article={article}
      keyPoints={[
        "Compara las medidas y la adaptación al hueco antes que el precio aislado.",
        "Comprueba el anclaje, el acabado y qué incluye cada producto.",
        "Verifica siempre la oferta y las condiciones vigentes del establecimiento.",
        "Una fabricación a medida parte de las dimensiones concretas de tu ventana."
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
        <h2>Qué debes comparar antes de comprar una reja</h2>
        <p>
          Esta guía te ayudará a entender qué conviene comparar antes de elegir, sin
          asumir que una opción es adecuada para todos los huecos o necesidades.
        </p>
        <ul className="mw-list">
          <li>Las medidas disponibles y su adaptación al hueco.</li>
          <li>El tipo de anclaje.</li>
          <li>Si el modelo es fijo o abatible.</li>
          <li>El acabado y el color.</li>
          <li>Las condiciones de envío.</li>
          <li>Los elementos incluidos con el producto.</li>
          <li>
            La{" "}
            <Link className="mw-inline-link" href="/plazos-entrega-rejas-a-medida">
              previsión de entrega
            </Link>
            .
          </li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Soluciones estándar y compra en gran superficie</h2>
        <p>
          Las grandes superficies y los comercios generalistas pueden ser uno de los
          primeros lugares que consulta una persona cuando busca una reja para una
          ventana. Por eso, nombres como IKEA o Leroy Merlin aparecen de forma
          habitual en este tipo de búsqueda.
        </p>
        <p>
          La oferta de cada establecimiento puede cambiar, por lo que conviene
          comprobar las medidas, materiales, sistema de fijación y condiciones del
          producto concreto antes de comprar.
        </p>
        <p>
          Al valorar una solución estándar, comprueba que sus dimensiones y
          características sean compatibles con el hueco donde se instalará.
        </p>
      </section>

      <section className="mw-section">
        <h2>Cuándo tiene sentido una reja fabricada a medida</h2>
        <p>Una solución a medida puede resultar adecuada cuando:</p>
        <ul className="mw-list">
          <li>El hueco tiene unas dimensiones concretas.</li>
          <li>Quieres evitar depender de una medida estándar.</li>
          <li>Necesitas elegir entre las opciones de anclaje disponibles.</li>
          <li>Quieres seleccionar el acabado y el color.</li>
          <li>Buscas un modelo concreto dentro del catálogo.</li>
        </ul>
      </section>

      <section className="mw-section">
        <h2>Medidas: estándar o fabricación para tu hueco</h2>
        <p>
          MetalWolft fabrica cada reja según las dimensiones configuradas por el
          cliente, siempre dentro de los límites admitidos para el producto. Medir con
          precisión es fundamental antes de realizar un pedido a medida.
        </p>
        <p>
          Consulta nuestra guía sobre{" "}
          <Link className="mw-inline-link" href="/medir-hueco-rejas-para-ventanas">
            cómo medir correctamente el hueco
          </Link>{" "}
          antes de introducir las dimensiones en el configurador.
        </p>
      </section>

      <section className="mw-section">
        <h2>Instalación y tipo de anclaje</h2>
        <p>
          MetalWolft fabrica y envía la reja, pero no presta servicio de instalación.
          El catálogo dispone de opciones de anclaje como agujeros interiores y,
          cuando corresponda, pletinas.
        </p>
        <p>
          Para conocer el proceso general y preparar el montaje, consulta la{" "}
          <Link className="mw-inline-link" href="/instalation-rejas-para-ventanas">
            guía de instalación de rejas para ventanas
          </Link>
          .
        </p>
      </section>

      <section className="mw-section">
        <h2>Colores y acabados</h2>
        <p>
          El configurador permite elegir entre colores agrupados en dos acabados:
          Satinado liso y Efecto forja. Las opciones disponibles se muestran al
          configurar cada producto.
        </p>
      </section>

      <section className="mw-section">
        <h2>Cómo comparar el precio de forma útil</h2>
        <p>
          Comparar únicamente el precio anunciado puede resultar insuficiente si los
          productos no tienen las mismas dimensiones, el mismo sistema de fijación,
          una configuración equivalente o las mismas condiciones de envío.
        </p>
        <p>
          En MetalWolft, el configurador calcula el precio con los datos del producto y
          de la configuración elegida. Así puedes consultar el importe antes de
          realizar el pedido.
        </p>
      </section>

      <section className="mw-section">
        <h2>Qué puedes configurar actualmente en MetalWolft</h2>
        <ul className="mw-list">
          <li>Las medidas admitidas para el producto.</li>
          <li>El modelo del catálogo.</li>
          <li>El anclaje disponible.</li>
          <li>El color y el acabado.</li>
          <li>La cantidad.</li>
        </ul>
        <p>
          Algunos modelos pueden ser abatibles. Esta característica pertenece al
          modelo elegido y no es una opción independiente para todas las rejas.
        </p>
      </section>

      <section className="mw-section">
        <h2>Entonces, ¿qué opción elegir?</h2>
        <p>
          Si encuentras una solución cuyas medidas y características encajan con tu
          hueco, puede ser suficiente para tus necesidades. Si necesitas que la reja
          se fabrique para unas dimensiones concretas y quieres elegir su
          configuración, una solución a medida permite partir directamente de las
          características de tu ventana.
        </p>
        <p>
          En MetalWolft puedes consultar los modelos disponibles, introducir las
          medidas y configurar tu reja antes de realizar el pedido.
        </p>
        <div className="mw-actions">
          <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
            Ver rejas para ventanas a medida
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
