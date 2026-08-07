import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const article = readFileSync(
  new URL("../app/donde-comprar-rejas-leroy-ikea/page.tsx", import.meta.url),
  "utf8"
);
const blog = readFileSync(new URL("./blog.ts", import.meta.url), "utf8");
const shell = readFileSync(
  new URL("../components/blog/BlogArticleShell.tsx", import.meta.url),
  "utf8"
);
const sitemap = readFileSync(new URL("../app/sitemap.ts", import.meta.url), "utf8");

assert.match(blog, /slug: "donde-comprar-rejas-leroy-ikea"/);
assert.match(
  blog,
  /title: "¿Dónde comprar rejas para ventanas\? Soluciones estándar y a medida"/
);
assert.match(blog, /metadataTitle: "¿Dónde comprar rejas para ventanas\? \| MetalWolft"/);
assert.match(
  blog,
  /metadataDescription:\s*"Qué debes comparar al comprar rejas para ventanas: medidas, anclaje, acabado y diferencias entre soluciones estándar y fabricación a medida\."/
);
assert.match(
  blog,
  /imageAlt: "¿Dónde comprar rejas para ventanas\? Ikea, Leroy Merlin o a medida"/
);

assert.match(article, /export const metadata = buildBlogArticleMetadata\(article\)/);
assert.match(article, /export default function BuyingWindowGrillesGuidePage/);
assert.doesNotMatch(article, /["']use client["']/);
assert.match(article, /<h2>Qué debes comparar antes de comprar una reja<\/h2>/);
assert.match(article, /<h2>Soluciones estándar y compra en gran superficie<\/h2>/);
assert.match(article, /<h2>Cuándo tiene sentido una reja fabricada a medida<\/h2>/);
assert.match(article, /<h2>Medidas: estándar o fabricación para tu hueco<\/h2>/);
assert.match(article, /<h2>Instalación y tipo de anclaje<\/h2>/);
assert.match(article, /<h2>Colores y acabados<\/h2>/);
assert.match(article, /<h2>Cómo comparar el precio de forma útil<\/h2>/);
assert.match(article, /<h2>Qué puedes configurar actualmente en MetalWolft<\/h2>/);
assert.match(article, /<h2>Entonces, ¿qué opción elegir\?<\/h2>/);
assert.match(article, /IKEA o Leroy Merlin aparecen de forma\s+habitual/);
assert.match(
  article,
  /La oferta de cada establecimiento puede cambiar, por lo que conviene\s+comprobar las medidas, materiales, sistema de fijación y condiciones del\s+producto concreto antes de comprar\./
);
assert.match(article, /href="\/medir-hueco-rejas-para-ventanas"/);
assert.match(article, /href="\/instalation-rejas-para-ventanas"/);
assert.match(article, /href="\/plazos-entrega-rejas-a-medida"/);
assert.match(article, /href="\/rejas-para-ventanas"/);
assert.match(article, /Ver rejas para ventanas a medida/);
assert.doesNotMatch(article, /<h1/);
assert.doesNotMatch(
  article,
  /seguridad real|m[aá]s segur[ao]|m[aá]s resistente|mejor calidad|dura[n]? d[eé]cadas|pintura permanece intacta|cualquier entorno|anticorrosi[oó]n|no sirven para exterior|torniller[ií]a m[aá]s resistente|cerradura|llave|perfil|grosor/i
);
assert.doesNotMatch(
  article,
  /RelatedProductsCarousel|productos similares|diferencias reales|Comentarios|comment-area|\/api\/posts/i
);

assert.match(shell, /<BreadcrumbJsonLd/);
assert.match(shell, /<JsonLd data=\{buildBlogArticleJsonLd\(article\)\} \/>/);
assert.match(shell, /<h1 className="mw-title mw-title--compact">\{article\.title\}<\/h1>/);
assert.match(blog, /"@type": "Article"/);
assert.match(blog, /path: `\/\$\{article\.slug\}`/);

const sitemapEntries = sitemap.match(
  /\{ path: "\/donde-comprar-rejas-leroy-ikea", changeFrequency: "monthly", priority: 0\.75 \}/g
);
assert.equal(sitemapEntries?.length, 1);

console.log("Buying-guide contract assertions passed");
