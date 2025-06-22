from flask import Blueprint, request, jsonify, current_app
from app.middleware.middleware import token_required
from app.services.ai_service import ask_ai

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

# ----- POST /ai/ask – Γενικό ----- #
@ai_bp.route("/ask", methods=["POST"])
@token_required
def ai_ask(current_user):
    try:
        db = current_app.db

        # Διαβάζουμε το σώμα του request (JSON)
        data = request.get_json()
        question = data.get("question", "").strip()
        cart_id = data.get("cart_id")

        # Αν δεν υπάρχει ερώτηση, επιστρέφουμε σφάλμα
        if not question:
            return jsonify({"success": False, "error": "Δεν δόθηκε ερώτηση."}), 400

        # Κλήση στην υπηρεσία AI για να πάρουμε την απάντηση
        answer, metadata = ask_ai(db, question, current_user["_id"], cart_id)

        # Αν υπήρξε σφάλμα κατά την απάντηση
        if metadata and isinstance(metadata, dict) and metadata.get("error"):
            return jsonify({"success": False, "error": metadata["error"]}), 500

        # Επιτυχής απάντηση
        return jsonify({
            "success": True,
            "response": answer,
            **(metadata if isinstance(metadata, dict) else {})
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Σφάλμα διακομιστή: {str(e)}"}), 500
