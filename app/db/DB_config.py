from pymongo import MongoClient

# Σύνδεση με MongoDB
client = MongoClient("mongodb://mongo:27017")
db = client["smartcart_db"]

# Όλα τα collections
products_collection = db["products"]
categories_collection = db["categories"]
users_collection = db["users"]
carts_collection = db["carts"]
cart_items_collection = db["cart_items"]
