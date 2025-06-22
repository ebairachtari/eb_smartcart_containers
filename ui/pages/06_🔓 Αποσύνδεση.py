import streamlit as st
from utils.api_helpers import call_api
from utils.logo_helper import inject_sidebar_logo

# --------------------- Sidebar ---------------------
inject_sidebar_logo()

# Αν ο χρήστης είναι συνδεδεμένος, διαγραφή token και redirect
if "token" in st.session_state:
    del st.session_state["token"]

# Καθαρισμός και άλλων session variables
for key in list(st.session_state.keys()):
    if key not in ["page"]:
        del st.session_state[key]

# Ενημέρωση και redirect
st.success("🔓 Αποσυνδεθήκατε με επιτυχία.")
st.switch_page("Σύνδεση.py")
