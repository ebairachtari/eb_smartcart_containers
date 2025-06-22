from datetime import datetime
from bson import ObjectId

# --- Δημιουργία ή εύρεση "ανοιχτού" καλαθιού για χρήστη - μόνο από το πιο πρόσφατο open καλάθι ---
def get_or_create_cart(db, user_id):
    cart = db.carts.find_one({"user_id": user_id, "status": "open"})
    if cart:
        return cart["_id"]
    result = db.carts.insert_one(
        {"user_id": user_id, "status": "open", "created_at": datetime.now()}
    )
    return result.inserted_id


# --- Επιστροφή περιεχομένων ενεργού καλαθιού - μόνο από το πιο πρόσφατο open καλάθι ---
def get_cart_contents(db, user_id):
    # Εύρεση ενεργού καλαθιού για τον χρήστη
    cart = db.carts.find_one({"user_id": user_id, "status": "open"})
    if not cart:
        return False, "Δεν υπάρχει ενεργό καλάθι."

    # Εύρεση προϊόντων στο καλάθι
    cart_items = list(db.cart_items.find({"cart_id": cart["_id"]}))

    # Συνάρτηση που μετατρέπει το stock σε κείμενο
    def get_availability_text(stock):
        if stock == 0:
            return "Εξαντλημένο"
        elif stock < 20:
            return "Περιορισμένη διαθεσιμότητα"
        return "Διαθέσιμο"

    # Επιστροφή περιεχομένων καλαθιού 
    return True, {
        "cart_id": str(cart["_id"]),
        "status": cart["status"],
        "created_at": cart["created_at"],
        "total_price": cart.get("total_price", 0),
        "total_price_efresh": cart.get("total_price_efresh", 0),
        "total_price_marketin": cart.get("total_price_marketin", 0),
        "items": [
            # Για κάθε item, βρίσκω τα στοιχεία του προϊόντος και φτιάχνω το τελικό dictionary
            (
                lambda product: {
                    "product_id": str(item["product_id"]),
                    "product_name": product.get("name", "Άγνωστο"),
                    "quantity": item.get("quantity", 0),
                    "unit_price": item.get("unit_price", 0),
                    "total_price": item.get("total_price", 0),
                    "stock": product.get("stock", 0),
                    "availability": get_availability_text(product.get("stock", 0)),
                    "image_url": product.get("image_url", "")
                    
                }
            )(db.products.find_one({"_id": item["product_id"]}))
            for item in cart_items
        ]
    }

# --- Προσθήκη ή ενημέρωση προϊόντος στο καλάθι (με τιμές) - μόνο από το πιο πρόσφατο open καλάθι ---
def add_or_update_cart_item(db, user_id, product_id, quantity):
    cart_items = db.cart_items
    products = db.products

    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        return False, "Το προϊόν δεν βρέθηκε."

    # Αν το προϊόν είναι εξαντλημένο, δεν επιτρέπεται η προσθήκη
    if product.get("stock", 0) <= 0:
        return False, "Το προϊόν είναι εξαντλημένο."

    unit_price = product.get("final_price", 0)
    cart_id = get_or_create_cart(db, user_id)
    item = cart_items.find_one({"cart_id": cart_id, "product_id": ObjectId(product_id)})

    if item:
        new_quantity = item["quantity"] + quantity
        if new_quantity > 0:
            cart_items.update_one(
                {"_id": item["_id"]},
                {
                    "$set": {
                        "quantity": new_quantity,
                        "total_price": round(unit_price * new_quantity, 2),
                    }
                },
            )
            update_cart_total_price(db, user_id)
            return True, "Η ποσότητα ενημερώθηκε."
        else:
            cart_items.delete_one({"_id": item["_id"]})
            update_cart_total_price(db, user_id)
            return True, "Το προϊόν αφαιρέθηκε από το καλάθι."
    else:
        if quantity > 0:
            cart_items.insert_one(
                {
                    "cart_id": cart_id,
                    "product_id": ObjectId(product_id),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": round(unit_price * quantity, 2),
                    "image_url": product.get("image_url", ""),
                    "created_at": datetime.now(),
                }
            )
            update_cart_total_price(db, user_id)
            return True, "Το προϊόν προστέθηκε στο καλάθι."
        else:
            return False, "Δεν μπορεί να προστεθεί προϊόν με μηδενική ποσότητα."


# --- Υπολογισμός και ενημέρωση συνολικού κόστους καλαθιού - μόνο από το πιο πρόσφατο open καλάθι ---
def update_cart_total_price(db, user_id):
    cart = db["carts"].find_one({"user_id": user_id, "status": "open"})
    if not cart:
        return

    cart_items = db["cart_items"].find({"cart_id": cart["_id"]})

    total_price = 0.0
    total_efresh = 0.0
    total_marketin = 0.0

    for item in cart_items:
        product = db["products"].find_one({"_id": ObjectId(item["product_id"])})
        if not product:
            continue

        quantity = item.get("quantity", 1)

        final_price = product.get("final_price", 0)
        total_price += final_price * quantity

        efresh_price = product.get("price_efresh", 0)
        marketin_price = product.get("price_marketin", 0)

        total_efresh += efresh_price * quantity
        total_marketin += marketin_price * quantity

    db["carts"].update_one(
        {"_id": cart["_id"]},
        {
            "$set": {
                "total_price": round(total_price, 2),
                "total_price_efresh": round(total_efresh, 2),
                "total_price_marketin": round(total_marketin, 2),
            }
        },
    )

# --- Ενημέρωση status καλαθιού και διαχείριση αποθέματος - όλα τα open καλάθια (ή όλα τα πιο πρόσφατα μαζί, αν ο χρήστης τα έχει αφήσει ανοιχτά) ---
def update_cart_status(db, user_id, status):
    open_carts = list(db.carts.find({"user_id": user_id, "status": "open"}))
    if not open_carts:
        return False

    for cart in open_carts:
        cart_items = db.cart_items.find({"cart_id": cart["_id"]})

        for item in cart_items:
            product_id = item["product_id"]
            quantity = item["quantity"]

            if status == "ordered":
                db.products.update_one({"_id": product_id}, {"$inc": {"stock": -quantity}})

        db.carts.update_one({"_id": cart["_id"]}, {"$set": {"status": status}})

    return True

# --- Διαγραφή ενός προϊόντος από το καλάθι - μόνο από το πιο πρόσφατο open καλάθι --
def delete_cart_item(db, user_id, product_id):
    cart = db.carts.find_one({"user_id": user_id, "status": "open"})
    if not cart:
        return False
    result = db.cart_items.delete_one({
        "cart_id": cart["_id"],
        "product_id": ObjectId(product_id)
    })
    update_cart_total_price(db, user_id)
    return result.deleted_count > 0

# --- Πλήρης διαγραφή καλαθιού και των προϊόντων του ---
def delete_cart(db, user_id):
    carts = list(db.carts.find({"user_id": user_id, "status": "open"}))
    if not carts:
        return "Δεν υπάρχει ενεργό καλάθι.", 404

    for cart in carts:
        db.cart_items.delete_many({"cart_id": cart["_id"]})
        db.carts.delete_one({"_id": cart["_id"]})

    return "Το καλάθι διαγράφηκε.", 200


# --- Επιστροφή ιστορικού καλαθιών για χρήστη ---
def get_cart_history(db, user_id):
    user_obj_id = ObjectId(user_id)
    carts = list(db.carts.find({
        "user_id": user_obj_id,
        "status": {"$in": ["ordered", "cancelled"]}
    }).sort("created_at", -1))


    result = []
    for c in carts:
        cart_id = c["_id"]
        cart_items = list(db.cart_items.find({"cart_id": cart_id}))
        items_details = []

        for item in cart_items:
            product = db.products.find_one({"_id": item["product_id"]})
            if product:
                items_details.append({
                    "product_id": str(product["_id"]),
                    "product_name": product.get("name", "Άγνωστο"),
                    "image_url": product.get("image_url", ""),
                    "quantity": item.get("quantity", 1),
                    "unit_price": item.get("unit_price", 0),
                })

        result.append({
            "id": str(cart_id),
            "created_at": c.get("created_at"),
            "status": c.get("status", "unknown"),
            "total_price": sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in items_details),
            "items": items_details
        })

    return result
