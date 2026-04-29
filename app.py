"""Generator Masowych Pism — Abacus Centrum Księgowe."""
import streamlit as st

from auth import ABACUS_GOLD, ABACUS_NAVY, check_password, logout_button
from db import init_schema

st.set_page_config(
    page_title="Generator Pism | Abacus",
    layout="wide",
    initial_sidebar_state="expanded",
)

check_password()

st.markdown(
    f"""
    <style>
    h1, h2, h3 {{ color: {ABACUS_NAVY}; font-weight: 700; }}
    .abacus-hero {{
        background: linear-gradient(135deg, {ABACUS_NAVY} 0%, #2a3d63 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }}
    .abacus-hero h1 {{ color: white; margin: 0 0 0.5rem 0; }}
    .abacus-hero .accent {{
        height: 4px; width: 72px; background: {ABACUS_GOLD};
        border-radius: 2px; margin-bottom: 1rem;
    }}
    .abacus-tile {{
        border: 1px solid #e1e4ec; border-left: 4px solid {ABACUS_NAVY};
        padding: 1rem 1.25rem; border-radius: 8px; height: 100%;
        background: white;
    }}
    .abacus-tile h4 {{ color: {ABACUS_NAVY}; margin: 0 0 0.5rem 0; }}
    .abacus-tile p {{ color: #555; margin: 0; font-size: 0.9rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    init_schema()
except Exception as exc:  # noqa: BLE001
    st.warning(
        f"Nie udało się zainicjalizować schematu bazy: {exc}. "
        "Uzupełnij dane w `.streamlit/secrets.toml`."
    )

st.markdown(
    """
    <div class="abacus-hero">
        <div class="accent"></div>
        <h1>Generator Masowych Pism</h1>
        <div>Abacus Centrum Księgowe — narzędzie do tworzenia i wysyłki pism do klientów biura.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Moduły")

tiles = [
    ("Baza klientów", "Lista klientów, import z Excela, edycja danych i pól dodatkowych."),
    ("Szablony", "Zarządzanie szablonami DOCX, mapowanie zmiennych."),
    ("Wyślij", "Generowanie pism dla wybranych klientów i wysyłka mailem."),
    ("Logi", "Historia wygenerowanych i wysłanych pism."),
    ("Ustawienia", "Konfiguracja pól dodatkowych i parametrów aplikacji."),
]

cols = st.columns(len(tiles))
for col, (title, desc) in zip(cols, tiles):
    with col:
        st.markdown(
            f'<div class="abacus-tile"><h4>{title}</h4><p>{desc}</p></div>',
            unsafe_allow_html=True,
        )

st.markdown("")
st.caption("Wybierz moduł z menu po lewej, aby rozpocząć pracę.")
