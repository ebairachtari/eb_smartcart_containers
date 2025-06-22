import streamlit as st
import os
import base64

# Αυτή η συνάρτηση εμφανίζει το λογότυπο στο κέντρο της σελίδας
def show_logo_centered(small=False):
    current_dir = os.path.dirname(__file__)
    logo_path = os.path.join(current_dir, "..", "assets", "logo.png")

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode()

        width = 120 if small else 500

        st.markdown(
            f"<div style='text-align:center; margin-bottom:1.5rem;'>"
            f"<img src='data:image/png;base64,{base64_image}' width='{width}'>"
            f"</div>",
            unsafe_allow_html=True
        )

# Αυτή η συνάρτηση εισάγει το λογότυπο στο sidebar
def inject_sidebar_logo():
    current_dir = os.path.dirname(__file__)
    logo_path = os.path.join(current_dir, "..", "assets", "logo.png")

    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode()

        st.markdown(
            f"""
            <style>
            [data-testid="stSidebar"]::before {{
                content: "";
                display: block;
                background-image: url("data:image/png;base64,{base64_image}");
                background-size: 130px auto;
                background-repeat: no-repeat;
                background-position: center 10px;
                height: 140px;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
