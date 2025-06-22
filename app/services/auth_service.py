from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from bson import ObjectId
import datetime

# Εγγραφή χρήστη
def register_user(db, email, password):
    users = db["users"]

    # Έλεγχος αν υπάρχει ήδη χρήστης
    if users.find_one({"email": email}):
        return False, "Ο χρήστης υπάρχει ήδη."

    hashed_password = generate_password_hash(password)

    new_user = {
        "email": email,
        "password": hashed_password,
        "created_at": datetime.datetime.utcnow()
    }

    users.insert_one(new_user)
    return True, "Εγγραφή επιτυχής!"

# Σύνδεση χρήστη και δημιουργία token
def login_user(db, email, password):
    users = db["users"]
    user = users.find_one({"email": email})

    if not user or not check_password_hash(user["password"], password):
        return None, "Μη έγκυρα στοιχεία σύνδεσης."

    token = create_access_token(identity=str(user["_id"]))
    return token, "Σύνδεση επιτυχής!"

