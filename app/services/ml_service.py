from bson import ObjectId
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans

# ----- Αυτόματη πρόβλεψη επόμενου προϊόντος με ταξινόμηση ----- #
# Αν ένας χρήστης έχει το καλάθι Χ, πόσο πιθανό είναι να αγοράσει και το προϊόν Y;
def predict_product_purchase(db, user_id, target_product_id):
    user_obj_id = ObjectId(user_id)
    target_obj_id = ObjectId(target_product_id)

    # Βίσκω τα καλάθια του χρήστη με κατάσταση "ordered"
    carts = list(db.carts.find({"user_id": user_obj_id, "status": "ordered"}).sort("created_at", 1))

    # Αν ο χρήστης έχει <5 καλάθια, δεν μπορεί να εκπαιδεύσει μοντέλο.
    if len(carts) < 5:
        return {"message": "Μη επαρκές ιστορικό για εκπαίδευση μοντέλου."}

    cart_ids = [c["_id"] for c in carts]

    # Βρίσκω όλα τα cart_items για αυτά τα καλάθια και τα μετατρέπω σε DataFrame
    cart_items = list(db.cart_items.find({"cart_id": {"$in": cart_ids}}))
    df = pd.DataFrame(cart_items)

    # Κάνω την πρόβλεψη αν το προϊόν-στόχος υπάρχει
    df["has_target"] = df["product_id"].apply(lambda pid: pid == target_obj_id)
    targets = df.groupby("cart_id")["has_target"].max().astype(int)

    # Φτιάχνω χαρακτηριστικά για κάθε καλάθι 
    features = df.groupby("cart_id").agg({
        "product_id": "count",
        "quantity": "sum"
    }).rename(columns={"product_id": "product_count", "quantity": "total_quantity"})

    full_data = features.join(targets)

    # Εκπαιδεύω μοντέλο ταξινόμησης
    X = full_data[["product_count", "total_quantity"]]
    y = full_data["has_target"]
    X_train, _, y_train, _ = train_test_split(X, y, random_state=42)

    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Παίρνω το ΤΕΛΕΥΤΑΙΟ καλάθι
    latest_cart_id = cart_ids[-1]
    latest_cart_data = full_data.loc[latest_cart_id]
    new_input = pd.DataFrame([latest_cart_data[["product_count", "total_quantity"]]])

    # Πρόβλεψη
    prediction = model.predict(new_input)[0]
    probability = round(model.predict_proba(new_input)[0][1], 2)

    return {
        "prediction": int(prediction),
        "probability": probability,
        "note": f"Η πρόβλεψη βασίστηκε στο πιο πρόσφατο καλάθι (προϊόντα: {int(new_input.iloc[0,0])}, ποσότητα: {int(new_input.iloc[0,1])})"
    }


# ----- Clustering προϊόντων με βάση κοινή εμφάνιση σε καλάθια ----- #
# Αν ένας χρήστης αγοράζει το προϊόν Χ, ποια άλλα προϊόντα αγοράζει συχνά μαζί ο ίδιος χρήστης;
def cluster_products_by_basket(db, user_id, n_clusters=3):
    user_obj_id = ObjectId(user_id)

    # Βρίσκω τα καλάθια του χρήστη
    carts = list(db.carts.find({"user_id": user_obj_id, "status": "ordered"}))
    cart_ids = [c["_id"] for c in carts]

    if len(cart_ids) < 3:
        return {"message": "Δεν υπάρχουν αρκετά καλάθια για clustering."}

    # Βρίσκω όλα τα cart_items για αυτά τα καλάθια
    cart_items = list(db.cart_items.find({"cart_id": {"$in": cart_ids}}))

    # Φτιάχνω πίνακα: καλάθι x προϊόν
    data = []
    for item in cart_items:
        cart_id = str(item["cart_id"])
        product_id = str(item["product_id"])
        data.append({"cart_id": cart_id, "product_id": product_id})

    df = pd.DataFrame(data)

    # Δημιουργία πίνακα συχνότητας προϊόντων ανά καλάθι
    pivot = df.pivot_table(index="cart_id", columns="product_id", aggfunc=len, fill_value=0)

    # Μετατροπή σε πίνακα προϊόντων x καλάθι
    product_matrix = pivot.T

    # Εκπαίδευση μοντέλου KMeans
    model = KMeans(n_clusters=n_clusters, random_state=42)
    product_matrix["cluster"] = model.fit_predict(product_matrix)

    # Βρίσκω τα προϊόντα που ανήκουν σε κάθε cluster
    product_ids = [ObjectId(pid) for pid in product_matrix.index]

    product_docs = db.products.find({
    "_id": {"$in": product_ids},
    "stock": {"$gt": 0}  # ΜΟΝΟ διαθέσιμα
    })
    id_to_info = {
        str(p["_id"]): {
            "id": str(p["_id"]),
            "name": p.get("name", "Άγνωστο"),
            "image_url": p.get("image_url", ""),
            "final_price": p.get("final_price", 0)
        }
        for p in product_docs
}

    # Δημιουργία λεξικού με τα clusters
    clusters = {}
    for pid, row in product_matrix.iterrows():
        cluster_id = int(row["cluster"])
        info = id_to_info.get(pid, {"id": pid, "name": "Άγνωστο"})
        clusters.setdefault(cluster_id, []).append(info)

    return clusters