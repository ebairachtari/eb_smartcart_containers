from flask import Blueprint, jsonify, current_app, request
from flask_jwt_extended import get_jwt_identity
from app.middleware.middleware import token_required
from bson import ObjectId
from app.services.products_service import (
    get_all_products,
    get_product_by_id,
    search_products
)
from app.services.product_prices_service import get_stored_prices

product_bp = Blueprint('product', __name__)

# GET /products – Λίστα όλων των προϊόντων
@product_bp.route('/products', methods=['GET'])
@token_required
def list_products(current_user):
    db = current_app.db
    result = get_all_products(db)
    return jsonify(result), 200

# GET /products/search – Αναζήτηση προϊόντων
@product_bp.route('/products/search', methods=['GET'])
@token_required
def search(current_user):
    db = current_app.db
    name = request.args.get("name", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "").strip()

    result, error = search_products(db, name, category, sort)
    if error:
        return jsonify({"msg": error}), 404
    return jsonify(result), 200

# GET /products/<id> – Λεπτομέρειες ενός προϊόντος
@product_bp.route('/products/<string:product_id>', methods=['GET'])
@token_required
def get_product(current_user,product_id):
    db = current_app.db
    result, error = get_product_by_id(db, product_id)
    if error:
        return jsonify({"msg": error}), 400
    return jsonify(result), 200

# GET /products/<id>/scrape – Λήψη τιμών από το Scraper
@product_bp.route('/products/<string:product_id>/scrape', methods=['GET'])
@token_required
def get_scraped_prices(current_user, product_id):
    db = current_app.db
    prices, error = get_stored_prices(db, product_id)

    if error:
        return jsonify({"msg": error}), 404

    return jsonify(prices), 200