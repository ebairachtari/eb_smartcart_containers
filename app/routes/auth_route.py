from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity,jwt_required
from app.middleware.middleware import token_required
from app.model.user_model import User
from app.services.auth_service import register_user, login_user

auth_bp = Blueprint('auth', __name__)

# POST /register – Εγγραφή
@auth_bp.route('/register', methods=['POST'])
def register():
    db = current_app.db
    data = request.get_json()
    user = User(**data)

    success, message = register_user(db, user.email, user.password)
    status = 201 if success else 409
    return jsonify({"msg": message}), status

# POST /login – Σύνδεση
# POST /login – Σύνδεση
@auth_bp.route('/login', methods=['POST'])
def login():
    db = current_app.db
    data = request.get_json()
    user = User(**data)

    token, message = login_user(db, user.email, user.password)
    if token:
        # Βρες το user_id από τη βάση
        found_user = db["users"].find_one({"email": user.email})
        user_id = str(found_user["_id"]) if found_user else None

        return jsonify({
            "msg": message,
            "access_token": token,
            "user_id": user_id
        }), 200

    return jsonify({"msg": message}), 401
