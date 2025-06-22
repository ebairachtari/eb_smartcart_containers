from bson import ObjectId
from collections import defaultdict
from datetime import datetime

# ----- Επιστροφή του αριθμού παραγγελιών ανά μήνα ----- #
def get_orders_per_month(db, user_id):
    from datetime import datetime
    from collections import defaultdict

    carts_collection = db.carts
    user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

    user_carts = carts_collection.find({
        "user_id": user_obj_id,
        "status": "ordered"
    })

    counts = defaultdict(int)

    for cart in user_carts:
        created_at = cart.get("created_at")
        if not created_at:
            continue
        # Δημιουργούμε key με βάση το έτος-μήνα
        month_key = created_at.strftime("%Y-%m")
        counts[month_key] += 1

    # Ταξινόμηση με βάση την ημερομηνία
    sorted_counts = dict(sorted(
        counts.items(),
        key=lambda item: datetime.strptime(item[0], "%Y-%m")
    ))

    # Επιστρέφουμε λίστα με σωστή σειρά και σωστά labels
    return [{"month": datetime.strptime(month, "%Y-%m").strftime("%b %Y"), "orders": count}
            for month, count in sorted_counts.items()]

# ----- Μέση δαπάνη ανά μήνα ----- #
def get_monthly_spending(db, user_id):
    from datetime import datetime
    from collections import defaultdict

    carts_collection = db.carts
    user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

    # Φέρνω όλα τα ολοκληρωμένα καλάθια του χρήστη
    user_carts = carts_collection.find({
        "user_id": user_obj_id,
        "status": "ordered"
    })

    monthly_prices = defaultdict(list)

    for cart in user_carts:
        created_at = cart.get("created_at")
        price = cart.get("total_price")
        if not created_at or not price:
            continue

        month_key = created_at.strftime("%Y-%m")
        monthly_prices[month_key].append(price)

    # Υπολογισμός μέσου όρου ανά μήνα
    monthly_avg = {
        month: round(sum(prices), 2)
        for month, prices in monthly_prices.items()
    }

    # Ταξινόμηση και μετατροπή σε list of dicts με labels "Jan 2025"
    result = []
    for month_key in sorted(monthly_avg.keys(), key=lambda x: datetime.strptime(x, "%Y-%m")):
        label = datetime.strptime(month_key, "%Y-%m").strftime("%b %Y")
        result.append({"month": label, "spending": monthly_avg[month_key]})

    return result

# ----- Αγαπημένα προϊόντα του χρήστη ----- #
def get_user_favorites(db, current_user):
    cart_ids = [c["_id"] for c in db.carts.find(
        {"user_id": current_user["_id"], "status": "ordered"},
        {"_id": 1}
    )]

    if not cart_ids:
        return {"favorites": []}, 200

    pipeline = [
        {"$match": {"cart_id": {"$in": cart_ids}}},
        {"$group": {"_id": "$product_id", "total": {"$sum": "$quantity"}}},
        {"$sort": {"total": -1}},
        {"$limit": 5}
    ]
    favorites = list(db.cart_items.aggregate(pipeline))

    product_ids = [f["_id"] for f in favorites if f["_id"]]
    products = db.products.find({"_id": {"$in": product_ids}})
    product_map = {p["_id"]: p for p in products}

    result = []
    for fav in favorites:
        prod = product_map.get(fav["_id"])
        if prod:
            result.append({
                "product_id": str(prod["_id"]),
                "name": prod.get("name", ""),
                "image_url": prod.get("image_url", ""),
                "times_bought": fav["total"]
            })

    return {"favorites": result}, 200

# ----- Περιοδικότητα Αγορών ----- #
def get_purchase_frequency(db, user_id):
    carts_collection = db.carts
    user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

    # Φέρνω τα καλάθια του χρήστη με status "ordered"
    user_carts = carts_collection.find({
        "user_id": user_obj_id,
        "status": "ordered"
    }).sort("created_at", 1)  # Ταξινόμηση κατά ημερομηνία (αύξουσα)

    dates = [cart["created_at"] for cart in user_carts if "created_at" in cart]

    # Χρειάζομαι τουλάχιστον 2 ημερομηνίες για να υπολογίσουμε διαφορά
    if len(dates) < 2:
        return {"average_days": None, "message": "Χρειάζονται τουλάχιστον 2 αγορές."}

    # Υπολογισμός διαφορών σε ημέρες μεταξύ διαδοχικών αγορών
    day_diffs = []
    for i in range(1, len(dates)):
        diff = (dates[i] - dates[i - 1]).days
        day_diffs.append(diff)

    # Μέσος όρος
    avg_days = round(sum(day_diffs) / len(day_diffs))

    return {"average_days": avg_days, "total_orders": len(dates)}

#  ----- Έξυπνο καλάθι ----- #
def get_suggested_cart(db, user_id, limit=10): # τα 10 πιο συχνά αγορασμένα προϊόντα
    user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

    # Βρίσκω καλάθια με status "ordered"
    carts = db.carts.find({
        "user_id": user_obj_id,
        "status": "ordered"
    })

    # Εάν δεν υπάρχουν καλάθια, επιστρέφω κενό
    cart_ids = [cart["_id"] for cart in carts]
    if not cart_ids:
        return []

    # Φέρνω cart_items αυτών των καλαθιών
    cart_items = db.cart_items.find({
        "cart_id": {"$in": cart_ids}
    })

    # Μετράω πόσες φορές εμφανίζεται κάθε προϊόν και φτιάχνω ένα λεξικό με τις μετρήσεις
    product_counts = defaultdict(int)

    for item in cart_items:
        product_id = str(item.get("product_id"))
        product_counts[product_id] += 1

    # Ταξινομώ από το πιο συχνό στο λιγότερο συχνό
    sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
    top_product_ids = [pid for pid, _ in sorted_products[:limit]]

    # Φέρνω τις πληροφορίες των προϊόντων
    products = db.products.find({
        "_id": {"$in": [ObjectId(pid) for pid in top_product_ids]}
    })

    # Δημιουργώ το αποτέλεσμα με τα προϊόντα και τις κατηγορίες τους
    result = []
    for p in products:
        category = db.categories.find_one({"_id": p.get("category_id")})
        category_name = category["name"] if category else "Άγνωστη"

        result.append({
            "id": str(p["_id"]),
            "name": p.get("name"),
            "category": category_name,
            "final_price": p.get("final_price")
        })
    return result