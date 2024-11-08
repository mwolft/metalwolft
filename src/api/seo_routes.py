from flask import Blueprint, render_template

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/rejas-para-ventanas')
def rejas_para_ventanas():
    meta_data = {
        "title": "10 Modelos Exclusivos - Rejas para Ventanas",
        "description": "Descubre nuestra amplia Colección de Rejas para Ventanas...",
        "keywords": "rejas para ventanas, rejas modernas, rejas rusticas...",
        "og_image": "https://www.metalwolft.com/assets/images/rejas-para-ventanas.jpg",
        "og_url": "https://www.metalwolft.com/rejas-para-ventanas"
    }
    return render_template("rejas_para_ventanas.html", **meta_data)
