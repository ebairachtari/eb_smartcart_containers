from datetime import datetime

# Κατηγορία
def create_category(name):
    return {
        "name": name
    }

# Προϊόν
def create_product(
    name,
    price_efresh=None,
    price_per_unit_efresh=None,
    price_marketin=None,
    price_per_unit_marketin=None,
    final_price=None,
    category_id=None,
    description=None,
    image_url=None,
    nutrition=None,
    scraped_from=None,
    efresh_url=None, 
    marketin_url=None,
    stock=None,        
    created_at=None
):
    return {
        "name": name,
        "price_efresh": price_efresh,
        "price_per_unit_efresh": price_per_unit_efresh,
        "price_marketin": price_marketin,
        "price_per_unit_marketin": price_per_unit_marketin,
        "final_price": final_price,
        "category_id": category_id,
        "description": description,
        "image_url": image_url,
        "nutrition": nutrition,
        "scraped_from": scraped_from or [],
        "efresh_url": efresh_url,
        "marketin_url": marketin_url,
        "stock": stock,
        "created_at": created_at or datetime.now()
    }

# Χρήστης
def create_user(email, password_hash, created_at=None):
    return {
        "email": email,
        "password": password_hash,
        "created_at": created_at or datetime.now()
    }

# Καλάθι
def create_cart(user_id, status="open", created_at=None):
    return {
        "user_id": user_id,
        "status": status,
        "created_at": created_at or datetime.now()
    }

# Προϊόν σε καλάθι
def create_cart_item(cart_id, product_id, quantity, created_at=None):
    return {
        "cart_id": cart_id,
        "product_id": product_id,
        "quantity": quantity,
        "created_at": created_at or datetime.now()
    }
