from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from bson import ObjectId

def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            db = current_app.db
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return jsonify({"msg": "Δε βρέθηκε ο χρήστης"}), 401
            return fn(user, *args, **kwargs)
        except Exception as e:
            return jsonify({"msg": str(e)}), 401
    return wrapper