from bson import ObjectId

# Επιστροφή αποθηκευμένων τιμών & URLs για ένα προϊόν από τη βάση
def get_stored_prices(db, product_id):

    if not ObjectId.is_valid(product_id):
        return None, "Μη έγκυρο ID προϊόντος."

    product = db["products"].find_one({"_id": ObjectId(product_id)})
    if not product:
        return None, "Το προϊόν δεν βρέθηκε στη βάση."

    return {
        "price_efresh": product.get("price_efresh"),
        "price_per_unit_efresh": product.get("price_per_unit_efresh"),
        "efresh_url": product.get("efresh_url"),
        "price_marketin": product.get("price_marketin"),
        "price_per_unit_marketin": product.get("price_per_unit_marketin"),
        "marketin_url": product.get("marketin_url")
    }, None
