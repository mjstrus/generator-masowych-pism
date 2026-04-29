import streamlit as st

from auth import ABACUS_NAVY, check_password, logout_button

st.set_page_config(page_title="Wyślij | Abacus", layout="wide")
check_password()

st.markdown(
    f"<h1 style='color:{ABACUS_NAVY};font-weight:700'>Wyślij</h1>",
    unsafe_allow_html=True,
)
st.info("Moduł w budowie")
logout_button()
