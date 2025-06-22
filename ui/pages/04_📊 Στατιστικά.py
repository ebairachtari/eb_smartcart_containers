import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.api_helpers import call_api
from utils.session_helpers import require_login
from datetime import datetime, timedelta
from utils.logo_helper import inject_sidebar_logo	

# --------------------- Έλεγχος login ---------------------
require_login()

# --------------------- Ρυθμίσεις ---------------------
st.set_page_config(page_title="Στατιστικά", page_icon="📊", layout="wide")

# --------------------- Sidebar ---------------------
inject_sidebar_logo()

# --------------------- Τίτλος και περιγραφή ---------------------
st.markdown("""
    <div style='text-align: center; margin-top: 2rem;'>
        <h1 style='font-size: 2.5rem;'>Τα στατιστικά σου</h1>
    </div>
""", unsafe_allow_html=True)

# --------------------- Card helper ---------------------
def card(title_icon, content_html):
    st.markdown(
        f"""
        <div style="background-color:#f8f9fc; padding:1.2rem; border-radius:12px;
                    margin-bottom:1.5rem; box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <h4 style="margin-top:0;">{title_icon}</h4>
            <div style="font-size: 1.05rem; line-height: 1.6;">
                {content_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --------------------- Κεντρική Συνάρτηση ---------------------
def show_dashboard():
    # ---------- Welcome block για νέο χρήστη ----------
    with st.spinner("🔎 Έλεγχος δραστηριότητας..."):
        res = call_api("/analytics/purchase-frequency", method="get")

    if res and res.status_code == 200:
        data = res.json().get("data", {})
        total_orders = data.get("total_orders", 0)

        if total_orders < 2:
            st.markdown("""
            <div style="background-color: #fef9c3; padding: 1.2rem; border-left: 5px solid #facc15;
                        border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 1px 6px rgba(0,0,0,0.05);">
                <h4>👋 Καλώς ήρθες στα Στατιστικά!</h4>
                <p style="font-size: 1.05rem; color: #555;">
                    Δεν έχεις ακόμα ιστορικό παραγγελιών, γι' αυτό και δεν υπάρχουν δεδομένα για ανάλυση.
                    Ξεκίνα τις αγορές σου και μόλις ξεπεράσεις τις 2 παραγγελίες εδώ θα δεις <strong>έξυπνα γραφήματα</strong>,
                    <strong>προσωπικά στατιστικά</strong> και <strong>προτάσεις βασισμένες στις συνήθειές σου</strong>.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.stop()  # Σταματάω όλη την υπόλοιπη εκτέλεση της σελίδας αν είναι νέος χρήστης

    # ---------- Παραγγελίες & Δαπάνες ----------
    with st.spinner("📦 Ανάκτηση στατιστικών παραγγελιών..."):
        res_orders = call_api("/analytics/orders-per-month", method="get")
        res_spending = call_api("/analytics/monthly-spending", method="get")

    if res_orders and res_spending and res_orders.status_code == 200 and res_spending.status_code == 200:
        df_orders = pd.DataFrame(res_orders.json().get("data", []))
        df_spending = pd.DataFrame(res_spending.json().get("data", []))

        df_orders["month_dt"] = pd.to_datetime(df_orders["month"], format="%b %Y")
        df_spending["month_dt"] = pd.to_datetime(df_spending["month"], format="%b %Y")

        six_months_ago = pd.Timestamp(datetime.today() - timedelta(days=180))
        df_orders = df_orders[df_orders["month_dt"] >= six_months_ago]
        df_spending = df_spending[df_spending["month_dt"] >= six_months_ago]

        df = pd.merge(df_orders, df_spending, on="month_dt", how="outer").sort_values("month_dt")
        df["month_str"] = df["month_dt"].dt.strftime("%b %Y")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["month_str"], y=df["orders"], name="📦 Παραγγελίες",
                                 mode="lines+markers", yaxis="y1", line=dict(color="royalblue", width=3),
                                 marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=df["month_str"], y=df["spending"], name="💶 Δαπάνη",
                                 mode="lines+markers", yaxis="y2", line=dict(color="seagreen", width=2),
                                 marker=dict(size=8)))

        fig.update_layout(
            xaxis=dict(title="Μήνας", tickangle=-45, tickfont=dict(size=12), automargin=True),
            #yaxis=dict(title="Αριθμός Παραγγελιών", tickformat=".0f"),
            yaxis=dict(title="Αριθμός Παραγγελιών", tickformat=".0f", dtick=1, range=[min(df["orders"]) - 0.5, max(df["orders"]) + 0.5] ),
            yaxis2=dict(title="Δαπάνη (€)", overlaying="y", side="right", tickformat=".0f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
            margin=dict(t=60, l=60, r=60, b=60),
            plot_bgcolor="white",
            hovermode="x unified"
        )

        st.markdown("""
            <div style='background-color:#f8f9fc; padding:1.2rem; border-radius:12px;
                        margin-bottom:0.2rem; box-shadow:0 1px 4px rgba(0,0,0,0.05);'>
                <h4 style='margin: 0;'>📊 Παραγγελίες & Δαπάνες ανά Μήνα</h4>
                <div style='font-size: 1.05rem; line-height: 1.6; margin-top: 0.5rem;'>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Σφάλμα κατά την ανάκτηση δεδομένων.")

    # ---------- Συχνότητα αγορών ----------
    with st.spinner("📈 Ανάκτηση συχνότητας αγορών..."):
        res_freq = call_api("/analytics/purchase-frequency", method="get")
    if res_freq and res_freq.status_code == 200:
        data = res_freq.json().get("data", {})
        avg = data.get("average_days")
        total = data.get("total_orders", 0)

        if avg is None or total == 0:
            card("📈 Συχνότητα Αγορών", "ℹ️ Δεν υπάρχουν επαρκή δεδομένα για συχνότητα.")
        else:
            html = (
                f"<div style='line-height: 1.6; font-size: 1.05rem;'>"
                f"📅 Κατά μέσο όρο παραγγέλνεις κάθε <strong>{avg} μέρες</strong>.<br>"
                f"🛒 Έχεις συνολικά <strong>{total} ολοκληρωμένες παραγγελίες</strong> στο ιστορικό σου."
                "</div>"
            )
            card("📈 Συχνότητα Αγορών", html)
    else:
        st.warning("⚠️ Σφάλμα κατά την ανάκτηση δεδομένων.")

    # ---------- Αγαπημένα προϊόντα ----------
    with st.spinner("🛍️ Ανάκτηση αγαπημένων προϊόντων..."):
        res = call_api("/analytics/favorites", method="get")

    if res and res.status_code == 200:
        favorites = res.json().get("favorites", [])
        if not favorites:
            card("🛍️ Τα Προϊόντα που προτιμάς", "ℹ️ Δεν υπάρχουν αγαπημένα προϊόντα.")
        else:
            rows = ""
            for product in favorites:
                name = product.get("name", "Άγνωστο")
                image_url = product.get("image_url", "")
                times_bought = product.get("times_bought", 0)

                rows += f"""
    <div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
        <img src="{image_url}" alt="{name}" style="width: 45px; height: 45px; object-fit: cover;
            border-radius: 6px; margin-right: 1rem;">
        <div>
            <strong>{name}</strong><br>
            📦 <span style="color: #555;">{times_bought} φορές</span>
        </div>
    </div>
    """

            html_block = f"<div style='line-height: 1.6; font-size: 1.05rem;'>{rows}</div>"
            card("🛍️ Τα Προϊόντα που προτιμάς", html_block)
    else:
        st.error("⚠️ Σφάλμα κατά την ανάκτηση δεδομένων.")

# --------------------- Εκκίνηση ---------------------
show_dashboard()
