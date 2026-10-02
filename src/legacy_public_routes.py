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
