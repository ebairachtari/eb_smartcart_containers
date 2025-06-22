from flask import Blueprint, jsonify, current_app
from app.middleware.middleware import token_required
from app.services.analytics_service import get_orders_per_month,get_monthly_spending,get_purchase_frequency,get_suggested_cart, get_user_favorites
from app.routes.cart_route import cart_bp
from bson import ObjectId
from collections import defaultdict

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

# ----- GET /analytics/orders-per-month – Στατιστικά παραγγελιών ανά μήνα ----- #
@analytics_bp.route('/orders-per-month', methods=['GET'])
@cart_bp.route("/cart", methods=["GET"])
@token_required
def orders_per_month(current_user):
    try:
        db = current_app.db
        result = get_orders_per_month(db, current_user["_id"])
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ----- GET /analytics/monthly-spending – Μέση δαπάνη ανά μήνα ----- #
@analytics_bp.route('/monthly-spending', methods=['GET'])
@cart_bp.route("/cart", methods=["GET"])
@token_required
def monthly_spending(current_user):
    try:
        db = current_app.db
        result = get_monthly_spending(db, current_user["_id"])
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ----- GET /analytics/favorites – Προϊόντα που έχει αποθηκεύσει ο χρήστης ως αγαπημένα ----- #
@analytics_bp.route("/favorites", methods=["GET"])
@cart_bp.route("/cart", methods=["GET"])
@token_required
def favorites_route(current_user):
    db = current_app.db
    user = db.users.find_one({"_id": ObjectId(current_user["_id"])})
    return get_user_favorites(db, user)

# ----- GET /analytics/purchase-frequency – Περιοδικότητα αγορών ----- #
@analytics_bp.route('/purchase-frequency', methods=['GET'])
@cart_bp.route("/cart", methods=["GET"])
@token_required
def purchase_frequency(current_user):
    try:
        db = current_app.db
        result = get_purchase_frequency(db, current_user["_id"])
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ----- GET /analytics/suggested-cart – Προτεινόμενα προϊόντα για νέο καλάθι ----- #
@analytics_bp.route('/suggested-cart', methods=['GET'])
@cart_bp.route("/cart", methods=["GET"])
@token_required
def suggested_cart(current_user):
    try:
        db = current_app.db
        result = get_suggested_cart(db, current_user["_id"])
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
