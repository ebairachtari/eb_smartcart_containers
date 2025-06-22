import requests
import streamlit as st


# Αυτή η συνάρτηση βοηθά στο να καλούμε όλα τα API με token, εύκολα και επαναχρησιμοποιήσιμα

def call_api(endpoint, method="get", params=None, data=None, json=None, headers=None, allow_unauthorized=False):
    API_URL = "http://smartcart_backend:5000"
    url = f"{API_URL}{endpoint}"

    # Αν δεν έχουν δοθεί headers, δημιουργώ ένα κενό dictionary
    if headers is None:
        headers = {}

    # Αν υπάρχει token στο session, το προσθέτω στα headers
    if "Authorization" not in headers and "token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['token']}"

    try:
        # Ανάλογα με τη μέθοδο, εκτελώ και αποθηκεύω το αποτέλεσμα στη μεταβλητή res
        if method == "get":
            res = requests.get(url, params=params, headers=headers)
        elif method == "post":
            res = requests.post(url, json=json or data, headers=headers)
        elif method == "patch":
            res = requests.patch(url, json=json or data, headers=headers)
        elif method == "delete":
            res = requests.delete(url, headers=headers)
        else:
            return None

        # Τώρα μπορώ να ελέγξω το status code
        if res.status_code == 401 and not allow_unauthorized:
            st.session_state["expired_session"] = True
            st.session_state["token"] = "" # Καθαρίζω το token
            st.switch_page("Σύνδεση.py")  # Μεταβαίνω στη σελίδα σύνδεσης
            st.stop()

        return res 

    except Exception as e:
        print(f"❌ call_api error: {e}")
        return None
