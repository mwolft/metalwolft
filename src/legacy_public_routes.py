"""Legacy public routing rules for the main website.

Single source of truth for public 301 redirects and 410 gone responses.
These rules apply only to the public website surface, never to business APIs.
"""

REDIRECT_MAP = {
    "/rejas/rejas-para-ventanas-pittsburgh": "/rejas-para-ventanas/reja-fija-pittsburgh",
    "/rejas/rejas-para-ventanas-livingston": "/rejas-para-ventanas/reja-fija-livingston",
    "/rejas/rejas-para-ventanas-lancaster": "/rejas-para-ventanas/reja-fija-lancaster",
    "/rejas/rejas-para-ventanas-essex": "/rejas-para-ventanas/reja-fija-essex",
    "/index.php": "/",
    "/rejas-para-ventanas.php": "/rejas-para-ventanas",
    "/blog/blog-metal-wolft.php": "/blogs",
    "/blog/medir_hueco_rejas_para_ventanas.php": "/medir-hueco-rejas-para-ventanas",
    "/blog/medir-hueco-rejas-para-ventanas.php": "/medir-hueco-rejas-para-ventanas",
    "/blog/instalation-rejas-para-ventanas": "/instalation-rejas-para-ventanas",
    "/blog/instalation-rejas-para-ventanas.php": "/instalation-rejas-para-ventanas",
}


GONE_PATHS = frozenset(
    {
        "/preguntas-frecuentes",
        "/puertas-correderas-metalicas",
        "/faq",
    }
)


# Verified public product paths with an exact Next.js counterpart (phase 2D).
NEXT_PRODUCT_REDIRECT_SLUGS = frozenset({
    "reja-abatible-albany",
    "reja-abatible-cortland",
    "reja-abatible-essex",
    "reja-abatible-idaho",
    "reja-abatible-maryland-para-ventanas",
    "reja-fija-albany",
    "reja-fija-clasica-charleston",
    "reja-fija-cortland",
    "reja-fija-dakota",
    "reja-fija-erie",
    "reja-fija-essex",
    "reja-fija-genesee",
    "reja-fija-idaho",
    "reja-fija-ithaca",
    "reja-fija-lancaster",
    "reja-fija-livingston",
    "reja-fija-luton",
    "reja-fija-maryland",
    "reja-fija-orleans-clasica",
    "reja-fija-pittsburgh",
    "reja-fija-poole",
    "reja-fija-vermont",
    "reja-fija-virginia",
    "reja-mascotas-ohio",
    "reja-puerta-albany",
    "reja-puerta-cortland",
    "reja-puerta-essex",
    "reja-puerta-maryland",
})


# Only routes with an equivalent page in the current Next.js storefront.
# Account, cart, checkout and recovery routes retain the old origin for now.
NEXT_STOREFRONT_REDIRECTS = {
    "/": "/",
    "/blogs": "/blogs",
    "/contact": "/contact",
    "/cambios-politica-cookies": "/cambios-politica-cookies",
    "/cookies-esenciales": "/politica-cookies",
    "/donde-comprar-rejas-leroy-ikea": "/donde-comprar-rejas-leroy-ikea",
    "/formulario-incidencias": "/formulario-incidencias",
    "/informacion-recogida": "/politica-privacidad",
    "/instalation-rejas-para-ventanas": "/instalation-rejas-para-ventanas",
    "/license": "/license",
    "/medir-hueco-rejas-para-ventanas": "/medir-hueco-rejas-para-ventanas",
    "/plazos-entrega-rejas-a-medida": "/plazos-entrega-rejas-a-medida",
    "/politica-cookies": "/politica-cookies",
    "/politica-devolucion": "/politica-devolucion",
    "/politica-privacidad": "/politica-privacidad",
    "/recepcion-pedidos-revisar-antes-firmar": "/recepcion-pedidos-revisar-antes-firmar",
    "/rejas-para-ventanas": "/rejas-para-ventanas",
    "/rejas-para-ventanas-modernas": "/rejas-para-ventanas-modernas",
    "/rejas-para-ventanas-sin-obra": "/rejas-para-ventanas-sin-obra",
}
