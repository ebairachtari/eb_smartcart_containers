from bson import ObjectId
import re
import unicodedata
from openai import OpenAI
from html import escape
from app.services.ml_service import predict_product_purchase, cluster_products_by_basket
from app.services.products_service import get_all_products
from random import shuffle
from collections import defaultdict

# -------------------- Δημιουργία OpenAI client --------------------
client = OpenAI(
    api_key="your-key-here" 
)

# -------------------- Κατηγορίες καθαριστικών --------------------
CLEANING_CATEGORIES = ["Απορρυπαντικά & Μαλακτικά Ρούχων"]

# -------------------- Επιτρεπόμενες για τι να μαγειρέψω --------------------
ALLOWED_CATEGORIES = [
    "Κρέας & Πουλερικά",
    "Ψάρια & Θαλασσινά",
    "Ζυμαρικά & Ρύζι",
    "Κατεψυγμένα Προϊόντα"
]

# -------------------- Επιτρεπόμενες για πρωινό --------------------
BREAKFAST_CATEGORIES = [
    "Γαλακτοκομικά & Γιαούρτια",
    "Μπάρες & Σνακ",
    "Αρτοσκευάσματα",
    "Καφές & Ροφήματα"
]

# -------------------- Βοηθητική συνάρτηση για προθέσεις --------------------
def detect_intent(question):
    q = question.lower()
    intents = set()

    if any(word in q for word in ["συνταγή", "μαγειρέψω", "φαγητό", "γεύμα"]):
        intents.add("recipe")
    if any(word in q for word in ["υγιεινό", "διατροφή", "δίαιτα", "ισορροπημένο"]):
        intents.add("health")
    if any(word in q for word in ["λείπει", "προτείνεις", "τι να πάρω", "συμπληρώσω"]):
        intents.add("suggest")
    if any(word in q for word in ["κοστίζει", "τιμή", "πόσο κάνει"]):
        intents.add("price")
    if any(word in q for word in ["απορρυπαντικό", "καθαριστικό", "μαλακτικό", "ρούχα", "πλυντήριο"]):
        intents.add("cleaning")
    if any(word in q for word in ["πρωινό", "πρωί"]):
        intents.add("breakfast")
    if any(word in q for word in ["ανάλυση", "ανάλυση καλαθιού", "κατανάλωση", "για πόσα γεύματα", "πιο ακριβά προϊόντα"]):
        intents.add("analysis")


    return intents

# -------------------- Βοηθητική συνάρτηση για να ελέγχω αν υπάρχουν σχετικά προϊόντα στο καλάθι του χρήστη για τη συγκεκριμένη πρόθεση --------------------

def has_relevant_products_in_cart(db, cart_id, allowed_category_names):

    if not cart_id:
        return False

    items = db["cart_items"].find({"cart_id": ObjectId(cart_id)})

    for item in items:
        product = db["products"].find_one({"_id": ObjectId(item["product_id"])})
        if not product:
            continue

        category = db["categories"].find_one({"_id": product["category_id"]})
        if category and category["name"] in allowed_category_names:
            return True

    return False

# -------------------- Ανάλυση Καλαθιού -------------------- #
def analyze_cart(db, user_id, cart_id=None):
    from collections import defaultdict

    result_text = ""

    # Βρίσκω το πιο πρόσφατο ανοιχτό καλάθι του χρήστη
    cart = db["carts"].find_one({"user_id": ObjectId(user_id), "status": "open"}, sort=[("created_at", -1)])
    if not cart:
        return "Δεν υπάρχει ανοιχτό καλάθι για ανάλυση."

    items = db["cart_items"].find({"cart_id": cart["_id"]})

    # Ομαδοποιω τα προϊόντα σε δύο βασικές κατηγορίες: Τρόφιμα και Καθαριστικά
    cost_per_major_category = defaultdict(float)
    total_cost = 0.0
    expensive_products = []
    high_quantity_items = 0  # Μετρητής προϊόντων με quantity > 3

    for item in items:
        product = db["products"].find_one({"_id": ObjectId(item["product_id"])})
        if not product:
            continue

        quantity = item.get("quantity", 1)
        price = product.get("final_price", 0)
        subtotal = quantity * price
        total_cost += subtotal

        # Εντοπίζω την κατηγορία του προϊόντος
        category_doc = db["categories"].find_one({"_id": product["category_id"]})
        category_name = category_doc["name"] if category_doc else "Άγνωστη Κατηγορία"

        # Ανήκει στα Καθαριστικά ή στα Τρόφιμα
        if category_name in CLEANING_CATEGORIES:
            major_category = "Καθαριστικά"
        else:
            major_category = "Τρόφιμα"

        # Συγκέντρωση κόστους ανά κύρια κατηγορία
        cost_per_major_category[major_category] += subtotal

        # Καταμέτρηση "υψηλής ποσότητας"
        if quantity >= 3:
            high_quantity_items += 1

        # Προσθήκη στο top expensive list
        expensive_products.append({
            "name": product["name"],
            "price": price,
            "image_url": product.get("image_url", "")
        })

    # ----------- Κόστος ανά Κατηγορία ----------- #
    result_text += "\n\n### 💰 Κόστος ανά Κατηγορία:\n"
    for cat, cost in sorted(cost_per_major_category.items(), key=lambda x: -x[1]):
        result_text += f"- **{cat}**: {cost:.2f}€\n"

    dominant = max(cost_per_major_category.items(), key=lambda x: x[1], default=None)
    if dominant and dominant[1] > 0.6 * total_cost:
        result_text += f"\n📌 Παρατηρείται ότι ξοδεύεις κυρίως σε *{dominant[0]}* αυτή τη φορά.\n"

    # ----------- Πιο Ακριβά Προϊόντα ----------- #
    top_expensive = sorted(expensive_products, key=lambda x: -x["price"])[:3]
    result_text += "\n### 💸 Πιο Ακριβά Προϊόντα:\n"
    for p in top_expensive:
        result_text += f"- {p['name']}: {p['price']:.2f}€\n"

    top_sum = sum(p["price"] for p in top_expensive)
    percentage = (top_sum / total_cost) * 100 if total_cost else 0
    rounded_percentage = round(percentage)

    if rounded_percentage >= 20:
        result_text += f"\n Περίπου το **{rounded_percentage}%** του συνολικού κόστους προέρχεται από αυτά τα προϊόντα.\n"

    # ----------- Έξυπνο Insight για stock προϊόντων ----------- #
    if high_quantity_items >= 2:
        result_text += "\n🛒 *Έχεις προσθέσει αρκετές ποσότητες σε κάποια προϊόντα — πιθανώς για οικογενειακή χρήση ή στοκ!*\n"

    return result_text

# -------------------- Κύρια συνάρτηση AI -------------------- #
def ask_ai(db, question, user_id, cart_id=None):
    from random import shuffle
    from bson import ObjectId

    # ----- Αν δεν υπάρχει ερώτηση -----
    if not question or not question.strip():
        return None, "Δεν δόθηκε ερώτηση για επεξεργασία."

    # ----- Ανίχνευση πρόθεσης του χρήστη (intents) -----
    intents = detect_intent(question)

    # ----- Ανάκτηση όλων των προϊόντων της βάσης -----
    all_products = list(db["products"].find({}))
    cart_products = []
    cart_categories = []
    cart_total = 0.0

    # ----- Αν δεν έχει δοθεί cart_id, βρες το πιο πρόσφατο open -----
    if not cart_id:
        recent = db["carts"].find_one({"user_id": ObjectId(user_id), "status": "open"}, sort=[("created_at", -1)])
        if recent:
            cart_id = str(recent["_id"])

    # ----- Ανάλυση καλαθιού -----
    # Αν υπάρχει καλάθι, φέρε όλα τα προϊόντα του
    if cart_id and ObjectId.is_valid(cart_id):
        cart = db["carts"].find_one({"_id": ObjectId(cart_id)})
        if cart:
            items = db["cart_items"].find({"cart_id": ObjectId(cart_id)})
            for item in items:
                try:
                    product_oid = ObjectId(item["product_id"])
                    product = db["products"].find_one({"_id": product_oid})
                except Exception:
                    continue
                if product:
                    quantity = item["quantity"]
                    price = product.get("final_price", 0)
                    subtotal = round(quantity * price, 2)
                    cart_total += subtotal
                    cart_products.append(
                        f"{product['name']} (ποσότητα: {quantity}, τιμή/τεμ: {price:.2f}€, σύνολο: {subtotal:.2f}€)"
                    )
                    category = db["categories"].find_one({"_id": product["category_id"]})
                    if category:
                        cart_categories.append(category["name"])

    # ----- Prompt συστήματος -----
    base_prompt = (
        "Είσαι το SmartCart AI: ένας έξυπνος και ευγενικός διατροφολόγος, σεφ και οικιακός βοηθός. Μιλάς πάντα στον ενικό, "
        "με απλό και καθημερινό ύφος. Χρησιμοποιείς emojis και markdown. Προσαρμόζεις την απάντηση ανάλογα με την περίπτωση:\n"
        "- Αν αφορά φαγητό: είσαι διατροφολόγος και σεφ.\n"
        "- Αν αφορά καθαριότητα: είσαι οικιακός βοηθός.\n"
        "- Δίνεις πρακτικές, έξυπνες και σύντομες απαντήσεις.\n"
        "Χρησιμοποίησε γνώση διατροφής και συμβατότητας τροφίμων.\n"
        "Πρόσεξε θερμίδες και αλλεργίες. Αν δεν ταιριάζουν, ενημέρωσε ευγενικά."
        "Αν τα προϊόντα δεν ταιριάζουν μεταξύ τους, **μην προτείνεις τίποτα** ή πες ευγενικά ότι χρειάζονται επιπλέον υλικά. "
        "Έχεις τα συγκεκριμένα προϊόντα στη διάθεσή σου. Πρέπει να προτείνεις **ρεαλιστικό και λογικό** γεύμα. "
        "Αν η ερώτηση αφορά το πρωινό, πρότεινε ελαφριές και εύκολες επιλογές. Αν αφορά μεσημεριανό, χρησιμοποίησε συνδυασμούς υδατανθράκων και πρωτεΐνης. Αν είναι απόγευμα, μπορείς να προτείνεις σνακ ή τσάι.\n"
        "Να μιλάς σαν να απαντάς σε έναν φίλο που σε ρώτησε «Τι να φάω σήμερα;». Όχι σαν εγχειρίδιο ή εκπαιδευτικό υλικό. Είσαι SmartCart, όχι εγκυκλοπαίδεια.\n"
    )

    # Έλεγχος αν έχει προϊόντα ΣΧΕΤΙΚΑ με την πρόθεση του χρήστη
    if "breakfast" in intents:
        intent_has_products = has_relevant_products_in_cart(db, cart_id, BREAKFAST_CATEGORIES)
    elif "recipe" in intents:
        intent_has_products = has_relevant_products_in_cart(db, cart_id, ALLOWED_CATEGORIES)
    elif "cleaning" in intents:
        intent_has_products = has_relevant_products_in_cart(db, cart_id, CLEANING_CATEGORIES)
    else:
        # Για άλλες περιπτώσεις: έχει προϊόντα γενικά;
        intent_has_products = bool(cart_products)
    
    # Εισαγωγή κατάλληλης γραμμής στο prompt
    if "suggest" in intents:
        base_prompt += "Αυτά είναι προϊόντα από το clustering. Δεν βρίσκονται στο καλάθι του χρήστη.\n"
    if intent_has_products:
        base_prompt += "Ο χρήστης έχει σχετικά προϊόντα στο καλάθι του.\n"
    else:
        base_prompt += "Ο χρήστης δεν έχει σχετικά προϊόντα στο καλάθι του. Προτείνε με βάση τη βάση.\n"

    # ----- Βοηθητική συνάρτηση για προετοιμασία prompt ανά πρόθεση -----
    def generate_contextual_response(categories, emoji, fallback_text, intent_name, quantity, source="db",from_cart_items=None):
        
        # Φιλτράρισμα προϊόντων με βάση τις κατηγορίες
        category_ids = {
            c["_id"] for c in db["categories"].find({"name": {"$in": categories}})
        }
        relevant_products_source = from_cart_items if source == "cart" and from_cart_items else all_products
        products = [p for p in relevant_products_source if p["category_id"] in category_ids]


        if not products:
            return f"{emoji} {fallback_text}", None

        # Aνακάτεμα των προϊόντων τυχαία και επιλογή των πρώτων quantity 
        shuffle(products)
        selected = products[:quantity]
        names = [p["name"] for p in selected]

        # Προσθήκη νέου prompt με τα επιλεγμένα προϊόντα.
        product_text = ", ".join(names)

        if source == "cart":
            base_prompt_local = base_prompt + f"\nΑυτά είναι προϊόντα που **έχεις στο καλάθι σου** και σχετίζονται με την ερώτησή σου: {product_text}\n"
        else:
            base_prompt_local = base_prompt + f"\nΑυτά είναι σχετικά προϊόντα από τη βάση, ανεξάρτητα από το καλάθι: {product_text}\n"

        # prompt για την πρόθεση
        if intent_name == "breakfast":
            base_prompt_local += "Πρότεινε ένα υγιεινό πρωινό με βάση τα προϊόντα αυτά."
        
        elif intent_name == "recipe":
            base_prompt_local += (
                "Πρότεινε ένα λογικό και νόστιμο γεύμα με αυτά τα υλικά. "
                "Πρόσεξε θερμίδες και αλλεργίες. Αν δεν ταιριάζουν, ενημέρωσε ευγενικά."
            )
        elif intent_name == "cleaning":
            base_prompt_local += "Πρότεινε καθαριστικό για ρούχα από αυτά."

        return product_text, base_prompt_local

    # ---------------------- Χειρισμός ανά πρόθεση ----------------------

    try:

        # Ανάλυση Καλαθιού
        if "analysis" in intents:
            analysis_result = analyze_cart(db, user_id, cart_id)
            return analysis_result, {"suggestions": []}

        # -------------------- Συγκέντρωση των προϊόντων του καλαθιού ως αντικείμενα --------------------
        cart_only_products = []
        if cart_id:
            cart_items_cursor = db["cart_items"].find({"cart_id": cart_id})
            for item in cart_items_cursor:
                product = db["products"].find_one({"_id": ObjectId(item["product_id"])})
                if product:
                    cart_only_products.append(product)

        # Πρωινό
        if "breakfast" in intents:
            # Έλεγχος αν το καλάθι περιέχει προϊόντα σχετικά με πρωινό
            source = "cart" if has_relevant_products_in_cart(db, cart_id, BREAKFAST_CATEGORIES) else "db"
            
            # Δημιουργία prompt με βάση την πηγή (καλάθι ή βάση)
            product_text, prompt = generate_contextual_response(
                BREAKFAST_CATEGORIES, "☀️", "Δεν υπάρχουν προϊόντα πρωινού.", "breakfast", 3, source=source, from_cart_items=cart_only_products
            )
            
            if prompt is None:
                return product_text, None

        # Συνταγή
        elif "recipe" in intents:
            # Έλεγχος αν το καλάθι περιέχει προϊόντα που σχετίζονται με φαγητό
            source = "cart" if has_relevant_products_in_cart(db, cart_id, ALLOWED_CATEGORIES) else "db"
            
            # Δημιουργία prompt με βάση την πηγή (καλάθι ή βάση)
            product_text, prompt = generate_contextual_response(
                ALLOWED_CATEGORIES, "🍽️", "Δεν υπάρχουν προϊόντα για φαγητό.", "recipe", 2, source=source, from_cart_items=cart_only_products
            )
            
            if prompt is None:
                return product_text, None

        # Καθαριστικό
        elif "cleaning" in intents:
            # Έλεγχος αν το καλάθι περιέχει καθαριστικά
            source = "cart" if has_relevant_products_in_cart(db, cart_id, CLEANING_CATEGORIES) else "db"

            # Δημιουργία prompt με βάση την πηγή (καλάθι ή βάση)
            product_text, prompt = generate_contextual_response(
                CLEANING_CATEGORIES, "🧼", "Δεν υπάρχουν καθαριστικά αυτή τη στιγμή.", "cleaning", 1, source=source, from_cart_items=cart_only_products
            )

            if prompt is None:
                return product_text, None


        # --------- Προτάσεις από clusters --------- #
        elif "suggest" in intents:
            clusters = cluster_products_by_basket(db, user_id)
            if isinstance(clusters, dict) and "message" in clusters:
                return "🤖 Δεν υπάρχουν αρκετά δεδομένα για να προτείνω σχετικά προϊόντα.", None

            # Πάρε το πιο πρόσφατο open καλάθι
            cart = db["carts"].find_one({"user_id": ObjectId(user_id), "status": "open"}, sort=[("created_at", -1)])
            existing_ids = set()
            if cart:
                current_items = list(db["cart_items"].find({"cart_id": cart["_id"]}))
                existing_ids = {
                    str(item["product_id"])
                    for item in current_items
                    if item.get("product_id")
                }
            # Βρες 1-3 προϊόντα από το cluster που δεν έχει ήδη
            suggestions = []

            for cluster in clusters.values():
                for product in cluster:
                    # Έλεγχος εγκυρότητας για να μη σπάει το frontend
                    if not product.get("final_price") or not product.get("image_url"):
                        continue

                    product_id_str = str(product["id"])
                    if (
                        product_id_str not in existing_ids
                        and product_id_str not in [p["id"] for p in suggestions]
                    ):
                        product["id"] = product_id_str  # Βεβαιώσου ότι είναι string για frontend
                        suggestions.append(product)

                    if len(suggestions) >= 3:
                        break

                if len(suggestions) >= 3:
                    break

            # Επιστροφή αν δεν βρέθηκαν προτάσεις
            if not suggestions:
                return "Δεν εντόπισα προϊόντα που λείπουν από το καλάθι σου.", []

            names = []
            for p in suggestions:
                name = p.get("name", "Άγνωστο προϊόν")
                price = p.get("final_price", 0)
                names.append(f"{name} ({price:.2f}€)")
                        
            joined = ", ".join(names)

            prompt = (
                base_prompt +
                f"\nΜε βάση τα προηγούμενα καλάθια του χρήστη και ανάλυση clustering, "
                f"προτείνονται 1–3 προϊόντα που συνήθως αγοράζει μαζί:\n"
                f"- {joined}\n\n"
                "Εξήγησέ του σύντομα γιατί θα ήταν χρήσιμα, με καθημερινό αλλά ουδέτερο ύφος. "
                "Κλείσε την απάντηση με μια πρόταση τύπου: «Αν σου φαίνονται χρήσιμα, μπορείς να τα προσθέσεις εύκολα στο καλάθι πατώντας το κουμπί παρακάτω.»"

            )            

        # Αν δεν ανήκει σε καμία από τις παραπάνω
        else:
            prompt = base_prompt + (
                "Ο χρήστης έκανε γενική ερώτηση. Προσπάθησε να του προτείνεις κάτι χρήσιμο, "
                "ανάλογα με τα διαθέσιμα προϊόντα, ακόμα και αν δεν έχει καλάθι. Μην προτείνεις τυχαία προϊόντα."
            )

        # ---------------------- Κλήση στο OpenAI ----------------------
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=700
        )

        result = response.choices[0].message.content
        return result, {"suggestions": suggestions if "suggest" in intents else []}

    except Exception as e:
        return None, {"error": f"Σφάλμα AI: {str(e)}"}
