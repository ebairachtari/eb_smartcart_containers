from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime
from app.middleware.middleware import token_required
from app.services.cart_service import (
    get_cart_contents,
    add_or_update_cart_item,
    update_cart_status,
    delete_cart_item,
    delete_cart,
    get_cart_history,
)

cart_bp = Blueprint("cart", __name__)

# GET /cart
@cart_bp.route("/cart", methods=["GET"])
@token_required
def get_user_cart(current_user):
    db = current_app.db
    success, response = get_cart_contents(db, current_user["_id"])
    if success:
        return jsonify(response), 200
    return jsonify({"msg": response}), 404

# POST /cart/items
@cart_bp.route("/cart/items", methods=["POST"])
@token_required
def add_cart_item(current_user):
    db = current_app.db
    data = request.json
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return jsonify({"msg": "product_id is required"}), 400

    success, message = add_or_update_cart_item(db, current_user["_id"], product_id, quantity)
    status_code = 201 if success else 400
    return jsonify({"msg": message}), status_code

# PATCH /cart/items
@cart_bp.route("/cart/items", methods=["PATCH"])
@token_required
def update_cart_item_quantity(current_user):
    db = current_app.db
    data = request.json
    product_id = data.get("product_id")
    action = data.get("action")

    if not product_id or action not in ["increment", "decrement"]:
        return jsonify({"msg": "Απαιτείται product_id και action: 'increment' ή 'decrement'"}), 400

    quantity = 1 if action == "increment" else -1
    success, message = add_or_update_cart_item(db, current_user["_id"], product_id, quantity)
    status_code = 200 if success else 400
    return jsonify({"msg": message}), status_code

# PATCH /cart/ordered
@cart_bp.route("/cart/ordered", methods=["PATCH"])
@token_required
def order_cart(current_user):
    db = current_app.db
    success = update_cart_status(db, current_user["_id"], "ordered")
    return jsonify({"msg": "Το καλάθι ολοκληρώθηκε" if success else "Δεν βρέθηκε ενεργό καλάθι"}), 200 if success else 404

# PATCH /cart/cancelled
@cart_bp.route("/cart/cancelled", methods=["PATCH"])
@token_required
def cancel_cart(current_user):
    db = current_app.db
    cart = db["carts"].find_one({"user_id": current_user["_id"], "status": "open"})

    if not cart:
        return jsonify({"msg": "Δεν βρέθηκε ενεργό καλάθι σε κατάσταση 'open' για ακύρωση."}), 400

    success = update_cart_status(db, current_user["_id"], "cancelled")
    return jsonify({"msg": "Το καλάθι ακυρώθηκε" if success else "Αποτυχία"}), 200 if success else 500

# DELETE /cart/items
@cart_bp.route("/cart/item/<product_id>", methods=["DELETE"])
@token_required
def delete_cart_item_route(current_user, product_id):
    db = current_app.db
    success = delete_cart_item(db, current_user["_id"], product_id)
    if success:
        return jsonify({"msg": "Το προϊόν αφαιρέθηκε από το καλάθι."}), 200
    return jsonify({"msg": "Το προϊόν δεν βρέθηκε ή το καλάθι είναι άδειο."}), 404

# DELETE /cart
@cart_bp.route("/cart", methods=["DELETE"])
@token_required
def delete_whole_cart(current_user):
    db = current_app.db
    cart = db["carts"].find_one({"user_id": current_user["_id"], "status": "open"})

    if not cart:
        return jsonify({"msg": "Το καλάθι δεν μπορεί να διαγραφεί γιατί δεν βρίσκεται σε κατάσταση 'open'."}), 400

    msg, status = delete_cart(db, current_user["_id"])
    return jsonify({"msg": msg}), status

# GET /carts/history
@cart_bp.route("/carts/history", methods=["GET"])
@token_required
def get_cart_history_route(current_user):
    db = current_app.db
    history = get_cart_history(db, current_user["_id"])
    return jsonify({"carts": history}), 200

# POST /cart/clone
@cart_bp.route("/cart/clone", methods=["POST"])
@token_required
def clone_cart(current_user):
    db = current_app.db
    data = request.json
    old_cart_id = data.get("cart_id")

    if not old_cart_id:
        return jsonify({"msg": "cart_id is required"}), 400

    old_cart = db.carts.find_one({"_id": ObjectId(old_cart_id), "user_id": current_user["_id"]})
    if not old_cart:
        return jsonify({"msg": "Δεν βρέθηκε καλάθι για αντιγραφή"}), 404

    # Δημιουργία νέου καλαθιού
    new_cart = {
        "user_id": current_user["_id"],
        "status": "open",
        "created_at": datetime.now(),
        "total_price": 0.0
    }
    new_cart_id = db.carts.insert_one(new_cart).inserted_id

    # Αντιγραφή προϊόντων με scraping τιμές
    old_items = list(db.cart_items.find({"cart_id": old_cart["_id"]}))
    for item in old_items:
        product = db.products.find_one({"_id": item["product_id"]}) or {}
        quantity = item.get("quantity", 1)
        unit_price = item.get("unit_price", 0)

        db.cart_items.insert_one({
            "cart_id": new_cart_id,
            "product_id": item["product_id"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": quantity * unit_price,
            "price_efresh": product.get("price_efresh", 0),
            "price_marketin": product.get("price_marketin", 0),
            "created_at": datetime.now()
        })

    # Ενημέρωση συνολικού ποσού
    from app.services.cart_service import update_cart_total_price
    update_cart_total_price(db, current_user["_id"])

    return jsonify({"msg": "Το καλάθι αντιγράφηκε επιτυχώς"}), 201


    # Ενημέρωση συνολικού κόστους του νέου καλαθιού
    cart_items = list(db.cart_items.find({"cart_id": new_cart_id}))
    total = sum(item["quantity"] * item["unit_price"] for item in cart_items)
    db.carts.update_one({"_id": new_cart_id}, {"$set": {"total_price": total}})

    # Υπολογισμός συνολικών τιμών scraping
    cart_items = list(db.cart_items.find({"cart_id": new_cart_id}))
    total = 0
    total_efresh = 0
    total_marketin = 0

    for item in cart_items:
        qty = item["quantity"]
        unit = item["unit_price"]
        total += qty * unit

        efresh = item.get("price_efresh", 0)
        marketin = item.get("price_marketin", 0)
        total_efresh += qty * efresh
        total_marketin += qty * marketin

    db.carts.update_one({"_id": new_cart_id}, {
        "$set": {
            "total_price": total,
            "total_price_efresh": total_efresh,
            "total_price_marketin": total_marketin
        }
    })   

    return jsonify({"new_cart_id": str(new_cart_id), "msg": "Το καλάθι αντιγράφηκε"}), 201