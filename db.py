"""Klient Supabase i (opcjonalna) inicjalizacja schematu.

Schemat tworzymy ręcznie w Supabase Dashboard (SQL Editor) — `SCHEMA_SQL`
zawiera gotowy skrypt do skopiowania. `init_schema()` pozostaje jako no-op
żeby nie psuć importu w `app.py`; jeśli w projekcie utworzysz funkcję RPC
`exec_sql(query text)` to ta funkcja użyje jej do automatycznego setupu.
"""
from __future__ import annotations

import streamlit as st
from supabase import Client, create_client


SCHEMA_SQL = """
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
);

CREATE TABLE IF NOT EXISTS extra_fields (
    id SERIAL PRIMARY KEY,
    field_key TEXT UNIQUE NOT NULL,
    field_label TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK (field_type IN ('text','number','boolean'))
);

CREATE TABLE IF NOT EXISTS client_extra_values (
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    field_key TEXT REFERENCES extra_fields(field_key) ON DELETE CASCADE,
    value TEXT,
    PRIMARY KEY (client_id, field_key)
);

CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    storage_path TEXT NOT NULL,
    variables JSONB,
    mapping JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS send_log (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES templates(id),
    client_id INTEGER REFERENCES clients(id),
    email_to TEXT NOT NULL,
    subject TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT CHECK (status IN ('sent','error','dry_run')),
    error_msg TEXT
);
"""


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    cfg = st.secrets["supabase"]
    return create_client(cfg["url"], cfg["service_role_key"])


def init_schema() -> None:
    """Tworzy schemat przez RPC `exec_sql`, jeśli istnieje. W przeciwnym razie no-op.

    W Supabase nie ma natywnego DDL przez REST — tabele najwygodniej utworzyć
    ręcznie w Dashboard → SQL Editor (skopiuj `SCHEMA_SQL`). Jeśli założysz
    własną funkcję `create or replace function exec_sql(query text) returns void
    language plpgsql as $$ begin execute query; end; $$;` to ta funkcja ją wywoła.
    """
    client = get_client()
    try:
        client.rpc("exec_sql", {"query": SCHEMA_SQL}).execute()
    except Exception:
        # Brak RPC `exec_sql` — schemat trzeba utworzyć ręcznie w Dashboard.
        return
