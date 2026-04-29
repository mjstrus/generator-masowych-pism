"""Połączenie z Supabase (PostgreSQL) i inicjalizacja schematu."""
from urllib.parse import urlparse

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


SCHEMA_DDL = [
    """
    CREATE TABLE IF NOT EXISTS clients (
        id SERIAL PRIMARY KEY,
        nazwa_firmy TEXT NOT NULL,
        nip TEXT UNIQUE NOT NULL,
        adres TEXT,
        email TEXT,
        telefon TEXT,
        rodzaj_ksiegowosci TEXT CHECK (rodzaj_ksiegowosci IN ('KH','KPiR','Ryczalt')),
        platnik_vat BOOLEAN DEFAULT FALSE,
        ma_pracownikow BOOLEAN DEFAULT FALSE,
        rodzaj_umowy TEXT CHECK (rodzaj_umowy IN ('UoP','UZ','UoD')),
        aktywny BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS extra_fields (
        id SERIAL PRIMARY KEY,
        field_key TEXT UNIQUE NOT NULL,
        field_label TEXT NOT NULL,
        field_type TEXT NOT NULL CHECK (field_type IN ('text','number','boolean'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS client_extra_values (
        client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
        field_key TEXT REFERENCES extra_fields(field_key) ON DELETE CASCADE,
        value TEXT,
        PRIMARY KEY (client_id, field_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS templates (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        storage_path TEXT NOT NULL,
        variables JSONB,
        mapping JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS send_log (
        id SERIAL PRIMARY KEY,
        template_id INTEGER REFERENCES templates(id),
        client_id INTEGER REFERENCES clients(id),
        email_to TEXT NOT NULL,
        subject TEXT,
        sent_at TIMESTAMPTZ DEFAULT NOW(),
        status TEXT CHECK (status IN ('sent','error','dry_run')),
        error_msg TEXT
    )
    """,
]


def _build_connection_string() -> str:
    """Buduje connection string PostgreSQL z konfiguracji Supabase.

    Hasło to service_role_key; host wyciągany jest z URL Supabase
    (https://<ref>.supabase.co -> db.<ref>.supabase.co).
    """
    cfg = st.secrets["supabase"]
    parsed = urlparse(cfg["url"])
    project_ref = parsed.hostname.split(".")[0] if parsed.hostname else ""
    db_host = f"db.{project_ref}.supabase.co"
    password = cfg.get("service_role_key") or cfg.get("key")
    return f"postgresql+psycopg2://postgres:{password}@{db_host}:5432/postgres"


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    return create_engine(_build_connection_string(), pool_pre_ping=True)


def init_schema() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for ddl in SCHEMA_DDL:
            conn.execute(text(ddl))
