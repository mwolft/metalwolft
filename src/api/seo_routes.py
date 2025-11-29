from flask import Blueprint, jsonify
from api.models import Products, Categories 
from datetime import datetime, timezone
import logging 

logger = logging.getLogger(__name__)

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/api/seo/home', methods=['GET'])
def seo_home():
    title = "Carpintería Metálica Online"
    description = (
        "Somos expertos en Carpintería Metálica. Fabricamos rejas para ventanas, puertas "
        "correderas, vallados metálicos o puertas peatonales."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png"
    url = "https://www.metalwolft.com/"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "website",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Metal Wolft",
            "url": url,
            "logo": image,
            "description": description,
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Ciudad Real",
                "addressCountry": "ES"
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "+34 634 11 26 04",
                "contactType": "Customer Service"
            }
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/cart', methods=['GET'])
def cart():
    meta_data = {
        "lang": "es",
        "title": "Carrito de compra | Metal Wolft",
        "description": "Revise su carrito de compra, gastos de envío y totales antes de completar su pedido en Metal Wolft.",
        "keywords": "carrito de compra, resumen de pedido, metal wolft",
        "robots": "noindex, nofollow",
        "theme_color": "#ff324d",
        "canonical": None,
        "og_type": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "og_url": None,
        "og_site_name": None,

        "twitter_card_type": None,
        "twitter_title": None,
        "twitter_description": None,
        "twitter_image": None,

        "json_ld": None
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/<string:category_slug>/<string:product_slug>', methods=['GET'])
def seo_product_new(category_slug, product_slug):
    try:
        # 1. Obtener categoría
        category = Categories.query.filter_by(slug=category_slug).first()
        if not category:
            logger.warning(f"SEO: Category not found for slug: {category_slug}")
            return jsonify({"message": "Category not found for SEO"}), 404

        # 2. Obtener producto
        product = Products.query.filter_by(slug=product_slug, categoria_id=category.id).first()
        if not product:
            logger.warning(f"SEO: Product not found for slug: {product_slug} in category: {category_slug}")
            return jsonify({"message": "Product not found for SEO"}), 404

        # 3. URL canonica
        product_full_url = f"https://www.metalwolft.com/{category.slug}/{product.slug}"

        # ============================================================
        #                      TITLE SEO
        # ============================================================
        title = (
            product.titulo_seo
            or f"{product.nombre} | {category.nombre}"
        )

        # Truncado suave a 60 caracteres
        if len(title) > 60:
            title = title[:57] + "..."

        # ============================================================
        #                   META DESCRIPTION SEO
        # ============================================================

        raw_description = (
            product.descripcion_seo
            or product.descripcion
            or ""
        )

        raw_description = raw_description.strip()
        description = raw_description[:152] + "..." if len(raw_description) > 155 else raw_description

        # Twitter usa descripción SEO
        twitter_description = description

        # JSON-LD usa descripción técnica completa
        jsonld_description = (product.descripcion or "").strip()

        # Imagen principal
        main_image = (
            product.imagen
            if product.imagen else
            "https://placehold.co/1200x630/cccccc/000000?text=Metal+Wolft"
        )

        # ============================================================
        #                      META RESULTANTE
        # ============================================================

        meta = {
            "lang": "es",
            "title": title,
            "description": description,
            "keywords": f"{product.nombre}, {category.nombre}, rejas para ventanas, {product.slug}, metal wolft",
            "canonical": product_full_url,
            "robots": "index, follow",
            "theme_color": "#ff324d",

            # ====================== OPEN GRAPH ======================
            "og_type": "product",
            "og_title": title,
            "og_description": description,
            "og_image": main_image,
            "og_image_width": "1200",
            "og_image_height": "630",
            "og_image_alt": title,
            "og_image_type": "image/jpeg",
            "og_url": product_full_url,
            "og_site_name": "Metal Wolft",
            "og_locale": "es_ES",
            "og_updated_time": datetime.now(timezone.utc).isoformat(),

            # ====================== TWITTER ========================
            "twitter_card_type": "summary_large_image",
            "twitter_site": "@MetalWolft",
            "twitter_creator": "@MetalWolft",
            "twitter_title": title,
            "twitter_description": twitter_description,
            "twitter_image": main_image,
            "twitter_image_alt": title,

            # ======================== JSON-LD =======================
            "json_ld": {
                "@context": "https://schema.org/",
                "@type": "Product",
                "@id": product_full_url,
                "name": product.h1_seo or product.nombre,
                "description": jsonld_description,
                "image": (
                    [main_image] +
                    [
                        img.image_url for img in product.images
                        if img.image_url.lower().endswith(('.jpg', '.jpeg', '.png'))
                    ]
                ),
                "sku": product.slug,
                "mpn": str(product.id),
                "brand": {
                    "@type": "Brand",
                    "name": "Metal Wolft"
                },
                "offers": {
                    "@type": "Offer",
                    "priceCurrency": "EUR",
                    "price": product.precio_rebajado or product.precio,
                    "availability": "https://schema.org/InStock",
                    "url": product_full_url,
                    "itemCondition": "https://schema.org/NewCondition",
                    "priceValidUntil": "2025-12-31",
                    "seller": {
                        "@type": "Organization",
                        "name": "Metal Wolft"
                    },
                    "hasMerchantReturnPolicy": {
                        "@type": "MerchantReturnPolicy",
                        "applicableCountry": "ES",
                        "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                        "merchantReturnDays": 7,
                        "returnMethod": "https://schema.org/ReturnByMail",
                        "returnFees": "https://schema.org/FreeReturn",
                        "refundType": "https://schema.org/RefundTypeFullRefund"
                    },
                    "shippingDetails": {
                        "@type": "OfferShippingDetails",
                        "shippingRate": {
                            "@type": "MonetaryAmount",
                            "value": "0.00",
                            "currency": "EUR"
                        },
                        "shippingDestination": {
                            "@type": "DefinedRegion",
                            "addressCountry": "ES"
                        },
                        "deliveryTime": {
                            "@type": "ShippingDeliveryTime",
                            "handlingTime": {
                                "@type": "QuantitativeValue",
                                "minValue": 30,
                                "maxValue": 30,
                                "unitCode": "d"
                            },
                            "transitTime": {
                                "@type": "QuantitativeValue",
                                "minValue": 1,
                                "maxValue": 2,
                                "unitCode": "d"
                            }
                        }
                    }
                },
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.7",
                    "reviewCount": 12
                },
                "review": [
                    {
                        "@type": "Review",
                        "author": {
                            "@type": "Person",
                            "name": "Cliente verificado"
                        },
                        "datePublished": "2024-12-01",
                        "reviewBody": "Reja muy resistente y fácil de instalar. Llegó en buen estado.",
                        "name": "Muy satisfecho con la compra",
                        "reviewRating": {
                            "@type": "Rating",
                            "ratingValue": "5",
                            "bestRating": "5"
                        }
                    }
                ]
            }
        }

        return jsonify(meta)

    except Exception as e:
        logger.error(f"Error en seo_product_new para {category_slug}/{product_slug}: {str(e)}")
        return jsonify({"message": "Error fetching SEO data", "error": str(e)}), 500


@seo_bp.route('/api/seo/rejas-para-ventanas', methods=['GET'])
def seo_rejas_para_ventanas():
    title = "Rejas para Ventanas Modernas al Mejor Precio"
    description = (
        "Descubre rejas para ventanas modernas, abatibles y sin obra. "
        "Precios accesibles y modelos exclusivos en hierro y aluminio. "
        "¡Pide tu catálogo hoy!"
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/rejas-para-ventanas_nzmi8k.png"
    url = "https://www.metalwolft.com/rejas-para-ventanas"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD (opcional para categorías) ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": url,
            "image": image,
            "description": description
        }
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/vallados-metalicos-exteriores', methods=['GET'])
def seo_vallados_metalicos():
    title = "Vallados Metálicos: Seguridad y Estilo Exterior"
    description = (
        "Descubre nuestra amplia gama de vallados metálicos diseñados para proteger "
        "y embellecer tu espacio exterior. ¡Visítanos hoy mismo!"
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/vallados-metalicos_vziaoe.png"
    url = "https://www.metalwolft.com/vallados-metalicos-exteriores"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD (Page SEO) ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": url,
            "image": image,
            "description": description
        }
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/puertas-peatonales-metalicas', methods=['GET'])
def seo_puertas_peatonales_metalicas():
    title = "Puertas Peatonales Metálicas — Diseños para exteriores"
    description = (
        "Explora nuestras puertas peatonales metálicas diseñadas para resistir y "
        "embellecer tu entrada. Modelos modernos, robustos y personalizables."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/puertas-metalicas_lu24dj.png"
    url = "https://www.metalwolft.com/puertas-peatonales-metalicas"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": url,
            "image": image,
            "description": description
        }
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/puertas-correderas-interiores', methods=['GET'])
def seo_puertas_correderas_interiores():
    title = "Puertas Correderas Interiores con Cristal — A medida"
    description = (
        "Descubre nuestra gama de puertas correderas interiores, disponibles con "
        "cristal templado y estructuras metálicas a medida para transformar tus espacios."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024438/puertas-correderas-interiores_ho9knt.png"
    url = "https://www.metalwolft.com/puertas-correderas-interiores"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": url,
            "image": image,
            "description": description
        }
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/puertas-correderas-exteriores', methods=['GET'])
def seo_puertas_correderas_exteriores():
    title = "Puertas Correderas Exteriores — Funcionalidad, estilo y confort"
    description = (
        "Descubre nuestra gama de puertas correderas exteriores que combinan "
        "funcionalidad, estilo y durabilidad. Soluciones ideales para jardines y espacios exteriores."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/puertas-correderas-exteriores_acr6ma.png"
    url = "https://www.metalwolft.com/puertas-correderas-exteriores"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": url,
            "image": image,
            "description": description
        }
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/cerramientos-de-cocina-con-cristal', methods=['GET'])
def seo_cerramientos_de_cocina_con_cristal():
    title = "Cerramientos de Cocina con Cristal — Diseño para interiores"
    description = (
        "Descubre nuestra gama de cerramientos de cocina y salón con cristal templado "
        "y estructura metálica."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/cerramientos-de-cocina-con-cristal_nprdml.png"
    url = "https://www.metalwolft.com/cerramientos-de-cocina-con-cristal"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "url": url,
            "image": image,
            "description": description
        }
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/blogs', methods=['GET'])
def seo_blog_metal_wolft():
    title = "Blog de Metal Wolft — Inspiración y diseño en metal"
    description = (
        "Explora artículos sobre herrería moderna, diseño en metal, ideas decorativas y "
        "proyectos exclusivos de Metal Wolft. Inspiración real para tu hogar."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png"
    url = "https://www.metalwolft.com/blogs"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "blog",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD (Blog global) ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)


@seo_bp.route('/api/seo/instalation-rejas-para-ventanas', methods=['GET'])
def seo_instalation_rejas_para_ventanas():
    title = "Instalación de rejas para ventanas sin obra — Guía paso a paso"
    description = (
        "Aprende cómo instalar rejas para ventanas de forma rápida y segura sin necesidad "
        "de obra. Guía paso a paso utilizando tornillos Torx."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733562859/rejas-de-seguridad-para-ventanas-open_w0kfez.png"
    url = "https://www.metalwolft.com/instalation-rejas-para-ventanas"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD (HowTo) ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "Instalación de rejas para ventanas sin obra",
            "description": description,
            "image": image,
            "url": url,
            "step": [
                {
                    "@type": "HowToStep",
                    "name": "Preparar herramientas",
                    "text": "Reúne los tornillos Torx y el destornillador correspondiente.",
                    "image": image
                },
                {
                    "@type": "HowToStep",
                    "name": "Marcar los puntos de anclaje",
                    "text": "Utiliza la plantilla para marcar los puntos de anclaje en el marco de la ventana."
                },
                {
                    "@type": "HowToStep",
                    "name": "Fijar la reja",
                    "text": "Asegura la reja al marco utilizando los tornillos Torx y comprueba la estabilidad."
                }
            ],
            "author": {
                "@type": "Person",
                "name": "Metal Wolft"
            }
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/medir-hueco-rejas-para-ventanas', methods=['GET'])
def seo_medir_hueco_rejas_para_ventanas():
    title = "Cómo medir el hueco para instalar rejas — Guía paso a paso"
    description = (
        "Aprende cómo medir correctamente el hueco para instalar rejas de ventanas sin obra. "
        "Guía paso a paso fácil y precisa para obtener medidas exactas."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733562852/rejas-para-ventanas-open_aoo6nt.avif"
    url = "https://www.metalwolft.com/medir-hueco-rejas-para-ventanas"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD (HowTo) ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "Cómo medir el hueco para instalar rejas",
            "description": description,
            "image": image,
            "url": url,
            "step": [
                {
                    "@type": "HowToStep",
                    "name": "Preparar herramientas",
                    "text": "Reúne una cinta métrica y un lápiz para marcar las medidas.",
                    "image": image
                },
                {
                    "@type": "HowToStep",
                    "name": "Medir ancho y alto",
                    "text": "Mide el ancho y alto del hueco donde instalarás la reja."
                },
                {
                    "@type": "HowToStep",
                    "name": "Anotar medidas",
                    "text": "Registra las medidas en milímetros para mayor precisión."
                }
            ],
            "author": {
                "@type": "Person",
                "name": "Metal Wolft"
            }
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/plazos-entrega-rejas-a-medida', methods=['GET'])
def seo_plazos_entrega_rejas_a_medida():
    title = "¿Cuánto tardan las rejas a medida? — Plazos de fabricación y envío"
    description = (
        "Descubre cuánto tardamos en fabricar y enviar tus rejas metálicas a medida. "
        "Explicamos los plazos de producción y cómo cambian según la época del año."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1753771759/plazos-de-entrega_xlzcdo.png"
    url = "https://www.metalwolft.com/plazos-entrega-rejas-a-medida"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD (ARTICLE) ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "image": image,
            "url": url,
            "author": {
                "@type": "Organization",
                "name": "Metal Wolft"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url
            },
            "datePublished": "2025-07-29"
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/recepcion-pedidos-revisar-antes-firmar', methods=['GET'])
def seo_recepcion_pedidos_revisar_antes_firmar():
    title = "Recepción de pedidos: revisa antes de firmar y reclama a tiempo"
    description = (
        "Aprende cómo revisar tus pedidos al recibirlos y cómo reclamar daños de transporte "
        "a tiempo. Consejos claros para proteger tu compra."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1757829775/recepcion-pedidos-revisar-antes-firmar_qkkjhb.png"
    url = "https://www.metalwolft.com/recepcion-pedidos-revisar-antes-firmar"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "image": image,
            "url": url,
            "author": {
                "@type": "Organization",
                "name": "Metal Wolft"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url
            },
            "datePublished": "2025-09-14"
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/donde-comprar-rejas-leroy-ikea', methods=['GET'])
def seo_donde_comprar_rejas_leroy_ikea():
    title = "Ikea, Leroy Merlin o a medida: ¿Dónde comprar rejas para ventanas?"
    description = (
        "Comparamos rejas para ventanas de Ikea, Leroy Merlin y rejas fabricadas a medida. "
        "Descubre diferencias reales."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1760079525/donde-comprar-rejas-leroy-ikea_-_copia_ztsabu.png"
    url = "https://www.metalwolft.com/donde-comprar-rejas-leroy-ikea"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "image": image,
            "url": url,
            "author": {
                "@type": "Organization",
                "name": "Metal Wolft"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url
            },
            "datePublished": "2025-10-10"
        }
    }
    return jsonify(meta_data)

@seo_bp.route('/api/seo/rejas-para-ventanas-sin-obra', methods=['GET'])
def seo_rejas_para_ventanas_sin_obra():
    title = "Rejas para ventanas sin obra — Seguras y fáciles de instalar"
    description = (
        "Descubre cómo funcionan las rejas para ventanas sin obra. Una solución segura, "
        "resistente y fabricada a medida sin necesidad de taladrar ni hacer reformas."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1760282425/rejas-para-ventanas-sin-obra-con-tornillos_pvxvxi.png"
    url = "https://www.metalwolft.com/rejas-para-ventanas-sin-obra"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "image": image,
            "url": url,
            "author": {
                "@type": "Organization",
                "name": "Metal Wolft"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url
            },
            "datePublished": "2025-10-10"
        }
    }

    return jsonify(meta_data)

@seo_bp.route('/api/seo/rejas-para-ventanas-modernas', methods=['GET'])
def seo_rejas_para_ventanas_modernas():
    title = "Rejas para ventanas modernas — Diseño, seguridad y fabricación a medida"
    description = (
        "Rejas modernas para ventanas con diseño contemporáneo, seguridad reforzada y "
        "fabricación a medida. Elegancia y resistencia para tu hogar."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1760282424/rejas-para-ventanas-modernas-2026_ntwgur.png"
    url = "https://www.metalwolft.com/rejas-para-ventanas-modernas"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "image": image,
            "url": url,
            "author": {
                "@type": "Organization",
                "name": "Metal Wolft"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://res.cloudinary.com/dewanllxn/image/upload/v1735631180/welder-bot_tqxadc.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url
            },
            "datePublished": "2025-10-10"
        }
    }
    return jsonify(meta_data)


@seo_bp.route("/api/seo/contact", methods=["GET"])
def seo_contact():
    title = "Contacto | MetalWolft — Carpintería Metálica Online"
    description = (
        "Ponte en contacto con MetalWolft para consultas, pedidos a medida o soporte. "
        "Estamos disponibles para ayudarte con cualquier proyecto de carpintería metálica."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733562783/puertas-peatonales-metalicas_i5cvxr.avif"
    url = "https://www.metalwolft.com/contact"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "website",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "ContactPage",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)


@seo_bp.route("/api/seo/politica-privacidad", methods=["GET"])
def seo_politica_privacidad():
    title = "Política de Privacidad | MetalWolft"
    description = (
        "Conoce qué datos recopila MetalWolft, cómo se utilizan y qué derechos tienes como usuario "
        "para garantizar la protección de tu información personal."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733562817/vallado-metalico-residencial_zhmusr.avif"
    url = "https://www.metalwolft.com/politica-privacidad"

    meta_data = {
        "lang": "es",
        "theme_color": "#ff324d",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)


@seo_bp.route("/api/seo/politica-cookies", methods=["GET"])
def seo_politica_cookies():
    title = "Política de Cookies | MetalWolft"
    description = (
        "Consulta la Política de Cookies de MetalWolft y descubre qué tipos de cookies utilizamos, "
        "para qué sirven y cómo puedes gestionarlas desde tu navegador."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733562604/cerramiento-cocina-salon_smb1vp.jpg"
    url = "https://www.metalwolft.com/politica-cookies"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)


@seo_bp.route("/api/seo/informacion-recogida", methods=["GET"])
def seo_informacion_recogida():
    title = "Información que Recopilamos | Privacidad del Usuario | MetalWolft"
    description = (
        "Conoce qué información recopilamos en MetalWolft, para qué la usamos y qué derechos tienes "
        "sobre tus datos personales según la normativa de privacidad."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733817377/herrero-ciudad-real_ndf77e.jpg"
    url = "https://www.metalwolft.com/informacion-recogida"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)


@seo_bp.route("/api/seo/politica-devolucion", methods=["GET"])
def seo_politica_devolucion():
    title = "Política de Devoluciones | MetalWolft"
    description = (
        "Revisa las condiciones para cambios y devoluciones en MetalWolft: plazos, requisitos y pasos "
        "necesarios para gestionar cualquier incidencia con tu pedido."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733562747/puertas-correderas-leroy-merlin_rix2yz.avif"
    url = "https://www.metalwolft.com/politica-devolucion"

    meta_data = {
        "lang": "es",
        "theme_color": "#ff324d",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)


@seo_bp.route("/api/seo/cambios-politica-cookies", methods=["GET"])
def seo_cambios_politica_cookies():
    title = "Cambios en la Política de Cookies | MetalWolft"
    description = (
        "Revisa las actualizaciones en la Política de Cookies de MetalWolft. "
        "Mantente informado sobre cambios recientes y cómo gestionamos las tecnologías de seguimiento."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733562604/cerramiento-cocina-salon_smb1vp.jpg"
    url = "https://www.metalwolft.com/cambios-politica-cookies"

    meta_data = {
        "lang": "es",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",
        "theme_color": "#ff324d",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)


@seo_bp.route("/api/seo/license", methods=["GET"])
def seo_license():
    title = "Licencia de Imágenes | MetalWolft"
    description = (
        "Consulta los derechos de autor, permisos y restricciones para el uso de las imágenes de MetalWolft "
        "en medios digitales o impresos."
    )
    image = "https://res.cloudinary.com/dewanllxn/image/upload/v1733817377/herrero-ciudad-real_ndf77e.jpg"
    url = "https://www.metalwolft.com/license"

    meta_data = {
        "lang": "es",
        "theme_color": "#ff324d",

        # --- TITLE & DESCRIPTION ---
        "title": title,
        "description": description,
        "canonical": url,
        "robots": "index, follow",

        # --- OPEN GRAPH ---
        "og_title": title,
        "og_description": description,
        "og_image": image,
        "og_url": url,
        "og_type": "article",
        "og_locale": "es_ES",
        "og_site_name": "Metal Wolft",

        # --- TWITTER ---
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": title,
        "twitter_description": description,
        "twitter_image": image,

        # --- JSON-LD ---
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url,
            "image": image,
            "publisher": {
                "@type": "Organization",
                "name": "Metal Wolft",
                "logo": {
                    "@type": "ImageObject",
                    "url": image
                }
            }
        }
    }

    return jsonify(meta_data)
