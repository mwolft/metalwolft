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
        "Qué comprobar antes de instalar la reja.",
        "Cómo desembalar y proteger el acabado.",
        "El orden correcto para presentar, marcar y fijar.",
        "Revisión final e incidencias antes del montaje."
      ]}
      heroMedia={
        <figure className="mw-media-frame">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="mw-article-hero-image" src={article.image} alt={article.imageAlt} />
        </figure>
      }
    >
      <section className="mw-section mw-installation-toc" aria-labelledby="installation-toc-title">
        <p className="mw-note">Guía paso a paso</p>
        <h2 id="installation-toc-title">Índice de instalación</h2>
        <nav aria-label="Índice de la guía de instalación">
          <ol>
            <li><a href="#antes-de-empezar">Antes de empezar</a></li>
            <li><a href="#revisa-la-reja">Revisa la reja antes de instalar</a></li>
            <li><a href="#desembalaje">Desembalaje y protección del acabado</a></li>
            <li><a href="#manipulacion">Manipulación de la reja</a></li>
            <li><a href="#instalacion">Instalación paso a paso</a></li>
            <li><a href="#anclajes">Diferencias según el anclaje</a></li>
            <li><a href="#revision-final">Revisión final</a></li>
          </ol>
        </nav>
      </section>

      <section className="mw-section" id="antes-de-empezar">
        <h2>Antes de empezar</h2>
        <p>
          Instala la reja con calma y, si sus dimensiones o peso lo aconsejan, con ayuda de otra persona.
          Una buena presentación antes de fijar evita esfuerzos innecesarios y mejora el resultado final.
        </p>
        <p>
          Antes de empezar, identifica qué reja corresponde a cada hueco y ten clara su posición. Si aún no has
          revisado las medidas, consulta nuestra{" "}
          <Link className="mw-inline-link" href="/medir-hueco-rejas-para-ventanas">
            guía para medir el hueco
          </Link>.
        </p>
        <h3>Herramientas y preparación</h3>
        <ul className="mw-list">
          <li>Taladro y broca adecuados al soporte y al anclaje.</li>
          <li>Llave o punta compatible con la tornillería suministrada.</li>
          <li>Rotulador para marcar los puntos de fijación.</li>
          <li>Medio para limpiar el polvo de los taladros.</li>
        </ul>
      </section>

      <section className="mw-section" id="revisa-la-reja">
        <h2>Revisa la reja antes de instalar</h2>
        <p>Antes de retirar todas las protecciones, comprueba que el pedido corresponde con lo solicitado:</p>
        <ul className="mw-list">
          <li>Modelo y medidas.</li>
          <li>Tipo de anclaje.</li>
          <li>Color y acabado con esmalte sintético antioxidante.</li>
          <li>Tornillería incluida, cuando corresponda.</li>
          <li>Estado visible general de la reja y del embalaje.</li>
        </ul>
        <aside className="mw-installation-callout" aria-label="Aviso antes de instalar">
          <p><strong>Si al desembalar observas un golpe, desconchado o posible defecto:</strong> no lo retoques todavía.</p>
          <p>
            Haz fotografías claras, conserva el embalaje y las protecciones cuando corresponda y comunícalo
            mediante el <Link className="mw-inline-link" href="/formulario-incidencias">formulario de incidencias</Link>.
            Puedes consultar también la{" "}
            <Link className="mw-inline-link" href="/recepcion-pedidos-revisar-antes-firmar">guía de recepción</Link>{" "}
            y la <Link className="mw-inline-link" href="/politica-devolucion">política vigente</Link>.
          </p>
        </aside>
      </section>

      <section className="mw-section" id="desembalaje">
        <h2>Desembalaje y protección del acabado</h2>
        <p>
          La reja se entrega protegida para el transporte con film protector, perfiles protectores en U,
          protección en las caras y cartón exterior. Retira las capas con orden para mantener protegidos los
          puntos de apoyo mientras trabajas.
        </p>
        <ol className="mw-steps">
          <li>Retira primero el cartón exterior con cuidado, separándolo de los perfiles protectores.</li>
          <li>Retira solo las protecciones necesarias para poder presentar y trabajar con la reja.</li>
          <li>Mantén el perfil protector inferior durante la presentación y colocación.</li>
          <li>Una vez instalada y correctamente fijada la reja, retira el protector inferior.</li>
          <li>Retira finalmente el film protector.</li>
        </ol>
        <aside className="mw-installation-callout" aria-label="Aviso sobre el protector inferior">
          <p>
            <strong>Mantén el protector inferior hasta el final de la fijación.</strong> Evita que el canto inferior
            del bastidor apoye directamente sobre vierteaguas, suelo, pared u otra superficie dura.
          </p>
        </aside>
      </section>

      <section className="mw-section" id="manipulacion">
        <h2>Cómo manipular la reja</h2>
        <p>
          Los cantos y aristas concentran el contacto en superficies pequeñas. Un golpe, apoyo o arrastre puede
          producir daños localizados en el acabado con esmalte sintético antioxidante si la pieza no se protege
          adecuadamente.
        </p>
        <ul className="mw-list">
          <li>No arrastres la reja.</li>
          <li>Evita golpes y apoyos directos sobre cantos o aristas.</li>
          <li>No utilices el bastidor como palanca.</li>
          <li>No fuerces una reja dentro de un hueco demasiado ajustado.</li>
          <li>Protege especialmente la pieza en cada presentación antes de la fijación definitiva.</li>
          <li>Levanta y desplaza la reja con apoyo suficiente; no la gires sobre una esquina.</li>
        </ul>
      </section>

      <section className="mw-section" id="instalacion">
        <h2>Instalación paso a paso</h2>
        <ol className="mw-steps">
          <li>Presenta la reja en la posición prevista, manteniendo el protector inferior.</li>
          <li>Marca todos los puntos de fijación.</li>
          <li>Retira la reja y perfora con comodidad.</li>
          <li>Limpia el polvo de los taladros.</li>
          <li>Coloca tacos o fijaciones cuando correspondan al sistema y al soporte.</li>
          <li>Vuelve a presentar la reja y comprueba de nuevo su posición.</li>
          <li>Atornilla o fija de forma progresiva, sin forzar el bastidor.</li>
          <li>Coloca tapas o remates de seguridad si el sistema los incorpora.</li>
        </ol>

        <div className="mw-split-media">
          <figure className="mw-media-frame">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562842/rejas-para-ventanas-modernas-2023_mambli.avif"
              alt="Reja para ventana preparada para instalar"
            />
          </figure>
          <figure className="mw-media-frame">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://res.cloudinary.com/dewanllxn/image/upload/v1733562850/rejas-para-ventanas-sin-obra-precio_bps3ec.avif"
              alt="Detalle de una reja para ventana antes de la fijación"
            />
          </figure>
        </div>
      </section>

      <section className="mw-section" id="anclajes">
        <h2>Diferencias según el anclaje</h2>
        <h3>Agujeros interiores</h3>
        <p>
          La fijación se realiza a través de los puntos preparados en el bastidor. La opción estándar utiliza
          tornillos de 80 mm; la opción larga, cuando se ha seleccionado, utiliza tornillos de 150 mm.
        </p>
        <h3>Pletinas</h3>
        <p>
          Presenta las pletinas correctamente apoyadas y marca cada punto antes de perforar. La opción estándar
          utiliza tornillos de 70 mm; la opción larga, cuando se ha seleccionado, utiliza tornillos de 150 mm.
        </p>
        <h3>Garras metálicas</h3>
        <p>
          Este sistema no utiliza tornillería y requiere fijación mediante obra. Las indicaciones de atornillado
          de los apartados anteriores no son aplicables a esta configuración.
        </p>
        <p>
          Si buscas un sistema de fijación para fachada terminada, consulta también nuestras{" "}
          <Link className="mw-inline-link" href="/rejas-para-ventanas-sin-obra">rejas para ventanas sin obra</Link>.
        </p>
      </section>

      <section className="mw-section" id="revision-final">
        <h2>Revisión final después de instalar</h2>
        <ul className="mw-list">
          <li>Comprueba que las fijaciones están correctamente asentadas.</li>
          <li>Revisa aplomo y holguras cuando correspondan.</li>
          <li>Retira el protector inferior y el film protector.</li>
          <li>Limpia el polvo y los restos de instalación.</li>
          <li>Inspecciona visualmente el acabado, especialmente en cantos y aristas.</li>
        </ul>
        <h3>Pequeños roces</h3>
        <p>
          Si durante la instalación se produce un pequeño roce o desconchado localizado, revisa la zona. Si el
          esmalte se ha dañado, especialmente cuando deja el acero expuesto, conviene realizar un retoque para
          restaurar la protección de la superficie.
        </p>
        <p>
          Los pequeños retoques y el mantenimiento tienen un{" "}
          <Link className="mw-inline-link" href="/mantenimiento-acabado-rejas-metalicas">
            procedimiento específico de mantenimiento y retoque
          </Link>. Esta guía se limita a la instalación y a la revisión inicial del producto.
        </p>
      </section>

      <section className="mw-section">
        <h2>Vídeo de apoyo para la instalación</h2>
        <p>Este vídeo resume la secuencia general de montaje para una reja de ventana.</p>
        <video className="mw-video" controls>
          <source
            src="https://res.cloudinary.com/dewanllxn/video/upload/v1733563618/instalacion-rejas-para-ventanas_kcno5b.webm"
            type="video/webm"
          />
        </video>
      </section>

      <section className="mw-section">
        <h2>Posible incidencia, daño durante el montaje o mantenimiento</h2>
        <ul className="mw-list">
          <li><strong>Antes de instalar:</strong> documenta cualquier posible incidencia y utiliza el canal de revisión indicado.</li>
          <li><strong>Durante la manipulación o instalación:</strong> revisa la zona afectada y protege el acabado si es necesario.</li>
          <li><strong>Después de instalar:</strong> aplica el mantenimiento adecuado al estado de la reja y al entorno.</li>
        </ul>
        <div className="mw-actions">
          <Link className="mw-button mw-button--primary" href="/rejas-para-ventanas">
            Ver rejas para ventanas
          </Link>
          <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas-sin-obra">
            Ver opciones sin obra
          </Link>
        </div>
      </section>
    </BlogArticleShell>
  );
}
