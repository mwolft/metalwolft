from flask import Blueprint, jsonify
from api.models import Products, Categories 
from datetime import datetime, timezone
import logging 

logger = logging.getLogger(__name__)

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/api/seo/home', methods=['GET'])
def home():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Carpintería Metálica Online | 🇪🇸",
        "twitter_description": "Somos expertos en Carpintería Metálica. Fabricamos rejas para ventanas, puertas correderas, vallados metálicos o puertas peatonales.",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png",
        "twitter_image_alt": "Carpintería Metálica Online",
        "title": "Carpintería Metálica Online | 🇪🇸",
        "description": "Somos expertos en Carpintería Metálica. Fabricamos rejas para ventanas, puertas correderas, vallados metálicos o puertas peatonales.",
        "keywords": "rejas para ventanas, puertas Metálicas, vallados exteriores, carpintería de aluminio",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png",
        "og_url": "https://www.metalwolft.com/",
        "og_type": "website",
        "og_locale": "es_ES",
        "og_updated_time": datetime.now(timezone.utc).isoformat(),
        "og_image_type": "image/jpeg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_alt": "Carpintería Metálica Online",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Metal Wolft",
            "url": "https://www.metalwolft.com/",
            "logo": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png",
            "description": "Somos expertos en Carpintería Metálica. Fabricamos rejas para ventanas, puertas correderas, vallados metálicos o puertas peatonales.",
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


@seo_bp.route('/api/seo/<string:category_slug>/<string:product_slug>', methods=['GET'])
def seo_product_new(category_slug, product_slug):
    try:
        category = Categories.query.filter_by(slug=category_slug).first()
        if not category:
            logger.warning(f"SEO: Category not found for slug: {category_slug}")
            return jsonify({"message": "Category not found for SEO"}), 404

        product = Products.query.filter_by(slug=product_slug, categoria_id=category.id).first()
        if not product:
            logger.warning(f"SEO: Product not found for slug: {product_slug} in category: {category_slug}")
            return jsonify({"message": "Product not found for SEO"}), 404

        product_full_url = f"https://www.metalwolft.com/{category.slug}/{product.slug}"

        base_title = f"{product.nombre} – {category.nombre} | Metal Wolft"
        title = base_title[:60]

        base_description = f"Descubre {product.nombre}, una {product.descripcion}"
        description = (base_description[:137] + "...") if len(base_description) > 140 else base_description

        twitter_description = f"Mira {product.nombre} en Metal Wolft. {product.descripcion}"
        twitter_description = (twitter_description[:137] + "...") if len(twitter_description) > 140 else twitter_description

        og_description = description

        meta = {
            "lang": "es",
            "title": title,
            "description": description,
            "keywords": f"{product.nombre}, {category.nombre}, {product.slug}, rejas, carpintería metálica, precio, online",

            "twitter_card_type": "summary_large_image",
            "twitter_site": "@MetalWolft",
            "twitter_creator": "@MetalWolft",
            "twitter_title": title,
            "twitter_description": twitter_description,
            "twitter_image": product.imagen if product.imagen else "https://placehold.co/1200x630/cccccc/000000?text=Metal+Wolft",
            "twitter_image_alt": f"Imagen de {product.nombre} de Metal Wolft",

            "og_type": "product",
            "og_title": title,
            "og_description": og_description,
            "og_image": product.imagen if product.imagen else "https://placehold.co/1200x630/cccccc/000000?text=Metal+Wolft",
            "og_image_width": "1200",
            "og_image_height": "630",
            "og_image_alt": f"Imagen de {product.nombre} de Metal Wolft",
            "og_image_type": "image/jpeg",
            "og_url": product_full_url,
            "og_site_name": "Metal Wolft",
            "og_locale": "es_ES",
            "og_updated_time": datetime.now(timezone.utc).isoformat(),

            "canonical": product_full_url,
            "robots": "index, follow",
            "theme_color": "#ff324d",

            "json_ld": {
                "@context": "https://schema.org/",
                "@type": "Product",
                "@id": product_full_url,
                "name": product.nombre,
                "image": ([product.imagen] if product.imagen else []) + [img.image_url for img in product.images if img.image_url],
                "description": product.descripcion,
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
                        "returnFees": "https://schema.org/FreeReturn"
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
                        "author": "Cliente verificado",
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
def rejas_para_ventanas():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Rejas para Ventanas Modernas al Mejor Precio",
        "twitter_description": "Descubre rejas para ventanas modernas, abatibles y sin obra. Precios accesibles y modelos exclusivos en hierro y aluminio. ¡Pide tu catálogo hoy!",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/rejas-para-ventanas_nzmi8k.png",
        "twitter_image_alt": "Rejas para ventanas",
        "title": "Rejas para Ventanas Modernas al Mejor Precio",
        "description": "Descubre rejas para ventanas modernas, abatibles y sin obra. Precios accesibles y modelos exclusivos en hierro y aluminio. ¡Pide tu catálogo hoy!",
        "keywords": "rejas para ventanas, rejas modernas, rejas rusticas...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/rejas-para-ventanas_nzmi8k.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/png",
        "og_image_alt": "Rejas para ventanas",
        "og_url": "https://www.metalwolft.com/rejas-para-ventanas",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_updated_time": datetime.now(timezone.utc).isoformat(),
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/rejas-para-ventanas",
        "robots": "index, follow",
        "theme_color": "#ff324d"
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/vallados-metalicos-exteriores', methods=['GET'])
def vallados_metalicos():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Vallados Metálicos: Seguridad y Estilo Exterior",
        "twitter_description": "Descubre nuestra amplia gama de vallados metálicos diseñados para proteger y embellecer tu espacio exterior. ¡Visítanos hoy mismo!",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/vallados-metalicos_vziaoe.png",
        "twitter_image_alt": "vallados metalicos",
        "title": "Vallados Metálicos: Seguridad y Estilo Exterior",
        "description": "Descubre nuestra amplia gama de vallados metálicos diseñados para proteger y embellecer tu espacio exterior. ¡Visítanos hoy mismo!",
        "keywords": "vallados metalicos, tipos de vallados metálicos, cerramientos metalicos exteriores, vallado exterior moderno, valla Metálica, valla metalica jardin, valla Metálica leroy merlin, valla Metálica bricomart, vallas Metálicas baratas, precio valla metalica, valla Metálica bricodepot, vallado metalico, valla metalica precio, vallas metalicas precios",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/vallados-metalicos_vziaoe.png",
        "og_url": "https://www.metalwolft.com/vallados-metalicos-exteriores",
        "og_type": "web",
        "og_locale": "es_ES",
        "og_updated_time": datetime.now(timezone.utc).isoformat(),
        "og_image_type": "image/jpg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_alt": "vallados metalicos",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/vallados-metalicos-exteriores",
        "robots": "index, follow", 
        "theme_color": "#ff324d"
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/puertas-peatonales-metalicas', methods=['GET'])
def puertas_peatonales_metalicas():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Puertas Peatonales Metálicas. Diseños para exteriores.",
        "twitter_description": "Explora nuestras puertas peatonales Metálicas diseñadas para resistir y embellecer tu entrada. ¡Descúbrelas ahora!",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/puertas-metalicas_lu24dj.png",
        "twitter_image_alt": "Puertas Peatonales Metálicas",
        "title": "Puertas Peatonales Metálicas. Diseños para exteriores.",
        "description": "Explora nuestras puertas peatonales Metálicas diseñadas para resistir y embellecer tu entrada. ¡Descúbrelas ahora!",
        "keywords": "puertas peatonales, puerta peatonal exterior, puerta peatonal en puerta de garaje, puerta peatonal automática...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/puertas-metalicas_lu24dj.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "Puertas Peatonales Metálicas",
        "og_url": "https://www.metalwolft.com/puertas-peatonales-metalicas",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_updated_time": datetime.now(timezone.utc).isoformat(),
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/puertas-peatonales-metalicas",
        "robots": "index, follow",
        "theme_color": "#ff324d"
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/puertas-correderas-interiores', methods=['GET'])
def puertas_correderas_interiores():
    meta_data = {
        "title": "Puertas Correderas con Cristal: a medida.",
        "description": "Descubre nuestra gama de puertas correderas interiores diseñadas para embellecer tu espacio interior.",
        "keywords": "puertas correderas con cristal, puertas correderas leroy merlin, puertas correderas de cristal empotradas en tabique, puertas correderas de cristal para baños...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024438/puertas-correderas-interiores_ho9knt.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "puertas correderas interiores",
        "og_url": "https://www.metalwolft.com/puertas-correderas-interiores",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/puertas-correderas-interiores",
        "robots": "index, follow",
        "theme_color": "#ff324d"
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/puertas-correderas-exteriores', methods=['GET'])
def puertas_correderas_exteriores():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Puertas Correderas Exterior: funcionalidad, estilo y confort",
        "twitter_description": "Descubre nuestra gama de puertas correderas exteriores que combinan funcionalidad y estilo, ideales para tu espacio exterior.",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/puertas-correderas-exteriores_acr6ma.png",
        "twitter_image_alt": "puertas correderas exteriores",
        "title": "Puertas Correderas Exterior: funcionalidad, estilo y confort",
        "description": "Descubre nuestra gama de puertas correderas exteriores que combinan funcionalidad y estilo, ideales para tu espacio exterior.",
        "keywords": "puertas correderas exteriores, puerta corredera exterior, puertas correderas chalet exterior, puerta corredera exterior jardin...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/puertas-correderas-exteriores_acr6ma.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "puertas correderas exteriores",
        "og_url": "https://www.metalwolft.com/puertas-correderas-exteriores",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/puertas-correderas-exteriores",
        "robots": "index, follow",
        "theme_color": "#ff324d"
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/cerramientos-de-cocina-con-cristal', methods=['GET'])
def cerramiento_de_cocina_con_cristal():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Cerramientos cocina con cristal",
        "twitter_description": "Descubre nuestra gama de cerramientos de cocina y salon diseñados para embellecer tu espacio interior.",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/cerramientos-de-cocina-con-cristal_nprdml.png",
        "twitter_image_alt": "cerramientos de cocina con cristal",
        "title": "Cerramientos cocina con cristal",
        "description": "Descubre nuestra gama de cerramientos de cocina y salon diseñados para embellecer tu espacio interior.",
        "keywords": "cerramiento cocina con cristal, cerramiento cocina con cristal leroy merlin, cerramiento cocina salon, cerramiento cocina aluminio...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/cerramientos-de-cocina-con-cristal_nprdml.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "cerramientos de cocina con cristal",
        "og_url": "https://www.metalwolft.com/cerramientos-de-cocina-con-cristal",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/cerramientos-de-cocina-con-cristal",
        "robots": "index, follow",
        "theme_color": "#ff324d"
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/blogs', methods=['GET'])
def blog_metal_wolft():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Blog de Metal Wolft: Inspiración y diseño",
        "twitter_description": "Explora nuestro blog dedicado a la herrería y el diseño en metal. Inspiración, consejos y proyectos creativos para elevar la elegancia en tu hogar.",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png",
        "twitter_image_alt": "carpinteria Metálica online",
        "title": "Blog de Metal Wolft: Inspiración y diseño",
        "description": "Explora nuestro blog dedicado a la herrería y el diseño en metal. Inspiración, consejos y proyectos creativos para elevar la elegancia en tu hogar.",
        "keywords": "rejas para ventanas, rejas modernas, rejas rústicas, rejas sin obra, rejas ikea, rejas leroy merlin",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "carpinteria Metálica online",
        "og_url": "https://www.metalwolft.com/blogs",
        "og_type": "website",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/blogs",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Blog",
            "headline": "Blog de Metal Wolft: Inspiración y diseño en metal y madera.",
            "description": "Explora nuestro blog dedicado a la herrería y el diseño en metal. Inspiración, consejos y proyectos creativos para elevar la elegancia en tu hogar.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1749024437/carpinteria-metalica-online_zcr6p0.png",
            "url": "https://www.metalwolft.com/blogs",
            "author": {
                "@type": "Organization",
                "name": "Metal Wolft"
            }
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/instalation-rejas-para-ventanas', methods=['GET'])
def instalation_rejas_para_ventanas():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Instalación de rejas para ventanas sin obra",
        "twitter_description": "Descubre cómo instalar rejas para ventanas de forma sencilla y segura sin necesidad de obra, utilizando tornillos Torx.",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562859/rejas-de-seguridad-para-ventanas-open_w0kfez.png",
        "twitter_image_alt": "Instalación de rejas para ventanas",
        "title": "Instalación de rejas para ventanas sin obra",
        "description": "Descubre cómo instalar rejas para ventanas de forma sencilla y segura sin necesidad de obra, utilizando tornillos Torx.",
        "keywords": "rejas para ventanas, rejas modernas, rejas rústicas, rejas sin obra, rejas ikea, rejas leroy merlin...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562859/rejas-de-seguridad-para-ventanas-open_w0kfez.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/png",
        "og_image_alt": "Instalación de rejas para ventanas",
        "og_url": "https://www.metalwolft.com/instalation-rejas-para-ventanas",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/instalation-rejas-para-ventanas",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "Instalación de rejas para ventanas sin obra",
            "description": "Descubre cómo instalar rejas para ventanas de forma sencilla y segura sin necesidad de obra, utilizando tornillos Torx.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562859/rejas-de-seguridad-para-ventanas-open_w0kfez.png",
            "url": "https://www.metalwolft.com/instalation-rejas-para-ventanas",
            "step": [
                {
                    "@type": "HowToStep",
                    "name": "Preparar herramientas",
                    "text": "Reúne los tornillos Torx y el destornillador correspondiente.",
                    "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562859/rejas-de-seguridad-para-ventanas-open_w0kfez.png"
                },
                {
                    "@type": "HowToStep",
                    "name": "Marcar los puntos de anclaje",
                    "text": "Utiliza la plantilla para marcar los puntos de anclaje en el marco de la ventana.",
                },
                {
                    "@type": "HowToStep",
                    "name": "Fijar la reja",
                    "text": "Asegura la reja al marco utilizando los tornillos Torx y comprueba la estabilidad.",
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
def medir_hueco_rejas_para_ventanas():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Cómo medir el hueco para instalación de rejas",
        "twitter_description": "Descubre cómo medir el hueco para instalar rejas de ventanas de forma sencilla y segura sin necesidad de obra. Guía paso a paso.",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562852/rejas-para-ventanas-open_aoo6nt.avif",
        "twitter_image_alt": "Medición hueco rejas para ventanas",
        "title": "Cómo medir el hueco para instalación de rejas",
        "description": "Descubre cómo medir el hueco para instalar rejas de ventanas de forma sencilla y segura sin necesidad de obra. Guía paso a paso.",
        "keywords": "rejas para ventanas, rejas modernas, rejas rústicas, rejas sin obra, rejas ikea, rejas leroy merlin...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562852/rejas-para-ventanas-open_aoo6nt.avif",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/avif",
        "og_image_alt": "Medición hueco rejas para ventanas",
        "og_url": "https://www.metalwolft.com/medir-hueco-rejas-para-ventanas",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft ",
        "canonical": "https://www.metalwolft.com/medir-hueco-rejas-para-ventanas",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "Medición del hueco para rejas de ventanas",
            "description": "Descubre cómo medir el hueco para instalar rejas de ventanas de forma sencilla y segura sin necesidad de obra. Guía paso a paso.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562852/rejas-para-ventanas-open_aoo6nt.avif",
            "url": "https://www.metalwolft.com/medir-hueco-rejas-para-ventanas",
            "step": [
                {
                    "@type": "HowToStep",
                    "name": "Preparar herramientas",
                    "text": "Reúne una cinta métrica y un lápiz para marcar las medidas.",
                    "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733562852/rejas-para-ventanas-open_aoo6nt.avif"
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
