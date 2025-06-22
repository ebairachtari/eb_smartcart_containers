from pymongo import MongoClient
import pandas as pd
from sklearn.cluster import KMeans
import joblib

# Σύνδεση με MongoDB
client = MongoClient("mongodb://smartcart_mongo:27017/")
db = client["smartcart_db"]

# Join των carts με τα cart_items
pipeline = [
    {
        "$lookup": {
            "from": "carts",
            "localField": "cart_id",
            "foreignField": "_id",
            "as": "cart_info"
        }
    },
    {"$unwind": "$cart_info"},
    {"$match": {"cart_info.status": "ordered"}},
    {
        "$project": {
            "user_id": "$cart_info.user_id",
            "product_id": 1
        }
    }
]

joined_data = list(db["cart_items"].aggregate(pipeline))
df = pd.DataFrame(joined_data)

# Προετοιμασία basket matrix: user_id × product_id
df["user_id"] = df["user_id"].astype(str)
df["product_id"] = df["product_id"].astype(str)
basket = df.pivot_table(index="user_id", columns="product_id", aggfunc="size", fill_value=0)

# Εκπαίδευση KMeans
model = KMeans(n_clusters=3, random_state=42)
model.fit(basket)

# Αποθήκευση μοντέλου
joblib.dump(model, "model.pkl")
print("Model trained and saved as model.pkl")

