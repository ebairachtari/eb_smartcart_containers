import streamlit as st
from datetime import datetime
from utils.api_helpers import call_api
from utils.session_helpers import require_login
from datetime import timedelta
from utils.logo_helper import inject_sidebar_logo


# --------------------- Έλεγχος login ---------------------
require_login()

# --------------------- Ρυθμίσεις ---------------------
st.set_page_config(page_title="Ιστορικό Αγορών", page_icon="📜", layout="wide")

# --------------------- Sidebar ---------------------
inject_sidebar_logo()

# --------------------- Φίλτρα --------------------
st.sidebar.markdown("## 🔍 Φίλτρα Ιστορικού Καλαθιών")

# --- Φίλτρο για ημερομηνία ---
date_filter = st.sidebar.selectbox(
    "Ημερομηνία:",
    options=[
        "Όλα",
        "Τελευταίες 30 ημέρες",
        "Τελευταίοι 6 μήνες",
        "Ανά έτος"
    ]
)

# --- Φίλτρο για status ---
status_filter = st.sidebar.multiselect(
    "Status:",
    options=["ordered", "cancelled"],
    default=["ordered"]
)

# --------------------- Τίτλος και περιγραφή ---------------------
st.markdown("""
    <div style='text-align: center; margin-top: 2rem;'>
        <h1 style='font-size: 2.5rem;'>Ιστορικό Καλαθιών</h1>
        <p style='font-size: 1.2rem; color:#555;'>Όλα τα καλάθια που ολοκλήρωσες με το SmartCart.</p>
    </div>
""", unsafe_allow_html=True)

# ------------------ Λήψη ιστορικού καλαθιών ------------------ #
@st.cache_data(ttl=60)
def fetch_cart_history():
    res = call_api("/carts/history", method="get")
    if res and res.status_code == 200:
        return res.json().get("carts", [])
    return []

# ------------------ Επανακατεύθυνση σε καλάθι ------------------
if st.session_state.get("redirect_to_cart"):
    st.session_state["redirect_to_cart"] = False
    st.switch_page("pages/03_🧺 Καλάθι.py")

# ------------------ Μήνυμα μετά από clone ------------------
if st.session_state.get("clone_success"):
    st.success("✅ Το καλάθι αντιγράφηκε με επιτυχία!")
    st.session_state["clone_success"] = False

# ------------------ Κλωνοποίηση καλαθιού ------------------
def clone_cart(cart_id):
    with st.spinner("🔁 Δημιουργία νέου καλαθιού..."):
        res = call_api("/cart/clone", method="post", json={"cart_id": cart_id})
    if res and res.status_code in [200, 201]:
        st.session_state["cart_cloned"] = True
        st.session_state["redirect_to_cart"] = True
        st.cache_data.clear()
        st.rerun()
    else:
        msg = res.json().get("msg", "Άγνωστο σφάλμα") if res else "Σφάλμα σύνδεσης"
        st.error(f"❌ Αποτυχία: {msg}")

# ------------------ Κάρτα καλαθιού ------------------
history = fetch_cart_history()
is_new_user = len(history) == 0

# ------------------ Εφαρμογή φίλτρων ------------------
filtered_history = []

now = datetime.now()
for cart in history:
    cart_date_str = cart.get("created_at")
    try:
        cart_date = datetime.strptime(cart_date_str, "%a, %d %b %Y %H:%M:%S %Z")
    except:
        continue

    cart_status = cart.get("status", "").lower()
    if cart_status not in status_filter:
        continue

    if date_filter == "Τελευταίες 30 ημέρες" and (now - cart_date).days > 30:
        continue
    elif date_filter == "Τελευταίοι 6 μήνες" and (now - cart_date).days > 180:
        continue
    elif date_filter == "Ανά έτος" and cart_date.year != now.year:
        continue

    filtered_history.append(cart)

history = filtered_history

if is_new_user:
    st.info("👋 Δεν έχεις ακόμα δημιουργήσει καλάθια. Το SmartCart θα εμφανίσει το ιστορικό σου εδώ μόλις ξεκινήσεις τις πρώτες αγορές.")
elif not history:
    st.info("ℹ️ Δεν βρέθηκαν καλάθια που να ταιριάζουν με τα επιλεγμένα φίλτρα.")

else:
    for cart in history:
        cart_id = cart.get("id")
        status = cart.get("status", "").lower()
        items = cart.get("items", [])
        date = cart.get("created_at")

        try:
            date_str = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z").strftime("%d/%m/%Y")
        except:
            date_str = str(date)

        # Αν εμφανίστηκε επιτυχές clone μήνυμα
        if st.session_state.get("clone_success") == cart_id:
            st.success("✅ Το καλάθι αντιγράφηκε με επιτυχία!")
            st.session_state["clone_success"] = None

        # Τίτλος
        status_label = {
            "ordered": "🟢 Ολοκληρωμένο",
            "cancelled": "🔴 Ακυρωμένο"
        }.get(status, "❔ Άγνωστο")

        title = f"🛒 Καλάθι {date_str}   |   {status_label}"
        
        # Κενό πριν τα προϊόντα
        st.markdown("")
        with st.expander(title, expanded=False):

            # Προϊόντα
            subtotal = 0.0
            if items:
                for item in items:
                    name = item.get("product_name", "Άγνωστο")
                    qty = item.get("quantity", 1)
                    unit = item.get("unit_price", 0.0)
                    total = qty * unit
                    subtotal += total
                    image_url = item.get("image_url", "")

                    # Σειρά με εικόνα, όνομα και υπολογισμό
                    cols = st.columns([1, 5])
                    with cols[0]:
                        st.markdown(
                    f"""
                    <div style='width:60px;height:60px;background-color:white;
                                display:flex;align-items:center;justify-content:center;
                     "           border:1px solid #ddd; border-radius:8px; overflow:hidden;'>
                        <img src="{image_url}" style='max-width:100%; max-height:100%; object-fit:contain;'>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                    with cols[1]:
                        st.write(f"**{name}**")
                        st.caption(f"{qty} × {unit:.2f}€ = {total:.2f}€")
            else:
                st.info("❕ Δεν υπάρχουν προϊόντα σε αυτό το καλάθι.")

            # Κενό πριν το σύνολο
            st.markdown("---")

            # Σύνολο + κουμπί αντιγραφής σε σειρά
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"**Σύνολο:** {subtotal:.2f}€")
            with col2:
                if st.button("🔁 Αντιγραφή", key=f"clone_btn_{cart_id}"):
                    clone_cart(cart_id)


