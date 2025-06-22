from bson import ObjectId
import re

# Επιστροφή όλων των προϊόντων
def get_all_products(db):
    products_collection = db["products"]
    categories_collection = db["categories"]

    products = list(products_collection.find({}))
    output = []

    def get_availability_text(stock):
        if stock == 0:
            return "Εξαντλημένο"
        elif stock < 20:
            return "Περιορισμένη διαθεσιμότητα"
        else:
            return "Διαθέσιμο"

    for product in products:
        category = categories_collection.find_one({"_id": product.get("category_id")})
        category_name = category["name"] if category else "Άγνωστη"

        output.append({
            "id": str(product["_id"]),
            "name": product["name"],
            "category": category_name,
            "final_price": product["final_price"],
            "image_url": product["image_url"],
            "stock": product.get("stock", 0),
            "availability": get_availability_text(product.get("stock", 0))
        })

    return output

# Αναζήτηση προϊόντων με φίλτρα και ταξινόμηση
def search_products(db, name_query, category_query, sort_option):
    products_collection = db["products"]
    categories_collection = db["categories"]

    query = {}

    if name_query:
        query["name"] = {"$regex": name_query, "$options": "i"}

    if category_query:
        category = categories_collection.find_one({
            "name": {"$regex": re.escape(category_query), "$options": "i"}
        })
        if category:
            query["category_id"] = category["_id"]
        else:
            return None, "Η κατηγορία δεν βρέθηκε"

    sort_map = {
        "price_asc": ("final_price", 1),
        "price_desc": ("final_price", -1),
        "name_asc": ("name", 1),
        "name_desc": ("name", -1)
    }

    sort_field = sort_map.get(sort_option)

    cursor = products_collection.find(query)
    if sort_field:
        cursor = cursor.sort([sort_field])

    def get_availability_text(stock):
        if stock == 0:
            return "Εξαντλημένο"
        elif stock < 20:
            return "Περιορισμένη διαθεσιμότητα"
        else:
            return "Διαθέσιμο"

    results = []
    for product in cursor:
        category = categories_collection.find_one({"_id": product.get("category_id")})
        category_name = category["name"] if category else "Άγνωστη"

        results.append({
            "id": str(product["_id"]),
            "name": product["name"],
            "category": category_name,
            "final_price": product["final_price"],
            "image_url": product["image_url"],
            "stock": product.get("stock", 0),
            "availability": get_availability_text(product.get("stock", 0))
        })

    return results, None

# Λεπτομέρειες προϊόντος με βάση ID
def get_product_by_id(db, product_id):
    products_collection = db["products"]
    categories_collection = db["categories"]

    if not ObjectId.is_valid(product_id):
        return None, "Μη έγκυρο ID"

    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        return None, "Το προϊόν δεν βρέθηκε"

    category = categories_collection.find_one({"_id": product.get("category_id")})
    category_name = category["name"] if category else "Άγνωστη"

    def get_availability_text(stock):
        if stock == 0:
            return "Εξαντλημένο"
        elif stock < 20:
            return "Περιορισμένη διαθεσιμότητα"
        else:
            return "Διαθέσιμο"

    result = {
        "id": str(product["_id"]),
        "name": product["name"],
        "category": category_name,
        "price_efresh": product.get("price_efresh"),
        "price_marketin": product.get("price_marketin"),
        "final_price": product["final_price"],
        "description": product["description"],
        "image_url": product["image_url"],
        "nutrition": product.get("nutrition"),
        "scraped_from": product.get("scraped_from"),
        "stock": product.get("stock", 0),
        "availability": get_availability_text(product.get("stock", 0))
    }

    return result, None

# Επιστροφή τιμών & URLs από τη βάση
def get_stored_prices(db, product_id):
    if not ObjectId.is_valid(product_id):
        return None, "Μη έγκυρο ID"

    product = db["products"].find_one({"_id": ObjectId(product_id)})
    if not product:
        return None, "Το προϊόν δεν βρέθηκε"

    return {
        "price_efresh": product.get("price_efresh"),
        "price_per_unit_efresh": product.get("price_per_unit_efresh"),
        "efresh_url": product.get("efresh_url"),
        "price_marketin": product.get("price_marketin"),
        "price_per_unit_marketin": product.get("price_per_unit_marketin"),
        "marketin_url": product.get("marketin_url")
    }, None