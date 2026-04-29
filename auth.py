"""Prosta ochrona hasłem dla aplikacji Streamlit."""
import streamlit as st

ABACUS_NAVY = "#1B2A4A"
ABACUS_GOLD = "#E8A000"


def _login_styles() -> None:
    st.markdown(
        f"""
        <style>
        .abacus-login-header {{
            color: {ABACUS_NAVY};
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 0.25rem;
        }}
        .abacus-login-sub {{
            color: {ABACUS_NAVY};
            opacity: 0.75;
            margin-bottom: 1.5rem;
        }}
        .abacus-accent {{
            height: 4px;
            width: 64px;
            background: {ABACUS_GOLD};
            border-radius: 2px;
            margin-bottom: 1rem;
        }}
        div.stButton > button[kind="primary"] {{
            background-color: {ABACUS_NAVY};
            border-color: {ABACUS_NAVY};
            color: white;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: {ABACUS_GOLD};
            border-color: {ABACUS_GOLD};
            color: {ABACUS_NAVY};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_login() -> None:
    _login_styles()
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="abacus-accent"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="abacus-login-header">Generator Masowych Pism</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="abacus-login-sub">Abacus Centrum Księgowe — panel wewnętrzny</div>',
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            password = st.text_input("Hasło dostępu", type="password")
            submitted = st.form_submit_button("Zaloguj", type="primary")
        if submitted:
            if password == st.secrets.get("APP_PASSWORD"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło.")


def check_password() -> None:
    """Blokuje aplikację dopóki użytkownik się nie zaloguje."""
    if st.session_state.get("authenticated"):
        return
    _render_login()
    st.stop()


def logout_button() -> None:
    if st.sidebar.button("Wyloguj", key=f"logout_{__name__}_{id(logout_button)}"):
        st.session_state["authenticated"] = False
        st.rerun()"""Prosta ochrona hasłem dla aplikacji Streamlit."""
import streamlit as st

ABACUS_NAVY = "#1B2A4A"
ABACUS_GOLD = "#E8A000"


def _login_styles() -> None:
    st.markdown(
        f"""
        <style>
        .abacus-login-header {{
            color: {ABACUS_NAVY};
            font-weight: 700;
            font-size: 2rem;
            margin-bottom: 0.25rem;
        }}
        .abacus-login-sub {{
            color: {ABACUS_NAVY};
            opacity: 0.75;
            margin-bottom: 1.5rem;
        }}
        .abacus-accent {{
            height: 4px;
            width: 64px;
            background: {ABACUS_GOLD};
            border-radius: 2px;
            margin-bottom: 1rem;
        }}
        div.stButton > button[kind="primary"] {{
            background-color: {ABACUS_NAVY};
            border-color: {ABACUS_NAVY};
            color: white;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: {ABACUS_GOLD};
            border-color: {ABACUS_GOLD};
            color: {ABACUS_NAVY};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_login() -> None:
    _login_styles()
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.markdown('<div class="abacus-accent"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="abacus-login-header">Generator Masowych Pism</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="abacus-login-sub">Abacus Centrum Księgowe — panel wewnętrzny</div>',
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            password = st.text_input("Hasło dostępu", type="password")
            submitted = st.form_submit_button("Zaloguj", type="primary")
        if submitted:
            if password == st.secrets.get("APP_PASSWORD"):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło.")


def check_password() -> None:
    """Blokuje aplikację dopóki użytkownik się nie zaloguje."""
    if st.session_state.get("authenticated"):
        return
    _render_login()
    st.stop()


def logout_button() -> None:
    if st.sidebar.button("Wyloguj", key="logout_btn_unique"):
        st.session_state["authenticated"] = False
        st.rerun()
