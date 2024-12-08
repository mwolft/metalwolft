from flask import Blueprint, jsonify


seo_bp = Blueprint('seo', __name__)


@seo_bp.route('/api/seo/home', methods=['GET'])
def home():
    meta_data = {
        "title": "Carpintería Metálica en Ciudad Real | Herrería y Soldador.",
        "description": "Somos expertos en carpintería metálica en Ciudad Real. Fabricamos rejas para ventanas, puertas correderas, vallados metálicos o puertas peatonales.",
        "keywords": "carpintería metálica en Ciudad Real, soldador en ciudad real, herrero en Ciudad Real, herrería en Ciudad Real, rejas para ventanas...",
        "og_image": "https://www.metalwolft.com/assets/images/herrero-soldador-ciudad-real.jpg",
        "og_url": "https://www.metalwolft.com/"
    }
    return jsonify(meta_data)


@seo_bp.route('/api/seo/rejas-para-ventanas', methods=['GET'])
def rejas_para_ventanas():
    meta_data = {
        "title": "10 Modelos Exclusivos - Rejas para Ventanas",
        "description": "Descubre nuestra amplia Colección de Rejas para Ventanas...",
        "keywords": "rejas para ventanas, rejas modernas, rejas rusticas...",
        "og_image": "https://res.cloudinary.com/dewanllxn/image/upload/v1733597610/rejas-para-ventanas_nthmwg.png",
        "og_url": "https://www.metalwolft.com/rejas-para-ventanas",
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
        "title": "Vallados Metálicos: Seguridad y Estilo Exterior",
        "description": "Descubre nuestra amplia gama de vallados metálicos diseñados para proteger y embellecer tu espacio exterior. ¡Visítanos hoy mismo!",
        "keywords": "vallados metalicos, tipos de vallados metálicos, cerramientos metalicos exteriores, vallado exterior moderno, valla metálica...",
        "og_image": "https://www.metalwolft.com/assets/images/vallados-metalicos-open.jpg",
        "og_url": "https://www.metalwolft.com/vallados-metalicos-exteriores"
    }
    return jsonify(meta_data)

@seo_bp.route('/api/seo/puertas-peatonales-metalicas', methods=['GET'])
def puertas_peatonales_metalicas():
    meta_data = {
        "title": "Puertas Peatonales Metálicas. Diseños para exteriores.",
        "description": "Explora nuestras puertas peatonales metálicas diseñadas para resistir y embellecer tu entrada. ¡Descúbrelas ahora!",
        "keywords": "puertas peatonales, puerta peatonal exterior, puerta peatonal en puerta de garaje, puerta peatonal automática...",
        "og_image": "https://www.metalwolft.com/assets/images/puertas-peatonales-open.jpg",
        "og_url": "https://www.metalwolft.com/puertas-peatonales-metalicas"
    }
    return jsonify(meta_data)


@seo_bp.route('/puertas-correderas-interiores')
def puertas_correderas_interiores():
    meta_data = {
        "title": "Puertas Correderas con Cristal: a medida.",
        "description": "Descubre nuestra gama de puertas correderas interiores diseñadas para embellecer tu espacio interior.",
        "keywords": "puertas correderas con cristal, puertas correderas leroy merlin, puertas correderas de cristal empotradas en tabique, puertas correderas de cristal para baños...",
        "og_image": "https://www.metalwolft.com/assets/images/puertas-correderas-interiores/puertas-correderas-interiores-open.jpg",
        "og_url": "https://www.metalwolft.com/puertas-correderas-interiores"
    }
    return render_template("puertas_correderas_interiores.html", **meta_data)


@seo_bp.route('/puertas-correderas-exteriores')
def puertas_correderas_exteriores():
    meta_data = {
        "title": "Puertas Correderas Exterior: funcionalidad, estilo y confort",
        "description": "Descubre nuestra gama de puertas correderas exteriores que combinan funcionalidad y estilo, ideales para tu espacio exterior.",
        "keywords": "puertas correderas exteriores, puerta corredera exterior, puertas correderas chalet exterior, puerta corredera exterior jardin...",
        "og_image": "https://www.metalwolft.com/assets/images/puertas-correderas-open.jpg",
        "og_url": "https://www.metalwolft.com/puertas-correderas-exteriores"
    }
    return render_template("puertas_correderas_exteriores.html", **meta_data)


@seo_bp.route('/cerramiento-de-cocina-con-cristal')
def cerramiento_de_cocina_con_cristal():
    meta_data = {
        "title": "Cerramientos cocina con cristal",
        "description": "Descubre nuestra gama de cerramientos de cocina y salon diseñados para embellecer tu espacio interior.",
        "keywords": "cerramiento cocina con cristal, cerramiento cocina con cristal leroy merlin, cerramiento cocina salon, cerramiento cocina aluminio...",
        "og_image": "https://www.metalwolft.com/assets/images/cerramientos-cocinas/cerramiento-de-cocina-con-cristal-open.jpg",
        "og_url": "https://www.metalwolft.com/cerramiento-de-cocina-con-cristal"
    }
    return render_template("cerramiento_de_cocina_con_cristal.html", **meta_data)


@seo_bp.route('/blogs')
def blog_metal_wolft():
    meta_data = {
        "title": "Blog de Metal Wolft: Inspiración y diseño en metal y madera.",
        "description": "Explora nuestro blog dedicado a la herrería y el diseño en metal. Inspiración, consejos y proyectos creativos para elevar la elegancia en tu hogar.",
        "keywords": "rejas para ventanas, rejas modernas, rejas rústicas, rejas sin obra, rejas ikea, rejas leroy merlin",
        "og_image": "https://www.metalwolft.com/assets/images/blog/rejas-de-seguridad-para-ventanas-open.png",
        "og_url": "https://www.metalwolft.com/blogs"
    }
    return render_template("blogs.html", **meta_data)


@seo_bp.route('/instalation-rejas-para-ventanas')
def instalation_rejas_para_ventanas():
    meta_data = {
        "title": "Instalación de rejas para ventanas sin obra: Tornillo Torx.",
        "description": "Descubre cómo instalar rejas para ventanas de forma sencilla y segura sin necesidad de obra, utilizando tornillos Torx.",
        "keywords": "rejas para ventanas, rejas modernas, rejas rústicas, rejas sin obra, rejas ikea, rejas leroy merlin...",
        "og_image": "https://www.metalwolft.com/assets/images/blog/rejas-de-seguridad-para-ventanas-open.png",
        "og_url": "https://www.metalwolft.com/instalation-rejas-para-ventanas"
    }
    return render_template("instalation_rejas_para_ventanas.html", **meta_data)

@seo_bp.route('/medir-hueco-rejas-para-ventanas')
def medir_hueco_rejas_para_ventanas():
    meta_data = {
        "title": "Medición del hueco de rejas para ventanas sin obra.",
        "description": "Descubre cómo medir el hueco para instalar rejas de ventanas de forma sencilla y segura sin necesidad de obra. Guía paso a paso.",
        "keywords": "rejas para ventanas, rejas modernas, rejas rústicas, rejas sin obra, rejas ikea, rejas leroy merlin...",
        "og_image": "https://www.metalwolft.com/assets/images/blog/rejas-para-ventanas-open.png",
        "og_url": "https://www.metalwolft.com/medir-hueco-rejas-para-ventanas"
    }
    return render_template("medir_hueco_rejas_para_ventanas.html", **meta_data)


@seo_bp.route('/sitemap.xml', methods=['GET'])
def sitemap():
    # Lista de URLs generadas dinámicamente
    urls = []
    for rule in current_app.url_map.iter_rules():
        if "GET" in rule.methods and not rule.arguments:  # Solo rutas sin parámetros
            url = url_for(rule.endpoint, _external=True)
            if "static" not in url:  # Excluir rutas de archivos estáticos
                urls.append(url)

    # Crear el contenido del sitemap XML
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        sitemap_content += f"  <url>\n    <loc>{url}</loc>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
    sitemap_content += '</urlset>'

    # Retornar el contenido del sitemap
    return Response(sitemap_content, mimetype='application/xml')
