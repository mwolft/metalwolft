from flask import Blueprint, jsonify


seo_bp = Blueprint('seo', __name__)


@seo_bp.route('/api/seo/home', methods=['GET'])
def home():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Carpintería Metálica Online | 🇪🇸",
        "twitter_description": "Somos expertos en carpintería metálica en Ciudad Real. Fabricamos rejas para ventanas, puertas correderas, vallados metálicos o puertas peatonales.",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
        "twitter_image_alt": "Carpintería metálica en Ciudad Real",
        "title": "Carpintería Metálica Online | 🇪🇸",
        "description": "Somos expertos en carpintería metálica en Ciudad Real. Fabricamos rejas para ventanas, puertas correderas, vallados metálicos o puertas peatonales.",
        "keywords": "carpintería metálica en Ciudad Real, soldador en ciudad real, herrero en Ciudad Real, herrería en Ciudad Real, rejas para ventanas, puertas metálicas, vallados exteriores, carpintería de aluminio...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
        "og_url": "https://www.metalwolft.com/",
        "og_type": "website",
        "og_locale": "es_ES",
        "og_updated_time": "2024-12-10T12:00:00",
        "og_image_type": "image/jpeg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_alt": "Carpintería metálica en Ciudad Real",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Metal Wolft",
            "url": "https://www.metalwolft.com/",
            "logo": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/logo-metal-wolft.jpg",
            "description": "Expertos en carpintería metálica en Ciudad Real, fabricamos rejas, puertas y vallados.",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Ciudad Real",
                "addressCountry": "ES"
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "+34 123 456 789",
                "contactType": "Customer Service"
            }
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/rejas-para-ventanas', methods=['GET'])
def rejas_para_ventanas():
    meta_data = {
        "lang": "es",
        "twitter_card_type": "summary_large_image",
        "twitter_site": "@MetalWolft",
        "twitter_creator": "@MetalWolft",
        "twitter_title": "Rejas para Ventanas Modernas al Mejor Precio",
        "twitter_description": "Descubre rejas para ventanas modernas, abatibles y sin obra. Precios accesibles y modelos exclusivos en hierro y aluminio. ¡Pide tu catálogo hoy!",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821800/rejas-para-ventanas_opusgz.png",
        "twitter_image_alt": "Rejas para ventanas",
        "title": "Rejas para Ventanas Modernas al Mejor Precio",
        "description": "Descubre rejas para ventanas modernas, abatibles y sin obra. Precios accesibles y modelos exclusivos en hierro y aluminio. ¡Pide tu catálogo hoy!",
        "keywords": "rejas para ventanas, rejas modernas, rejas rusticas...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821800/rejas-para-ventanas_opusgz.png",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/png",
        "og_image_alt": "Rejas para ventanas",
        "og_url": "https://www.metalwolft.com/rejas-para-ventanas",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_updated_time": "2024-12-10T12:00:00",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/rejas-para-ventanas",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": [
            {
                "@context": "https://schema.org/",
                "@type": "ImageObject",
                "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561338/rejas-para-ventanas_qyj5nq.png",
                "creditText": "Rejas para ventanas",
                "creator": { "@type": "Person", "name": "ESSEX" },
                "copyrightNotice": "Metal Wolft",
                "acquireLicensePage": "https://www.metalwolft.com/license",
                "license": "https://www.metalwolft.com/license"
            },
            {
                "@context": "https://schema.org/",
                "@type": "ImageObject",
                "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733560989/rejas-para-ventanas_vwhwjy.avif",
                "creditText": "Rejas para ventanas",
                "creator": { "@type": "Person", "name": "ALBANY" },
                "copyrightNotice": "Metal Wolft",
                "acquireLicensePage": "https://www.metalwolft.com/license",
                "license": "https://www.metalwolft.com/license"
            },
                      {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561486/rejas-para-ventanas_grlync.png",
            "creditText": "Reja para ventana",
            "creator": { "@type": "Person", "name": "LUTON" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561452/rejas-para-ventanas_bjs0kt.png",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "POOLE" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561584/rejas-para-ventanas_d8ojmp.avif",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "DELHI" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561547/rejas-para-ventanas_agh7r0.png",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "ERIE" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561465/rejas-para-ventanas_suhqkg.png",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "PITTSBURGH" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561500/rejas-para-ventanas_fzz2wp.png",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "LANCASTER" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561600/rejas-para-ventanas_c9ctly.png",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "CORTLAND" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561562/rejas-para-ventanas_ybx4oj.avif",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "GENESEE" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          },
          {
            "@context": "https://schema.org/",
            "@type": "ImageObject",
            "contentUrl": "https://res.cloudinary.com/dewanllxn/image/upload/v1733561526/rejas-para-ventanas_kkeagu.png",
            "creditText": "Rejas para ventanas",
            "creator": { "@type": "Person", "name": "LIVINGSTON" },
            "copyrightNotice": "Metal Wolft",
            "acquireLicensePage": "https://www.metalwolft.com/license",
            "license": "https://www.metalwolft.com/license"
          }
        ]
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
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821751/vallados-metalicos-open_lemviq.png",
        "twitter_image_alt": "vallados metalicos",
        "title": "Vallados Metálicos: Seguridad y Estilo Exterior",
        "description": "Descubre nuestra amplia gama de vallados metálicos diseñados para proteger y embellecer tu espacio exterior. ¡Visítanos hoy mismo!",
        "keywords": "vallados metalicos, tipos de vallados metálicos, cerramientos metalicos exteriores, vallado exterior moderno, valla metálica, valla metalica jardin, valla metálica leroy merlin, valla metálica bricomart, vallas metálicas baratas, precio valla metalica, valla metálica bricodepot, vallado metalico, valla metalica precio, vallas metalicas precios",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821751/vallados-metalicos-open_lemviq.png",
        "og_url": "https://www.metalwolft.com/vallados-metalicos-exteriores",
        "og_type": "web",
        "og_locale": "es_ES",
        "og_updated_time": "2024-12-10T12:00:00",
        "og_image_type": "image/jpg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_alt": "vallados metalicos",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/vallados-metalicos-exteriores",
        "robots": "index, follow", 
        "theme_color": "#ff324d",  
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Vallados Metálicos: Seguridad y Estilo Exterior",
            "description": "Descubre nuestra amplia gama de vallados metálicos diseñados para proteger y embellecer tu espacio exterior.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821751/vallados-metalicos-open_lemviq.png",
            "url": "https://www.metalwolft.com/vallados-metalicos-exteriores",
            "author": {
                "@type": "Person",
                "name": "Metal Wolft"
            }
        }
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
        "twitter_description": "Explora nuestras puertas peatonales metálicas diseñadas para resistir y embellecer tu entrada. ¡Descúbrelas ahora!",
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821886/puertas-peatonales-open_e9vsu8.jpg",
        "twitter_image_alt": "Puertas Peatonales Metálicas",
        "title": "Puertas Peatonales Metálicas. Diseños para exteriores.",
        "description": "Explora nuestras puertas peatonales metálicas diseñadas para resistir y embellecer tu entrada. ¡Descúbrelas ahora!",
        "keywords": "puertas peatonales, puerta peatonal exterior, puerta peatonal en puerta de garaje, puerta peatonal automática...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821886/puertas-peatonales-open_e9vsu8.jpg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "Puertas Peatonales Metálicas",
        "og_url": "https://www.metalwolft.com/puertas-peatonales-metalicas",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_updated_time": "2024-12-10T12:00:00",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/puertas-peatonales-metalicas",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Puertas Peatonales Metálicas. Diseños para exteriores.",
            "description": "Explora nuestras puertas peatonales metálicas diseñadas para resistir y embellecer tu entrada. ¡Descúbrelas ahora!",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821886/puertas-peatonales-open_e9vsu8.jpg",
            "url": "https://www.metalwolft.com/puertas-peatonales-metalicas",
            "author": {
                "@type": "Person",
                "name": "Metal Wolft"
            }
        }
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/puertas-correderas-interiores', methods=['GET'])
def puertas_correderas_interiores():
    meta_data = {
        "title": "Puertas Correderas con Cristal: a medida.",
        "description": "Descubre nuestra gama de puertas correderas interiores diseñadas para embellecer tu espacio interior.",
        "keywords": "puertas correderas con cristal, puertas correderas leroy merlin, puertas correderas de cristal empotradas en tabique, puertas correderas de cristal para baños...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "puertas correderas interiores",
        "og_url": "https://www.metalwolft.com/puertas-correderas-interiores",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/puertas-correderas-interiores",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Puertas Correderas con Cristal: a medida.",
            "description": "Descubre nuestra gama de puertas correderas interiores diseñadas para embellecer tu espacio interior.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
            "url": "https://www.metalwolft.com/puertas-correderas-interiores",
            "author": {
                "@type": "Person",
                "name": "Metal Wolft"
            }
        }
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
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733823037/puertas-correderas-open_so6hji.jpg",
        "twitter_image_alt": "puertas correderas exteriores",
        "title": "Puertas Correderas Exterior: funcionalidad, estilo y confort",
        "description": "Descubre nuestra gama de puertas correderas exteriores que combinan funcionalidad y estilo, ideales para tu espacio exterior.",
        "keywords": "puertas correderas exteriores, puerta corredera exterior, puertas correderas chalet exterior, puerta corredera exterior jardin...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733823037/puertas-correderas-open_so6hji.jpg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "puertas correderas exteriores",
        "og_url": "https://www.metalwolft.com/puertas-correderas-exteriores",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/puertas-correderas-exteriores",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Puertas Correderas Exterior: funcionalidad, estilo y confort",
            "description": "Descubre nuestra gama de puertas correderas exteriores que combinan funcionalidad y estilo, ideales para tu espacio exterior.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733823037/puertas-correderas-open_so6hji.jpg",
            "url": "https://www.metalwolft.com/puertas-correderas-exteriores",
            "author": {
                "@type": "Person",
                "name": "Metal Wolft"
            }
        }
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
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
        "twitter_image_alt": "cerramientos de cocina con cristal",
        "title": "Cerramientos cocina con cristal",
        "description": "Descubre nuestra gama de cerramientos de cocina y salon diseñados para embellecer tu espacio interior.",
        "keywords": "cerramiento cocina con cristal, cerramiento cocina con cristal leroy merlin, cerramiento cocina salon, cerramiento cocina aluminio...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "cerramientos de cocina con cristal",
        "og_url": "https://www.metalwolft.com/cerramientos-de-cocina-con-cristal",
        "og_type": "article",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/cerramientos-de-cocina-con-cristal",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Cerramientos cocina con cristal",
            "description": "Descubre nuestra gama de cerramientos de cocina y salon diseñados para embellecer tu espacio interior.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
            "url": "https://www.metalwolft.com/cerramientos-de-cocina-con-cristal",
            "author": {
                "@type": "Person",
                "name": "Metal Wolft"
            }
        }
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
        "twitter_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
        "twitter_image_alt": "herrero soldador ciudad real",
        "title": "Blog de Metal Wolft: Inspiración y diseño",
        "description": "Explora nuestro blog dedicado a la herrería y el diseño en metal. Inspiración, consejos y proyectos creativos para elevar la elegancia en tu hogar.",
        "keywords": "rejas para ventanas, rejas modernas, rejas rústicas, rejas sin obra, rejas ikea, rejas leroy merlin",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
        "og_image_width": "400",
        "og_image_height": "300",
        "og_image_type": "image/jpg",
        "og_image_alt": "herrero soldador ciudad real",
        "og_url": "https://www.metalwolft.com/blogs",
        "og_type": "website",
        "og_locale": "es_ES",
        "og_locale_alternate": "en_US",
        "og_site_name": "Metal Wolft Ciudad Real",
        "canonical": "https://www.metalwolft.com/blogs",
        "robots": "index, follow",
        "theme_color": "#ff324d",
        "json_ld": {
            "@context": "https://schema.org",
            "@type": "Blog",
            "headline": "Blog de Metal Wolft: Inspiración y diseño en metal y madera.",
            "description": "Explora nuestro blog dedicado a la herrería y el diseño en metal. Inspiración, consejos y proyectos creativos para elevar la elegancia en tu hogar.",
            "image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733821952/herrero-soldador-ciudad-real_cc199z.jpg",
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
        "og_site_name": "Metal Wolft Ciudad Real",
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
        "og_site_name": "Metal Wolft Ciudad Real",
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
