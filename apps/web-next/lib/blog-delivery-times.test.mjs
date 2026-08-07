import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const article = readFileSync(
  new URL("../app/plazos-entrega-rejas-a-medida/page.tsx", import.meta.url),
  "utf8"
);
const blog = readFileSync(new URL("./blog.ts", import.meta.url), "utf8");
const shell = readFileSync(
  new URL("../components/blog/BlogArticleShell.tsx", import.meta.url),
  "utf8"
);
const sitemap = readFileSync(new URL("../app/sitemap.ts", import.meta.url), "utf8");

assert.match(blog, /slug: "plazos-entrega-rejas-a-medida"/);
assert.match(blog, /title: "¿Cuánto tardan las rejas a medida\?"/);
assert.match(
  blog,
  /metadataTitle: "¿Cuánto tardan las rejas a medida\? \| Plazos de fabricación y entrega"/
);
assert.match(
  blog,
  /metadataDescription:\s*"Consulta la previsión actual de entrega de nuestras rejas a medida y descubre cómo interpretarla antes de realizar tu pedido\."/
);
assert.match(blog, /imageAlt: "Plazos de entrega de rejas para ventanas a medida"/);
assert.match(blog, /title: article\.metadataTitle \|\| article\.title/);
assert.match(
  blog,
  /description: trimTextAtWord\(article\.metadataDescription \|\| article\.description, 155\)/
);

assert.match(article, /export const metadata = buildBlogArticleMetadata\(article\)/);
assert.match(article, /export default async function DeliveryTimesPage/);
assert.match(article, /await fetchDeliveryEstimate\(\)/);
assert.match(article, /<DeliveryEstimate estimate=\{deliveryEstimate\} variant="banner" \/>/);
assert.match(article, /<h2>Consulta la previsión actual de entrega<\/h2>/);
assert.match(article, /href="\/medir-hueco-rejas-para-ventanas"/);
assert.match(article, /href="\/instalation-rejas-para-ventanas"/);
assert.match(article, /href="\/rejas-para-ventanas"/);
assert.doesNotMatch(article, /<h1/);
assert.doesNotMatch(article, /href="\/plazos-entrega-rejas-a-medida"/);
assert.doesNotMatch(article, /20 días naturales|en tiempo real|Comentarios|comment-area/i);

assert.match(shell, /<BreadcrumbJsonLd/);
assert.match(shell, /<JsonLd data=\{buildBlogArticleJsonLd\(article\)\} \/>/);
assert.match(shell, /<h1 className="mw-title mw-title--compact">\{article\.title\}<\/h1>/);
assert.match(blog, /"@type": "Article"/);
assert.match(blog, /mainEntityOfPage: articleUrl/);
assert.match(
  sitemap,
  /\{ path: "\/plazos-entrega-rejas-a-medida", changeFrequency: "monthly", priority: 0\.75 \}/
);

console.log("Delivery-times guide contract assertions passed");
