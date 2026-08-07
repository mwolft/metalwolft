import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const article = readFileSync(
  new URL("../app/recepcion-pedidos-revisar-antes-firmar/page.tsx", import.meta.url),
  "utf8"
);
const blog = readFileSync(new URL("./blog.ts", import.meta.url), "utf8");
const shell = readFileSync(
  new URL("../components/blog/BlogArticleShell.tsx", import.meta.url),
  "utf8"
);
const sitemap = readFileSync(new URL("../app/sitemap.ts", import.meta.url), "utf8");

assert.match(blog, /slug: "recepcion-pedidos-revisar-antes-firmar"/);
assert.match(blog, /title: "Recepción de pedidos: qué revisar antes de firmar"/);
assert.match(
  blog,
  /metadataTitle: "Recepción de pedidos: qué revisar antes de firmar \| MetalWolft"/
);
assert.match(
  blog,
  /metadataDescription:\s*"Qué revisar al recibir una reja a medida y cómo actuar si detectas daños en el transporte\. Fotografías, embalaje y pasos para comunicar una incidencia\."/
);
assert.match(blog, /imageAlt: "Recepción de pedidos y revisión de daños"/);

assert.match(article, /export const metadata = buildBlogArticleMetadata\(article\)/);
assert.match(article, /export default function OrderReceptionGuidePage/);
assert.doesNotMatch(article, /["']use client["']/);
assert.match(article, /<h2>Qué revisar al recibir el pedido<\/h2>/);
assert.match(article, /<h2>Si observas daños en el embalaje<\/h2>/);
assert.match(article, /<h2>Qué necesitamos para revisar una incidencia<\/h2>/);
assert.match(article, /plazo\s+máximo de 48 horas/);
assert.match(article, /href="\/contact"/);
assert.match(article, /href="\/politica-devolucion"/);
assert.match(article, /href="\/plazos-entrega-rejas-a-medida"/);
assert.match(article, /href="\/rejas-para-ventanas"/);
assert.doesNotMatch(article, /<h1/);
assert.doesNotMatch(article, /SEUR|reponer sin problemas|reposici[oó]n autom[aá]tica/i);
assert.doesNotMatch(article, /Comentarios|comment-area|WhatsApp|\/api\/posts/i);

assert.match(shell, /<BreadcrumbJsonLd/);
assert.match(shell, /<JsonLd data=\{buildBlogArticleJsonLd\(article\)\} \/>/);
assert.match(shell, /<h1 className="mw-title mw-title--compact">\{article\.title\}<\/h1>/);
assert.match(blog, /"@type": "Article"/);
assert.match(blog, /path: `\/\$\{article\.slug\}`/);

const sitemapEntries = sitemap.match(
  /\{ path: "\/recepcion-pedidos-revisar-antes-firmar", changeFrequency: "monthly", priority: 0\.75 \}/g
);
assert.equal(sitemapEntries?.length, 1);

console.log("Order-reception guide contract assertions passed");
