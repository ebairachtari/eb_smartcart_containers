import streamlit as st
import requests
from utils.api_helpers import call_api  # helper για API
from utils.session_helpers import require_login  # helper για login
from utils.logo_helper import show_logo_centered  # χρήση για εμφάνιση logo
from utils.logo_helper import inject_sidebar_logo  # χρήση για εμφάνιση logo στο sidebar

# --------------------- Έλεγχος login ---------------------
require_login()

# --------------------- Ρυθμίσεις ---------------------
st.set_page_config(page_title="Προϊόντα", page_icon="🛒", layout="wide")

# ------------------ Στυλ για τον τίτλο ------------------
st.markdown("""
    <div style='text-align: center; margin-top: 2rem;'>
        <h1 style='font-size: 2.5rem;'>Λίστα Προϊόντων</h1>
    </div>
""", unsafe_allow_html=True)

# --------------------- Sidebar ---------------------
inject_sidebar_logo()

# ------------------ Cache για όλα τα προϊόντα ------------------
@st.cache_data
def get_all_products():
    res = call_api("/products", method="get")
    if res.status_code == 200:
        return res.json()
    return []

# ------------------ Cache για λήψη λεπτομερειών προϊόντος ------------------
@st.cache_data
def get_product_details(product_id):
    res = call_api(f"/products/{product_id}", method="get")
    if res.status_code == 200:
        return res.json()
   
    return {}

# ------------------ Συνάρτηση για λήψη badge AI πρόβλεψης ------------------
def get_prediction_badge(product_id):
    prediction_key = f"ai_recommend_{product_id}"
    
    if prediction_key not in st.session_state:
        res = call_api(f"/ml/predict-product?product_id={product_id}", method="get")
        if res and res.status_code == 200:
            data = res.json().get("data", {})
            st.session_state[prediction_key] = data.get("prediction") == 1
        else:
            st.session_state[prediction_key] = False

    is_ai_recommended = st.session_state[prediction_key]

    if is_ai_recommended:
        return """
            <div style='
                display: flex;
                justify-content: center;
                align-items: center;
                margin-bottom: 0.8rem;
            '>
                <span title="Βασισμένο στις πρόσφατες αγορές σου" style='
                    background: linear-gradient(90deg, #f06e95, #ff8a65);
                    color: white;
                    padding: 6px 16px;
                    border-radius: 999px;
                    margin-bottom: 0.5rem;
                    font-size: 0.85rem;
                    font-weight: bold;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                '>
                    🔥 Επιλογή SmartCart
                </span>
            </div>
        """
    else:
        return "<div style='height: 38px; margin-bottom: 0.8rem;'></div>"

# ------------------ Εμφάνιση Προϊόντων ------------------
def show_products():

    # Cache-safe λήψη όλων των προϊόντων για εξαγωγή κατηγοριών
    products = get_all_products()
    if not products:
        st.info("ℹ️ Δεν υπάρχουν διαθέσιμα προϊόντα.")
        return

    # Εξαγωγή μοναδικών κατηγοριών 
    seen = set()
    ordered_categories = []
    for p in products:
        cat = p.get("category")
        if cat and cat not in seen:
            seen.add(cat)
            ordered_categories.append(cat)
    categories = ["Καμία κατηγορία"] + ordered_categories

    #  Επιλογή κατηγορίας
    st.sidebar.markdown(
        "<div style='font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem;'>"
        "🔍 Κατηγορίες"
        "</div>", unsafe_allow_html=True
    )

    new_category = st.sidebar.radio(
        label="Κατηγορίες",
        options=categories,
        index=0,
        key="category_radio",
        label_visibility="collapsed"
    )

    if "selected_category" not in st.session_state:
        st.session_state.selected_category = new_category

    if new_category != st.session_state.selected_category:
        st.session_state.selected_category = new_category
        st.session_state["name_filter"] = ""
        st.rerun()

    category_param = "" if new_category == "Καμία κατηγορία" else new_category

    #  Φίλτρα και ταξινόμηση 
    cols_filters = st.columns([3, 2])
    with cols_filters[0]:
        name_filter = st.text_input("🔍 Αναζήτηση με όνομα:", key="name_filter")
    
    with cols_filters[1]:
        sort_option = st.selectbox("↕️ Ταξινόμηση:", ["", "price_asc", "price_desc", "name_asc", "name_desc"],
            format_func=lambda x: {
                "": "Καμία",
                "price_asc": "Τιμή ↑",
                "price_desc": "Τιμή ↓",
                "name_asc": "Όνομα A-Ω",
                "name_desc": "Όνομα Ω-A"
            }.get(x, x)
        )

    # Μήνυμα πάνω από το spinner 
    info_box = st.empty()
    spinner_area = st.empty()

    # Έλεγχος αν δεν έχει δοθεί ούτε όνομα ούτε κατηγορία 
    if new_category == "Καμία κατηγορία" and not name_filter:
        st.info(" ℹ️ Μπορείς να επιλέξεις κατηγορία ή να αναζητήσεις προϊόντα.")
        return
    else:
        filtered_products = [
            p for p in products
            if (new_category == "Καμία κατηγορία" or p["category"] == new_category)
            and (not name_filter or name_filter.lower() in p["name"].lower())
        ]

        # Αν δεν βρέθηκαν αποτελέσματα, εμφάνισε μήνυμα
        if not filtered_products:
            st.info("⚠️ Δεν βρέθηκαν προϊόντα που να ταιριάζουν με τα επιλεγμένα φίλτρα.")
            return

    # Παράμετροι αναζήτησης
    params = {
        "name": name_filter,
        "category": category_param,
        "sort": sort_option
    }

    # Συνάρτηση για ασφαλή εμφάνιση 
    def safe(value):
        if not value or str(value).lower() in ["none", "nan", "null"]:
            return "-"
        return str(value)

    # ------------------ Εμφάνιση προϊόντων σε Grid ------------------
    # Placeholder για καθαρή απόδοση
    placeholder = st.empty() # Καθαρισμός placeholder
    with placeholder.container():
        with st.spinner("🔄 Φόρτωση προϊόντων..."):

            #  Κλήση API για αναζήτηση προϊόντων
            res = call_api("/products/search", method="get", params=params)
            filtered_products = res.json() if res.status_code == 200 else []

            #  Αρχικοποίηση & Toggle AI 
            if "enable_ai" not in st.session_state:
                st.session_state["enable_ai"] = False
            enable_ai = st.session_state["enable_ai"]

            new_ai = st.sidebar.toggle("Ενεργοποίηση AI Πρόβλεψης", value=st.session_state["enable_ai"])

            if new_ai != st.session_state["enable_ai"]:
                st.session_state["enable_ai"] = new_ai
                # Καθαρίζουμε όλα τα cached αποτελέσματα πρόβλεψης
                for key in list(st.session_state.keys()):
                    if key.startswith("ai_recommend_"):
                        del st.session_state[key]
                st.rerun()

            #  Συνάρτηση απόδοσης badge AI 
            def get_prediction_badge(product_id):
                prediction_key = f"ai_recommend_{product_id}"

                if st.session_state.get("enable_ai", True):
                    # Αν δεν υπάρχει αποθηκευμένο αποτέλεσμα ή είναι False, κάνε νέο call
                    if prediction_key not in st.session_state:
                        res = call_api(f"/ml/predict-product?product_id={product_id}", method="get")
                        if res and res.status_code == 200:
                            data = res.json().get("data", {})
                            st.session_state[prediction_key] = data.get("prediction") == 1
                        else:
                            st.session_state[prediction_key] = False

                if st.session_state.get(prediction_key):
                    return """<div style='display: flex; justify-content: center; margin-bottom: 0.8rem;'>
                        <span title="Βασισμένο στις πρόσφατες αγορές σου" style='
                            background: linear-gradient(90deg, #f06e95, #ff8a65);
                            color: white;
                            padding: 6px 16px;
                            border-radius: 999px;
                            font-size: 0.85rem;
                            font-weight: bold;
                            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
                        '>
                            🔥 Επιλογή SmartCart
                        </span>
                    </div>"""
                else:
                    return "<div style='height: 38px; margin-bottom: 0.8rem;'></div>"

            # Εμφάνιση προϊόντων
            cols = st.columns(3)
            for i, product in enumerate(filtered_products):
                with cols[i % 3]:
                    with st.container():
                        
                        # Αν είναι ενεργή η πρόβλεψη AI εμφάνιση badge
                        if enable_ai:
                            st.markdown(get_prediction_badge(product['id']), unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='height: 38px; margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)

                        # Εμφάνιση εικόνας
                        st.markdown(f"""
                        <div style='
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 160px;
                            margin-bottom: 0.8rem;
                        '>
                            <img src="{product['image_url']}" style="max-height: 140px; max-width: 100%; object-fit: contain;">
                        </div>
                        """, unsafe_allow_html=True)

                        # Εμφάνιση ονόματος
                        st.markdown(f"""
                        <p style='
                            font-weight: 600;
                            margin: 0.5rem 0;
                            display: -webkit-box;
                            -webkit-line-clamp: 3;
                            -webkit-box-orient: vertical;
                            overflow: hidden;
                            height: 3.9rem;
                            line-height: 1.3rem;
                        '>{safe(product['name'])}</p>
                        """, unsafe_allow_html=True)

                        # Εμφάνιση διαθεσιμότητας
                        availability = product.get("availability", "")
                        icon = "❔"
                        color = "#666"

                        if "διαθέσιμο" in availability.lower():
                            icon = "✅"
                            color = "#228B22"
                        elif "περιορισμένη" in availability.lower():
                            icon = "‼️"
                            color = "#DAA520"
                        elif "εξαντλημένο" in availability.lower():
                            icon = "❌"
                            color = "#B22222"

                        st.markdown(
                            f"<p style='margin: 0.2rem 0; color:{color};'>{icon} {safe(availability)}</p>",
                            unsafe_allow_html=True
                        )

                        # Τιμή και κουμπί προσθήκης στο καλάθι
                        price_col, cart_col = st.columns([3, 3])

                        with price_col:
                            st.markdown(
                                f"<p style='font-size: 2.5rem; font-weight: bold; color: #222; margin: 0.5rem 0;'>"
                                f"{float(product['final_price']):.2f} €</p>",
                                unsafe_allow_html=True
                            )

                        with cart_col:
                            add_key = f"add_{product['id']}"

                            # Styling κουμπιού μέσω container
                            button_style = """
                                <style>
                                div[data-testid="stHorizontalBlock"] button {
                                    background-color: #34bd15;
                                    color: white;
                                    font-weight: bold;
                                    padding: 0.5rem 1rem;
                                    border: none;
                                    border-radius: 8px;
                                    font-size: 0.9rem;
                                    margin-top: 0.4rem;
                                }
                                div[data-testid="stHorizontalBlock"] button:hover {
                                    background-color: #007ba1;
                                }
                                </style>
                            """
                            st.markdown(button_style, unsafe_allow_html=True)

                            # Αν είναι εξαντλημένο, εμφάνιση απενεργοποιημένου κουμπιού
                            if "εξαντλημένο" in availability.lower():
                                st.markdown("""
                                    <button disabled style='
                                        background-color: #ccc;
                                        color: #666;
                                        font-weight: bold;
                                        padding: 0.5rem 1rem;
                                        border: none;
                                        border-radius: 8px;
                                        font-size: 0.9rem;
                                        margin-top: 0.4rem;
                                        width: 100%;
                                        cursor: not-allowed;
                                    '>
                                        🛒 Μη διαθέσιμο
                                    </button>
                                """, unsafe_allow_html=True)
                            else:
                                if st.button("Προσθήκη στο καλάθι", key=add_key):
                                    response = call_api("/cart/items", method="post", data={
                                        "product_id": product["id"],
                                        "quantity": 1
                                    })
                                    if response and response.status_code in [200, 201]:
                                        st.toast("✅ Το προϊόν προστέθηκε στο καλάθι!")
                                    else:
                                        st.toast("⚠️ Προέκυψε σφάλμα κατά την προσθήκη.")

                        # ------------------ Λεπτομέρειες Προϊόντος ------------------
                        detail_key = f"product_details_{product['id']}"
                        details_expanded_key = f"details_expanded_{product['id']}"

                        # Αν δεν υπάρχει ήδη, αρχικοποιούμε
                        if detail_key not in st.session_state:
                            st.session_state[detail_key] = None

                        # Expander που ενεργοποιείται μόνο όταν το ανοίξει ο χρήστης
                        with st.expander("ℹ️ Λεπτομέρειες", expanded=False):
                            # Αν δεν έχουν φορτωθεί ακόμα τα δεδομένα, τα καλούμε
                            if st.session_state[detail_key] is None:
                                st.session_state[detail_key] = get_product_details(product['id'])

                            detail = st.session_state[detail_key]
                            description = safe(detail.get("description"))
                            if description and description != "-":
                                st.markdown(
                                    "<p style='margin-top: 0.5rem; margin-bottom: 0.2rem;'><strong>Περιγραφή:</strong></p>"
                                    f"<p style='margin: 0.2rem 0 0.8rem 1rem;'>{description}</p>",
                                    unsafe_allow_html=True
                                )

                            # Διατροφικά στοιχεία
                            nutrition_raw = safe(detail.get("nutrition"))
                            if nutrition_raw and nutrition_raw.strip() != "-":
                                nutrition_lines = nutrition_raw.split("\n")
                                cleaned = [
                                    line.strip() for line in nutrition_lines
                                    if line.strip() and not line.strip().lower().startswith(("διατροφικά", "ανά"))
                                ]
                                if cleaned:
                                    st.markdown("🍎**Διατροφικά Στοιχεία ανά 100g:**", unsafe_allow_html=True)
                                    for line in cleaned:
                                        st.markdown(f"<p style='margin: 0.2rem 0 0.2rem 1rem;'>• {line}</p>", unsafe_allow_html=True)
                                else:
                                    st.markdown("🍎**Διατροφικά Στοιχεία ανά 100g:** -", unsafe_allow_html=True)
                            else:
                                st.markdown("🍎**Διατροφικά Στοιχεία ανά 100g:** -", unsafe_allow_html=True)

                            # --------------- Scraping Τιμών ----------------
                            scrape_key = f"scrape_result_{product['id']}"
                            if scrape_key not in st.session_state:
                                st.session_state[scrape_key] = None

                            if st.button("📥 Τιμές από e-Fresh & Market IN", key=f"scrape_btn_{product['id']}"):
                                scrape_res = call_api(f"/products/{product['id']}/scrape", method="get")
                                if scrape_res and scrape_res.status_code == 200:
                                    st.session_state[scrape_key] = scrape_res.json()
                                else:
                                    st.warning("⚠️ Δεν βρέθηκαν τιμές scraping.")

                            if st.session_state[scrape_key]:
                                prices = st.session_state[scrape_key]
                                st.markdown(f"e-Fresh: {safe(prices.get('price_efresh'))} € – [Link]({safe(prices.get('efresh_url'))})")
                                st.markdown(f"Market IN: {safe(prices.get('price_marketin'))} € – [Link]({safe(prices.get('marketin_url'))})")

# Κλήση της κύριας συνάρτησης εμφάνισης προϊόντων
show_products()