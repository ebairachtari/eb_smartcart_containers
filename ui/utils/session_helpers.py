import streamlit as st

# Έλεγχος αν ο χρήστης είναι συνδεδεμένος
def require_login():
    """Ελέγχει αν ο χρήστης είναι συνδεδεμένος. Αν όχι, μεταφέρει στη σελίδα Σύνδεσης."""
    if "token" not in st.session_state or not st.session_state["token"]:
        st.warning("🚫 Πρέπει να συνδεθείς πρώτα.")
        st.switch_page("Σύνδεση.py")