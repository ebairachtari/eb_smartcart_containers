from flask import Blueprint, jsonify, request, current_app
from app.middleware.middleware import token_required
from app.services.products_by_category_service import get_products_by_category

product_by_category_bp = Blueprint("product_by_category", __name__)

# GET /products/by-category?category=Κατηγορία
@product_by_category_bp.route("/products/by-category", methods=["GET"])
@token_required
def by_category(current_user):
    category = request.args.get("category", "").strip()

    if not category:
        return jsonify({"msg": "Η κατηγορία είναι υποχρεωτική"}), 400

    db = current_app.db
    results, error = get_products_by_category(db, category)

    if error:
        return jsonify({"msg": error}), 404

    return jsonify(results), 200
