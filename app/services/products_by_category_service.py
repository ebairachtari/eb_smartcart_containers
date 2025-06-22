from bson import ObjectId
import re

# Επιστροφή προϊόντων βάσει ονόματος κατηγορίας
def get_products_by_category(db, category_name):
    categories = db["categories"]
    products = db["products"]

    # Αναζήτηση κατηγορίας (με regex για case-insensitive match)
    category = categories.find_one({
        "name": {"$regex": f"^{re.escape(category_name)}$", "$options": "i"}
    })

    if not category:
        return None, "Η κατηγορία δεν βρέθηκε."

    category_id = category["_id"]

    # Φέρνουμε προϊόντα που ανήκουν σε αυτή την κατηγορία
    results = list(products.find({"category_id": category_id}))

    output = []
    for p in results:
        output.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "final_price": p["final_price"],
            "image_url": p["image_url"],
            "stock": p.get("stock", 0),
            "availability": "Εξαντλημένο" if p.get("stock", 0) == 0 else (
                "Περιορισμένη διαθεσιμότητα" if p.get("stock", 0) < 20 else "Διαθέσιμο"
            )
        })

    return output, None
