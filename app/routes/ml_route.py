from flask import Blueprint, request, jsonify, current_app
from app.middleware.middleware import token_required
from app.services.ml_service import predict_product_purchase,cluster_products_by_basket

ml_bp = Blueprint('ml', __name__, url_prefix='/ml')

#  ----- GET /ml/predict-product – Πρόβλεψη επόμενου προϊόντος ----- #
@ml_bp.route('/predict-product', methods=['GET'])
@token_required
def predict_product(current_user):
    try:
        db = current_app.db
        product_id = request.args.get("product_id")

        if not product_id:
            return jsonify({"success": False, "error": "Λείπει το product_id"}), 400

        result = predict_product_purchase(db, current_user["_id"], product_id)
        return jsonify({"success": True, "data": result})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

#  ----- GET /ml/cluster-products – Clustering προϊόντων ----- #
@ml_bp.route('/cluster-products', methods=['GET'])
@token_required
def cluster_products(current_user):
    try:
        db = current_app.db
        clusters = cluster_products_by_basket(db, current_user["_id"])
        return jsonify({"success": True, "data": clusters})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
