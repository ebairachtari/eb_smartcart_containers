from datetime import datetime
from bson import ObjectId

# Επιστρέφει το προφίλ του χρήστη με στατιστικά
def get_user_profile(db, current_user):
    user_id = current_user["_id"]

    # Βασικά στοιχεία χρήστη
    profile = {
        "email": current_user.get("email"),
        "created_at": current_user.get("created_at")
    }

    # Φέρνω τα καλάθια που έχουν ολοκληρωθεί ΜΟΝΟ
    carts = list(db.carts.find({
        "user_id": user_id,
        "status": {"$in": ["ordered"]}
    }))

    # Πλήθος παραγγελιών
    profile["total_orders"] = len(carts)

    # Ημερομηνία τελευταίας παραγγελίας
    if carts:
        last_cart = max(carts, key=lambda c: c["created_at"])
        profile["last_order_date"] = last_cart["created_at"]
    else:
        profile["last_order_date"] = None

    # Συνολική αξία όλων των παραγγελιών
    total_spent = sum(c.get("total_price", 0) for c in carts)
    profile["total_spent"] = round(total_spent, 2)

    # Εξοικονόμηση αν αγόραζε από e-Fresh ή MarketIn
    total_efresh = sum(c.get("total_price_efresh", 0) for c in carts)
    total_marketin = sum(c.get("total_price_marketin", 0) for c in carts)

    savings_efresh = round(total_efresh - total_spent, 2)
    savings_marketin = round(total_marketin - total_spent, 2)

    profile["saved_vs_efresh"] = savings_efresh
    profile["saved_vs_marketin"] = savings_marketin


    return profile
