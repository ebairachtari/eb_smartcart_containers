from db.DB_config import (
    products_collection,
    categories_collection,
    users_collection,
    carts_collection,
    cart_items_collection
)

# Προϊόντα

def insert_product(product):
    return products_collection.insert_one(product)

def get_all_products():
    return list(products_collection.find())

# Κατηγορίες

def find_category_by_name(name):
    return categories_collection.find_one({"name": name})

def insert_category(category):
    return categories_collection.insert_one(category)

# Χρήστες

def get_all_users():
    return list(users_collection.find())

def insert_user(user):
    return users_collection.insert_one(user)

# Καλάθια

def insert_cart(cart):
    return carts_collection.insert_one(cart)

def get_all_carts():
    return list(carts_collection.find())

# Προϊόντα Καλαθιού

def insert_cart_item(item):
    return cart_items_collection.insert_one(item)

def get_all_cart_items():
    return list(cart_items_collection.find())
