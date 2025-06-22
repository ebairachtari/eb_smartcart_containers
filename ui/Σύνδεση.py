import streamlit as st
import base64
import os
from utils.api_helpers import call_api  # helper για API
from utils.logo_helper import show_logo_centered  # helper για το logo

# ---- Εμφάνιση ----
st.set_page_config(
    page_title="Σύνδεση / Εγγραφή",
    page_icon="🔐", 
    layout="centered",
    initial_sidebar_state="collapsed")

# Έλεγχος αν η συνεδρία έχει λήξει
if st.session_state.get("expired_session"):
    st.warning("⏳ Η συνεδρία σου έληξε. Παρακαλώ συνδέσου ξανά.")
    del st.session_state["expired_session"]

# Έλεγχος αν ο χρήστης έχει κάνει login
if "token" in st.session_state and st.session_state["token"]:
    st.switch_page("pages/01_🏠 Αρχική.py")

# Αρχικό logo
show_logo_centered()

def login_form():
    st.subheader("🔐 Σύνδεση")
    with st.form("login_form"):
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Κωδικός", type="password")
        submit = st.form_submit_button("Σύνδεση")

        if submit:
            try:
                # Χρήση της call_api για login
                res = call_api("/auth/login", method="post", data={"email": email, "password": password}, allow_unauthorized=True)
                if res.status_code == 200:
                    data = res.json()
                    token = data.get("access_token")
                    st.session_state["token"] = token
                    st.session_state["user_id"] = data["user_id"]

                    # Μετάβαση σε σελίδα Home μετά το login
                    st.switch_page("pages/01_🏠 Αρχική.py")

                else:
                    st.error("❌ Λάθος email ή κωδικός.")
            except Exception as e:
                st.error(f"⚠️ Σφάλμα: {e}")

def register_form():
    st.subheader("📝 Δημιουργία Λογαριασμού")
    with st.form("register_form"):
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Κωδικός", type="password")
        confirm_password = st.text_input("🔒 Επανάληψη Κωδικού", type="password")
        submit = st.form_submit_button("Εγγραφή")

        if submit:
            if password != confirm_password:
                st.error("❌ Οι κωδικοί δεν ταιριάζουν.")
            else:
                try:
                    # Χρήση της call_api για register
                    res = call_api("/auth/register", method="post", data={"email": email, "password": password})
                    if res.status_code == 201:
                        st.success("✅ Εγγραφή επιτυχής! Μπορείς τώρα να συνδεθείς.")
                    elif res.status_code == 409:
                        st.warning("⚠️ Υπάρχει ήδη λογαριασμός με αυτό το email.")
                    else:
                        st.error("⚠️ Σφάλμα κατά την εγγραφή.")
                except Exception as e:
                    st.error(f"⚠️ Σφάλμα: {e}")

# Tabs για login/register
tabs = st.tabs(["🔐 Σύνδεση", "📝 Εγγραφή"])
with tabs[0]:
    login_form()
with tabs[1]:
    register_form()