from flask import Blueprint, current_app 
from datetime import datetime, timezone 
from sqlalchemy.orm import joinedload 
from api.models import db, Products, Categories, Posts 
import os 
import logging
import json 

logger = logging.getLogger(__name__) 


sitemap_bp = Blueprint('sitemap_bp', __name__)


def generate_sitemap_file(app_instance):
    try:
        with app_instance.app_context():
            urls = []
            base_url = "https://www.metalwolft.com" 

            # --- 1. URLs Estáticas ---
            urls.append({
                "loc": f"{base_url}/",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'), 
                "changefreq": "daily",
                "priority": "1.00",
                "image": [{"loc": "https://res.cloudinary.com/dewanllxn/image/upload/v1733817377/herrero-ciudad-real_ndf77e.jpg", "caption": "Carpintería Metálica"}]
            })
            urls.append({
                "loc": f"{base_url}/blogs",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'), 
                "changefreq": "daily",
                "priority": "0.70"
            })
            urls.append({
                "loc": f"{base_url}/medir-hueco-rejas-para-ventanas",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'), 
                "changefreq": "monthly",
                "priority": "0.60"
            })
            urls.append({
                "loc": f"{base_url}/instalation-rejas-para-ventanas",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'), 
                "changefreq": "monthly",
                "priority": "0.60"
            })
            urls.append({
                "loc": f"{base_url}/contact",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'), 
                "changefreq": "yearly",
                "priority": "0.50"
            })
            urls.append({
                "loc": f"{base_url}/politica-privacidad",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                "changefreq": "yearly",
                "priority": "0.30"
            })
            urls.append({
                "loc": f"{base_url}/politica-cookies",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                "changefreq": "yearly",
                "priority": "0.30"
            })
            urls.append({
                "loc": f"{base_url}/informacion-recogida",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                "changefreq": "yearly",
                "priority": "0.30"
            })
            urls.append({
                "loc": f"{base_url}/politica-devolucion",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                "changefreq": "yearly",
                "priority": "0.30"
            })
            urls.append({
                "loc": f"{base_url}/cambios-politica-cookies",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                "changefreq": "yearly",
                "priority": "0.30"
            })
            urls.append({
                "loc": f"{base_url}/license",
                "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                "changefreq": "yearly",
                "priority": "0.20"
            })

            # --- 2. URLs Dinámicas de Categorías ---
            categories = Categories.query.all()
            for category in categories:
                cat_url = f"{base_url}/{category.slug}"
                cat_image_loc = category.image_url if category.image_url else None
                
                urls.append({
                    "loc": cat_url,
                    "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'), 
                    "changefreq": "weekly",
                    "priority": "0.80",
                    "image": [{"loc": cat_image_loc, "caption": category.nombre}] if cat_image_loc else None
                })

            # --- 3. URLs Dinámicas de Productos ---
            products = Products.query.options(joinedload(Products.categoria)).all()
            for product in products:
                if product.categoria and product.categoria.slug:
                    product_url = f"{base_url}/{product.categoria.slug}/{product.slug}"
                    product_images = []
                    if product.imagen:
                        product_images.append({"loc": product.imagen, "caption": product.nombre})
                    for img in product.images: 
                        if img.image_url:
                            product_images.append({"loc": img.image_url, "caption": f"{product.nombre} - Imagen {img.id}"})

                    urls.append({
                        "loc": product_url,
                        "lastmod": datetime.now(timezone.utc).isoformat(timespec='seconds'), 
                        "changefreq": "monthly",
                        "priority": "0.70",
                        "image": product_images if product_images else None
                    })

            # --- 4. URLs Dinámicas de Posts de Blog ---
            posts = Posts.query.all() 
            for post in posts:
                post_url = f"{base_url}/blogs/{post.slug}"
                post_image_loc = post.image_url if post.image_url else None
                urls.append({
                    "loc": post_url,
                    "lastmod": (post.updated_at if post.updated_at else post.created_at).isoformat(timespec='seconds'),
                    "changefreq": "weekly",
                    "priority": "0.60",
                    "image": [{"loc": post_image_loc, "caption": post.title}] if post_image_loc else None
                })


            # --- CONSTRUCCIÓN DEL XML FINAL DEL SITEMAP ---
            xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_output += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'

            for url_info in urls:
                xml_output += '  <url>\n'
                xml_output += f'    <loc>{url_info["loc"]}</loc>\n'
                xml_output += f'    <lastmod>{url_info["lastmod"]}</lastmod>\n'
                xml_output += f'    <changefreq>{url_info["changefreq"]}</changefreq>\n'
                xml_output += f'    <priority>{url_info["priority"]}</priority>\n'
                
                if url_info.get("image"):
                    for img in url_info["image"]:
                        if img and img.get("loc"): 
                            xml_output += '    <image:image>\n'
                            xml_output += f'      <image:loc>{img["loc"]}</image:loc>\n'
                            if img.get("caption"):
                                xml_output += f'      <image:caption>{img["caption"]}</image:caption>\n'
                            xml_output += '    </image:image>\n'
                
                xml_output += '  </url>\n'
            xml_output += '</urlset>'

            sitemap_folder = app_instance.config.get('SITEMAP_FOLDER')
            if not sitemap_folder:
                logger.error("SITEMAP_FOLDER no está configurado en app.config. No se pudo guardar el sitemap.")
                return False

            sitemap_path = os.path.join(sitemap_folder, 'sitemap.xml')
            os.makedirs(sitemap_folder, exist_ok=True) 

            with open(sitemap_path, 'w', encoding='utf-8') as f:
                f.write(xml_output)
            
            logger.info(f"Sitemap generado y guardado en: {sitemap_path}")
            return True # Éxito
    except Exception as e:
        logger.error(f"Error al generar y guardar el sitemap: {str(e)}")
        return False

@sitemap_bp.cli.command("generate")
def generate_sitemap_command():
    if generate_sitemap_file(current_app._get_current_object()):
        print("Sitemap generado correctamente.")
    else:
        print("Error al generar el sitemap.")