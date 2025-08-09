from io import BytesIO
from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from .invoice_service import render_invoice_pdf

api_invoice_preview = Blueprint('api_invoice_preview', __name__)

@api_invoice_preview.route('/invoices/preview', methods=['POST'])
@jwt_required()
def invoice_preview():
    user = get_jwt_identity()
    if not user or not user.get("is_admin"):
        return {"message": "Forbidden"}, 403

    if not request.is_json:
        return {"message": "Content-Type must be application/json"}, 415

    inv = request.get_json(silent=True)
    if not inv:
        return {"message": "Invalid or empty JSON body"}, 400

    pdf_bytes = render_invoice_pdf(inv)
    return send_file(BytesIO(pdf_bytes),
                     mimetype='application/pdf',
                     as_attachment=False,
                     download_name='invoice_preview.pdf')
