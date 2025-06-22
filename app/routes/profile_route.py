from flask import Blueprint, request, jsonify, current_app
from app.middleware.middleware import token_required
from app.services.profile_service import get_user_profile

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET"])
@token_required
def profile(current_user):
    db = current_app.db
    profile = get_user_profile(db, current_user)
    if not profile:
        return jsonify({"msg": "Ο χρήστης δεν βρέθηκε"}), 404
    return jsonify(profile), 200
