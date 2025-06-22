import streamlit as st
import requests
from datetime import datetime
from utils.api_helpers import call_api  # helper για API
from utils.session_helpers import require_login  # helper για login
from utils.logo_helper import inject_sidebar_logo # helper για εμφάνιση logo
import os

# --------------------- Έλεγχος login ---------------------
require_login()

# --------------------- Ρυθμίσεις ---------------------
st.set_page_config(page_title="Αρχική", page_icon="🏠", layout="wide")

# --------------------- Sidebar ---------------------
inject_sidebar_logo()

# --------------------- Φόρτωση Προφίλ ---------------------
res = call_api("/profile", method="get")
if res and res.status_code == 200:
    profile = res.json()
    email = profile.get("email", "Χρήστης")
else:
    email = "Χρήστης"
   
# --------------------- Header ---------------------
st.markdown(f"""
    <div style='text-align: center; margin-top: 2rem;'>
        <h1 style='font-size: 2.8rem;'>Καλωσήρθες στο <span style='color:#f06e95;'>Smartcart, </span>{email}</h1>
        <p style='font-size: 1.3rem; color:#444;'>Η έξυπνη πλατφόρμα αγορών με AI, στατιστικά και συγκρίσεις τιμών.</p>
    </div>
""", unsafe_allow_html=True)

# --------------------- Προφίλ Χρήστη ---------------------
try:
    res = call_api("/profile", method="get")
    if res.status_code == 200:
        profile = res.json()
        total_orders = profile.get("total_orders", 0)
        total_spent = profile.get("total_spent", 0.0)
        last_date_raw = profile.get("last_order_date")
        last_order = datetime.strptime(last_date_raw, "%a, %d %b %Y %H:%M:%S %Z").strftime("%d/%m/%Y") if last_date_raw else "—"

        # Κάρτες με βασικές πληροφορίες
        st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style='padding:1.4rem; border-radius:14px; background:linear-gradient(135deg, #dbeafe, #eff6ff); 
                        border-left: 5px solid #3b82f6; box-shadow: 0 4px 10px rgba(0,0,0,0.06);'>
                <div style='font-size: 1.1rem;'>📦 <b>{total_orders} Ολοκληρωμένες παραγγελίες</b></div>
                <div style='color: #1e3a8a; font-size: 0.95rem; margin-top: 0.4rem;'>Έξυπνες αγορές, κάθε φορά!</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='padding:1.4rem; border-radius:14px; background:linear-gradient(135deg, #dcfce7, #f0fdf4); 
                        border-left: 5px solid #10b981; box-shadow: 0 4px 10px rgba(0,0,0,0.06);'>
                <div style='font-size: 1.1rem;'>💶 <b>{total_spent:.2f}€ Σύνολο Αγορών</b></div>
                <div style='color: #065f46; font-size: 0.95rem; margin-top: 0.4rem;'>Επένδυση στην καθημερινότητα σου!</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style='padding:1.4rem; border-radius:14px; background:linear-gradient(135deg, #fef9c3, #fefce8); 
                        border-left: 5px solid #facc15; box-shadow: 0 4px 10px rgba(0,0,0,0.06);'>
                <div style='font-size: 1.1rem;'>📅 <b>Τελευταία αγορά:</b> {last_order}</div>
                <div style='color: #92400e; font-size: 0.95rem; margin-top: 0.4rem;'>Είσαι έτοιμος για την επόμενη;</div>
            </div>
            """, unsafe_allow_html=True)

        # Κάρτες εξοικονόμησης από ανταγωνιστές
        savings_efresh = profile.get("saved_vs_efresh", 0.0)
        savings_marketin = profile.get("saved_vs_marketin", 0.0)

        with st.container():
            st.markdown(f"""
            <div style='margin-top: 2rem; display: flex; gap: 1.5rem;'>
                        
            <div style='flex:1; padding:1.4rem; border-radius:14px; background:linear-gradient(135deg, #fce7f3, #fdf2f8); 
                        border-left: 5px solid #ec4899; box-shadow: 0 4px 10px rgba(0,0,0,0.06);'>
                <div style='font-size: 1.1rem;'>🛍️ Αν ψώνιζες από <b>e-Fresh</b></div>
                <div style='color: #831843; font-size: 0.95rem; margin-top: 0.4rem;'>Θα πλήρωνες <b>{savings_efresh:.2f}€</b> παραπάνω!</div>
            </div>

            <div style='flex:1; padding:1.4rem; border-radius:14px; background:linear-gradient(135deg, #ede9fe, #f5f3ff); 
                        border-left: 5px solid #8b5cf6; box-shadow: 0 4px 10px rgba(0,0,0,0.06);'>
                <div style='font-size: 1.1rem;'>🛒 Αν ψώνιζες από <b>MarketIn</b></div>
                <div style='color: #4c1d95; font-size: 0.95rem; margin-top: 0.4rem;'>Θα πλήρωνες <b>{savings_marketin:.2f}€</b> παραπάνω!</div>
            </div>

            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.warning("⚠️ Αδυναμία φόρτωσης του προφίλ.")
except Exception as e:
    st.error(f"⚠️ Σφάλμα: {e}")


# --------------------- Αυτόματη Δημιουργία Καλαθιού ---------------------
# Κουμπιά επιλογής
col1, col2 = st.columns([1, 1])
suggested_products = []

# Συνάρτηση για suggested προϊόντα
@st.cache_data(ttl=300)
def fetch_suggested_cart():
    res = call_api("/analytics/suggested-cart", method="get")
    if res.status_code == 200:
        return res.json().get("data", []) 
    return []

# Εμφάνιση επιλογών
st.markdown("""
<div style='margin-top: 2rem; text-align:center;'>
    <p style='font-size: 1.1rem; color: #444; margin-bottom: 1rem;'>
        Πώς θέλεις να ξεκινήσεις τις αγορές σου σήμερα;
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🤖 Έξυπνο καλάθι", key="auto_cart", use_container_width=True):
        
        # Προσθήκη overlay στην αρχή της ενέργειας
        with st.spinner("🤖 Δημιουργία έξυπνου καλαθιού..."):
        
            # Φόρτωση προτεινόμενων προϊόντων
            suggested = fetch_suggested_cart()

            if not suggested:
                st.warning("⚠️ Δεν υπάρχουν προτεινόμενα προϊόντα.")
            else:
                # Δημιουργία καλαθιού προσθέτοντας προϊόντα
                success = True
                failures = []

                for p in suggested:
                    product_id = p.get("id")
                    res = call_api("/cart/items", method="post", data={"product_id": product_id, "quantity": 1})

                    if res.status_code not in [200, 201]:
                        message = ""
                        try:
                            message = res.json().get("msg", res.text)
                        except:
                            message = res.text

                        failures.append({
                            "name": p.get("name", "Άγνωστο"),
                            "status": res.status_code,
                            "message": message
                        })
                        success = False

                if success:
                    st.success("✅ Το καλάθι σου δημιουργήθηκε με επιτυχία!")
                else:
                    st.warning("⚠️ Κάποια προϊόντα δεν προστέθηκαν σωστά.")
                    for f in failures:
                        st.markdown(f"""
                        ❌ **{f['name']}** — Status: `{f['status']}`  
                        <span style='color:#666;font-size:0.9rem;'>{f['message']}</span>
                        """, unsafe_allow_html=True)

                # Καθαρισμός cache και αλλαγή σελίδας
                st.cache_data.clear()
                st.switch_page("pages/03_🧺 Καλάθι.py")

with col2:
    if st.button("🛍️ Διάλεξε προϊόντα", use_container_width=True):
        st.switch_page("pages/02_🛒 Προϊόντα.py")
