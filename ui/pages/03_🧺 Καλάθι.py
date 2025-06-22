import streamlit as st
import requests
import random
from utils.session_helpers import require_login
from utils.api_helpers import call_api
from utils.logo_helper import inject_sidebar_logo  # helper για εμφάνιση logo

# --------------------- Έλεγχος login ---------------------
require_login()

# --------------------- Ρυθμίσεις ---------------------
st.set_page_config(page_title="Το Καλάθι μου", page_icon="🧺", layout="wide")

# ------------------ Στυλ για τον τίτλο ------------------
st.markdown("""
    <div style='text-align: center; margin-top: 2rem;'>
        <h1 style='font-size: 2.5rem;'>Το καλάθι σου</h1>
    </div>
""", unsafe_allow_html=True)

# --------------------- Sidebar ---------------------
inject_sidebar_logo()

# ------------------- Ρύθμιση πρώτης φόρτωσης -------------------
if "initial_load_done" not in st.session_state:
    st.session_state["initial_load_done"] = False

if not st.session_state["initial_load_done"]:
    st.session_state["initial_load_done"] = True
    st.rerun()

# ------------------------- Flags για refresh και AI -------------------------
refresh_key = "refresh_cart"

if refresh_key not in st.session_state:
    st.session_state[refresh_key] = 0

if "show_ai_suggestions" not in st.session_state:
    st.session_state["show_ai_suggestions"] = False
if "ai_cart_added" not in st.session_state:
    st.session_state["ai_cart_added"] = False
if "ai_just_added" not in st.session_state:
    st.session_state["ai_just_added"] = False
if "ai_response_text" not in st.session_state:
    st.session_state["ai_response_text"] = ""
if "ai_suggestions" not in st.session_state:
    st.session_state["ai_suggestions"] = []
if "show_recipe_ai" not in st.session_state:
    st.session_state["show_recipe_ai"] = False
if "recipe_response_text" not in st.session_state:
    st.session_state["recipe_response_text"] = ""
if "show_cart_analysis" not in st.session_state:
    st.session_state["show_cart_analysis"] = False
if "cart_analysis_response" not in st.session_state:
    st.session_state["cart_analysis_response"] = ""

# Αν το cart ενημερώθηκε σε άλλη σελίδα (π.χ. Προϊόντα), κάνε auto-refresh εδώ
if st.session_state.get("cart_just_updated", False):
    st.session_state["cart_just_updated"] = False
    st.cache_data.clear()
    st.rerun()

# Αν το καλάθι αδειάσει, εμφάνισε μήνυμα
if st.session_state.get("cart_cleared"):
    st.success("✅ Το καλάθι άδειασε!")
    st.session_state["cart_cleared"] = False
if st.session_state.get("clear_cart_failed"):
    st.warning("⚠️ Δεν ήταν δυνατή η διαγραφή του καλαθιού.")
    st.session_state["clear_cart_failed"] = False

# Αν το καλάθι αντιγράφηκε, εμφάνισε μήνυμα
if st.session_state.get("cart_cloned"):
    st.success("✅ Το καλάθι αντιγράφηκε με επιτυχία!")
    st.session_state["cart_cloned"] = False

# Αν προστέθηκε 1 προϊόν από AI με κουμπί → εμφάνισε μήνυμα
if st.session_state["ai_cart_added"]:
    st.success("✅ Το προϊόν προστέθηκε στο καλάθι!")
    st.session_state["ai_cart_added"] = False

# Αν προστέθηκαν όλα τα προϊόντα από AI → καθάρισε και κάνε rerun
if st.session_state["ai_just_added"]:
    st.session_state["ai_just_added"] = False
    st.session_state["show_ai_suggestions"] = False
    st.session_state["ai_response_text"] = ""
    st.session_state["ai_suggestions"] = []
    st.rerun()

# --------------------- Συνάρτηση για λήψη περιεχομένων καλαθιού ---------------------
def get_cart_contents():
    try:
        res = call_api("/cart", method="get")
        if res.status_code == 200:
            return res.json()
        return None
    except Exception as e:
        print("⚠️ Σφάλμα στο API:", e)
        return None

# --------------------- Συνάρτηση για ενημέρωση ποσότητας προϊόντος ---------------------
def update_quantity(product_id, action):
    call_api("/cart/items", method="patch", json={
        "product_id": product_id,
        "action": action
    })
    st.cache_data.clear()
    
# --------------------- Συνάρτηση για διαγραφή προϊόντος από το καλάθι ---------------------
def delete_product(product_id):
    call_api(f"/cart/item/{product_id}", method="delete")
    st.cache_data.clear()

# --------------------- Συνάρτηση για ολοκλήρωση καλαθιού ---------------------
def order_cart():
    call_api("/cart/ordered", method="patch")
    st.cache_data.clear()
    st.session_state["last_cart_status"] = "ordered"

# --------------------- Συνάρτηση για ακύρωση καλαθιού ---------------------
def cancel_cart():
    call_api("/cart/cancelled", method="patch")
    st.cache_data.clear()
    st.session_state["last_cart_status"] = "cancelled"

# --------------------- Συνάρτηση για διαγραφή ολόκληρου καλαθιού ---------------------
def delete_whole_cart():
    res = call_api("/cart", method="delete")
    st.cache_data.clear()
    return res

# --------------------- Συνάρτηση για εύρεση open καλαθιού ---------------------
def get_open_cart_id():
    cart = get_cart_contents()
    if cart and cart.get("status") == "open":
        return cart.get("id")
    return None

# --------------------- Εμφάνιση Καλαθιού ---------------------
def show_cart():
    cart = get_cart_contents()

    if not cart or not cart.get("items"):
        # Αν δεν υπάρχει ενεργό καλάθι, δες αν μόλις ολοκληρώθηκε ή ακυρώθηκε
        if "last_cart_status" in st.session_state:
            if st.session_state["last_cart_status"] == "ordered":
                st.success("✅ Η παραγγελία σου ολοκληρώθηκε με επιτυχία!")
            elif st.session_state["last_cart_status"] == "cancelled":
                st.warning("↩️ Η παραγγελία σου ακυρώθηκε.")
            del st.session_state["last_cart_status"]
        else:
            st.warning("Δεν υπάρχει ενεργό καλάθι.")
        return

    items = cart["items"]
    total = cart.get("total_price", 0)
    efresh_total = cart.get("total_price_efresh", 0)
    marketin_total = cart.get("total_price_marketin", 0)

    for item in items:
        with st.container():
            cols = st.columns([1, 3, 2, 0.5, 0.5, 0.5, 1])

            # Εικόνα
            with cols[0]:
                image_url = item.get("image_url", "")
                st.markdown(f"""
                    <div style='height:90px; display:flex; align-items:center; justify-content:center;'>
                        <img src="{image_url}" style='max-height:90px; max-width:90px; object-fit:contain;'>
                    </div>
                """, unsafe_allow_html=True)

            # Όνομα και διαθεσιμότητα
            with cols[1]:
                st.markdown(f"**{item.get('product_name', 'Άγνωστο')}**")
                st.caption(item.get("availability", ""))

            # Τιμή και σύνολο
            with cols[2]:
                unit_price = item.get("unit_price", 0)
                quantity = item.get("quantity", 1)
                subtotal = unit_price * quantity
                st.markdown(f"{unit_price:.2f}€/τμχ")
                st.caption(f"📦 {subtotal:.2f}€ σύνολο")

            # Κουμπί μείωσης ποσότητας
            with cols[3]:
                def decrement(product_id):
                    update_quantity(product_id, "decrement")

                st.button("➖", key=f"minus_{item['product_id']}", on_click=decrement, args=(item["product_id"],))


            # Εμφάνιση ποσότητας
            with cols[4]:
                st.markdown(f"<div style='text-align:center;font-size:18px'>{quantity}</div>", unsafe_allow_html=True)

            # Κουμπί αύξησης ποσότητας
            with cols[5]:
                def increment(product_id):
                    update_quantity(product_id, "increment")

                st.button("➕", key=f"plus_{item['product_id']}", on_click=increment, args=(item["product_id"],))

            # Κουμπί διαγραφής προϊόντος
            with cols[6]:
                def delete(product_id):
                    delete_product(product_id)

                st.button("🗑️ Αφαίρεση", key=f"del_{item['product_id']}", on_click=delete, args=(item["product_id"],))

            # Προσθήκη κενής στήλης για spacing
            st.markdown("---")
    
    # ---------------------- Κουμπί για αφαίρεση όλων των προϊόντων ----------------------
    empty_col1, empty_col2, empty_col3 = st.columns([4, 1, 1])
    with empty_col3:
        if st.button("🧹 Άδειασμα Καλαθιού"):
            res = delete_whole_cart()
            if res and res.status_code == 200:
                st.session_state["cart_cleared"] = True
            else:
                st.session_state["clear_cart_failed"] = True
            st.rerun()

    # ---------------------- SmartCart Info Box with Σύνολο ----------------------
    diff = min(efresh_total, marketin_total) - total

    st.markdown(f"""
        <div style="background-color:#f0fdf4; border:1px solid #34d399; border-radius:10px;
                    padding:1.2rem; margin-top:1.5rem; font-size:15px; position:relative;">
            <div style='position:absolute; top:1.2rem; right:1.2rem;
                        font-size:1.4rem; font-weight:bold;'>
                🧾 Σύνολο: {total:.2f}€
            </div>
            <b>SmartCart:</b> Εξοικονομείς τουλάχιστον <span style="color:#16a34a;">{diff:.2f}€</span> σε σχέση με τα άλλα καταστήματα.
            <br><span style="color:#4b5563;">e-Fresh:</span> {efresh_total:.2f}€ |
            <span style="color:#4b5563;">MarketIn:</span> {marketin_total:.2f}€
        </div>
    """, unsafe_allow_html=True)

    # --- Kενό διάστημα για spacing ---
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("---")

    # ---------------------- Κουμπιά Ολοκλήρωσης & Ακύρωσης ----------------------
    col1, col2 = st.columns([5.8, 1.2])

    with col1:
        st.button("↩️ Ακύρωση Παραγγελίας", on_click=cancel_cart)

    with col2:
        st.button("🛒 Ολοκλήρωση Αγοράς", on_click=order_cart)

    # --- Kενό διάστημα για spacing ---
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")

    # ------------------- 🤖 SmartCart AIAssistant — Συμβουλές -------------------

    st.markdown("## 🤖 Πώς μπορώ να σε βοηθήσω;")
    cols = st.columns(4)

    # --------- Πρόταση Συμπληρωματικών Προϊόντων ---------
    with cols[0]:
        if st.button("💡Τι μου λείπει;"):
            st.session_state["show_ai_suggestions"] = True
            with st.spinner("Γίνεται ανάλυση..."):
                cart = get_cart_contents()
                cart_id = cart.get("id") if cart else None
                res = call_api("/ai/ask", method="post", json={
                    "question": "Τι μου λείπει;",
                    "cart_id": cart_id
                })
                if res and res.status_code == 200:
                    data = res.json()
                    st.session_state["ai_response_text"] = data.get("response", "")
                    st.session_state["ai_suggestions"] = data.get("suggestions", [])
                else:
                    st.session_state["ai_response_text"] = "⚠️ Το SmartCart δεν κατάφερε να δώσει απάντηση."
                    st.session_state["ai_suggestions"] = []
            st.rerun()

    # --------- 2. Έμπνευση για Γεύματα ---------
    with cols[1]:
        if st.button("👩‍🍳 Έμπνευση για Γεύματα"):
            st.session_state["show_recipe_ai"] = True
            with st.spinner("Αναζήτηση συνταγών..."):
                cart = get_cart_contents()
                cart_id = cart.get("id") if cart else None
                res = call_api("/ai/ask", method="post", json={
                    "question": "Πρότεινέ μου 2–3 συνταγές με βάση τα προϊόντα που έχω στο καλάθι μου και εκτίμησε τις θερμίδες ανά μερίδα. Θέλω εύκολες, υγιεινές και ρεαλιστικές επιλογές.",
                    "cart_id": cart_id
                })
                if res and res.status_code == 200:
                    data = res.json()
                    st.session_state["recipe_response_text"] = data.get("response", "🤖 Δεν εντόπισα συνταγές.")
                else:
                    st.session_state["recipe_response_text"] = "⚠️ Δεν ήταν δυνατή η επικοινωνία με το SmartCart AI."
            st.rerun()

    # --------- 3. Έξυπνη Ανάλυση Καλαθιού ---------
    with cols[2]:
        if st.button("📊 Έξυπνη Ανάλυση Καλαθιού"):
            st.session_state["show_cart_analysis"] = True
            with st.spinner("Γίνεται ανάλυση του καλαθιού..."):
                cart = get_cart_contents()
                cart_id = cart.get("id") if cart else None
                res = call_api("/ai/ask", method="post", json={
                    "question": "Κάνε μου ανάλυση καλαθιού",
                    "cart_id": cart_id
                })
                if res and res.status_code == 200:
                    st.session_state["cart_analysis_response"] = res.json().get("response", "")
                else:
                    st.session_state["cart_analysis_response"] = "⚠️ Το SmartCart δεν κατάφερε να κάνει ανάλυση του καλαθιού."
            st.rerun()

    # --------- 4. Γενική Ερώτηση στον SmartCart AI ---------
    with cols[3]:
        if st.button("💬 Ρώτα το SmartCart", key="open_custom_question"):
            st.session_state["show_custom_question"] = True
            st.session_state["custom_ai_input_value"] = ""  # Reset input για αποφυγή conflicts

    # Μόλις πατήσει το κουμπί, εμφανίζεται input και submit
    if st.session_state.get("show_custom_question"):
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        question = st.text_input("Γράψε την ερώτησή σου εδώ:", key="custom_ai_input_value")

        if st.button("🆗 Υποβολή Ερώτησης", key="submit_custom_question"):
            with st.spinner("Σκέφτομαι την καλύτερη απάντηση..."):
                cart = get_cart_contents()
                cart_id = cart.get("id") if cart else None

                res = call_api("/ai/ask", method="post", json={
                    "question": question,
                    "cart_id": cart_id
                })

                if res and res.status_code == 200:
                    st.session_state["custom_ai_response"] = res.json().get("response", "🤖 Δεν ελήφθη απάντηση.")
                else:
                    st.session_state["custom_ai_response"] = "⚠️ Δεν ήταν δυνατή η επικοινωνία με το SmartCart AI."
            st.rerun()

    # --------- Εμφάνιση Συμπληρωματικών Προϊόντων ---------
    if st.session_state.get("show_ai_suggestions"):
        st.markdown(f"""<div style="border:1px solid #ccc; padding:1rem; border-radius:10px; background-color:#f9f9f9">
            <div style="font-size:16px;">{st.session_state['ai_response_text']}</div>
        </div>""", unsafe_allow_html=True)

        suggestions = st.session_state.get("ai_suggestions", [])
        if suggestions:
            top_row = st.columns([4, 1])  # Κουμπί πάνω δεξιά
            with top_row[0]:
                st.markdown("### 📌 Προτεινόμενα Προϊόντα:")
            with top_row[1]:
                st.markdown("<div style='margin-top: 1rem'></div>", unsafe_allow_html=True)
                if st.button(" 🛒 Προσθήκη όλων στο καλάθι"):
                    with st.spinner("Προσθήκη προϊόντων..."):
                        for product in suggestions:
                            call_api("/cart/items", method="post", json={
                                "product_id": product["id"],
                                "quantity": 1
                            })
                        st.toast("✅ Όλα τα προϊόντα προστέθηκαν!")
                        st.cache_data.clear()
                        st.session_state["ai_just_added"] = True
                        st.rerun()

            cols = st.columns(3)
            for i, product in enumerate(suggestions):
                with cols[i % 3]:
                    # Προϊόν με εικόνα, τιμή, όνομα
                    st.markdown(f"""<div style='display: flex; align-items: center; justify-content: center; height: 130px; margin-bottom: 0.4rem;'>
                        <img src="{product['image_url']}" style="max-height: 110px; max-width: 100%; object-fit: contain;">
                    </div>
                    <p style='font-weight: 600; margin: 0.4rem 0 0.2rem 0; font-size: 0.95rem; min-height: 2.5rem;'>{product['name']}</p>
                    <p style='font-size: 1.1rem; font-weight: bold; color: #222; margin: 0.2rem 0 0.4rem 0;'>{float(product['final_price']):.2f} €</p>""", unsafe_allow_html=True)

        # Απόκρυψη στο κάτω μέρος
        if st.button("🔼 Απόκρυψη περιεχομένου", key="hide_ai_suggestions"):
            st.session_state["show_ai_suggestions"] = False
            st.session_state["ai_response_text"] = ""
            st.session_state["ai_suggestions"] = []
            st.rerun()

    # --------- Εμφάνιση Συνταγών ---------
    if st.session_state.get("show_recipe_ai"):
        st.markdown(f"""
            <div style="border:1px solid #ccc; padding:1rem; border-radius:10px; background-color:#f9f9f9">
                <div style="font-size:16px;">{st.session_state['recipe_response_text']}</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔼 Απόκρυψη περιεχομένου", key="hide_recipe_ai"):
            st.session_state["show_recipe_ai"] = False
            st.session_state["recipe_response_text"] = ""
            st.rerun()

    # --------- Εμφάνιση Ανάλυσης Καλαθιού ---------
    if st.session_state.get("show_cart_analysis"):
        st.markdown(f"""
            <div style="border:1px solid #ccc; padding:1rem; border-radius:10px; background-color:#f9f9f9">
                <div style="font-size:16px;">{st.session_state['cart_analysis_response']}</div>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔼 Απόκρυψη περιεχομένου", key="hide_cart_analysis"):
            st.session_state["show_cart_analysis"] = False
            st.session_state["cart_analysis_response"] = ""
            st.rerun()

    # --------- Εμφάνιση Απάντησης ---------
    if st.session_state.get("custom_ai_response"):
        st.markdown(f"""
            <div style="border:1px solid #ccc; padding:1rem; border-radius:10px; background-color:#f9f9f9; margin-top:1.5rem;">
                <div style="font-size:16px;">{st.session_state['custom_ai_response']}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

        if st.button("🔼 Απόκρυψη περιεχομένου", key="hide_custom_question"):
            st.session_state["show_custom_question"] = False
            st.session_state["custom_ai_response"] = ""
            st.rerun()

# Κλήση εμφάνισης
show_cart()